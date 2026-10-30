from datetime import datetime,timedelta
import io
import unittest
from unittest.mock import Mock
import zipfile
from .core import (HEADER,MetadataError,parse_clocks,member,intake,validate_archive_directory,
    qualify_clock,media_decision,scalar_evidence,reasons_from_evidence,summarize,clips)


def fixture(times=None):
    times=times if times is not None else [i/20 for i in range(1201)]
    start=datetime(2020,1,1)
    lines=[','.join(HEADER)]
    for i,t in enumerate(times):
        stamp=(start+timedelta(milliseconds=10*i)).isoformat(sep=' ')
        lines.append(','.join([stamp,str(t)]+['opaque NOT A NUMBER']*7))
    return ('\n'.join(lines)+'\n').encode()


class ParserTests(unittest.TestCase):
    def test_opaque_poses_positions(self):
        w,t=parse_clocks(fixture()); self.assertEqual(len(w),1201)
        self.assertTrue(qualify_clock(w,t)['clock_qualified'])
    def test_calendar_not_returned(self):
        w,t=parse_clocks(fixture([0,.02])); self.assertEqual(w,[0,.01])
    def test_header(self):
        with self.assertRaisesRegex(MetadataError,'unexpected_header'): parse_clocks(b'bad\n')
    def test_nonfinite(self):
        for t in ['nan','inf','-1']:
            with self.assertRaisesRegex(MetadataError,'invalid_playback_clock'): parse_clocks(fixture([0,t]))
    def test_invalid_clock_value_sanitized(self):
        with self.assertRaisesRegex(MetadataError,'^invalid_clock_field$'): parse_clocks(fixture([0,'private secret']))
    def test_bad_wall_string(self):
        with self.assertRaisesRegex(MetadataError,'invalid_clock_field'):
            parse_clocks(fixture([0,.01]).replace(b'2020-01-01',b'private-text'))
    def test_row_shape(self):
        with self.assertRaisesRegex(MetadataError,'malformed_row'): parse_clocks((','.join(HEADER)+'\n0,0').encode())
    def test_oversized(self):
        with self.assertRaisesRegex(MetadataError,'oversized_metadata_row'): parse_clocks(b'x'*4097)
    def test_empty(self):
        with self.assertRaisesRegex(MetadataError,'insufficient_clock_rows'): parse_clocks((','.join(HEADER)+'\n').encode())
    def test_encoding(self):
        with self.assertRaisesRegex(MetadataError,'invalid_csv_encoding_or_syntax'): parse_clocks(b'\xff')


class GuardTests(unittest.TestCase):
    def test_partition(self): self.assertEqual(len(clips()),16)
    def test_calibration_refused_before_read(self):
        for clip in ('e1v02','e2v04','e3v01'):
            z=Mock()
            with self.assertRaises(ValueError): intake(z,clip,'1')
            z.read.assert_not_called(); z.getinfo.assert_not_called()
    def test_path(self): self.assertEqual(member('e2v09','48'),'Formated_Data/Experiment_2/48/video_8.csv')
    def test_identity_rejected(self):
        for x in ('0','49','../1','01'):
            with self.assertRaises(ValueError): member('e1v01',x)
    def test_missing(self):
        z=Mock(); z.getinfo.side_effect=KeyError('unimportant')
        with self.assertRaisesRegex(MetadataError,'missing_trace_member'): intake(z,'e1v01','1')
    def test_archive_paths(self):
        for names in (['a','A'],['../a'],['a\\b'],['/a']):
            z=Mock(); z.namelist.return_value=names
            with self.assertRaises(ValueError): validate_archive_directory(z)
    def test_real_zip_reader_opaque_fields(self):
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w') as z: z.writestr(member('e1v01','1'),fixture())
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as z:
            sha,(w,t)=intake(z,'e1v01','1')
        self.assertEqual(len(sha),64); self.assertTrue(qualify_clock(w,t)['clock_qualified'])


class ClockTests(unittest.TestCase):
    def check(self,t): return qualify_clock([i*.01 for i in range(len(t))],t)
    def test_regular(self): self.assertTrue(self.check([i/20 for i in range(1201)])['clock_qualified'])
    def test_duplicate_time(self): self.assertTrue(self.check([v for i in range(1201) for v in [i/20]*2])['clock_qualified'])
    def test_early_backstep_retained(self):
        t=[i/20 for i in range(1201)]; t[2]=.01
        self.assertTrue(self.check(t)['clock_qualified'])
    def test_stale_repeat_not_filtered_out(self):
        t=[i/20 for i in range(1201)]; t[12]=.4
        self.assertIn('ambiguous_target_crossing',self.check(t)['clock_reasons'])
    def test_missing_target(self): self.assertIn('stale_target_crossing',self.check([0,60])['clock_reasons'])
    def test_age_boundary(self):
        self.assertTrue(self.check([0]+[i+.6 for i in range(60)]+[60])['clock_qualified'])
    def test_initial_bracket(self): self.assertIn('missing_initial_bracket',self.check([1,60])['clock_reasons'])
    def test_coverage(self): self.assertIn('missing_60s_coverage',self.check([i/20 for i in range(1191)])['clock_reasons'])
    def test_wall_reversal(self):
        r=qualify_clock([0,-.1,1],[0,.5,60]); self.assertEqual(r['clock_reasons'],['invalid_or_backward_wall_clock'])
    def test_interval_jump_counts_all_targets(self):
        e,_=scalar_evidence([0,1],[0,60]); self.assertEqual(e['crossing_counts'],[1]*60)
    def test_long_later_repetition_not_ignored(self):
        t=[i/20 for i in range(1301)]+[0,.5,60]
        self.assertIn('ambiguous_target_crossing',self.check(t)['clock_reasons'])


class MediaTests(unittest.TestCase):
    def base(self): return {'stream':{'start_time':'0','duration':'120'},'first_pts_seconds':0,
        'last_pts_seconds':61,'maximum_target_frame_age_seconds':.04,'target_timing_pass':True,'sha256':'a'*64}
    def test_pass(self): self.assertTrue(media_decision(self.base())['qualified'])
    def test_origin_not_shifted(self):
        m=self.base(); m['stream']['start_time']='0.04'; m['first_pts_seconds']=.04; m['target_timing_pass']=False
        self.assertEqual(media_decision(m)['reasons'],['nonzero_media_origin'])
    def test_inconsistent_flag(self):
        m=self.base(); m['target_timing_pass']=False
        with self.assertRaises(ValueError): media_decision(m)
    def test_short_media(self):
        m=self.base(); m['last_pts_seconds']=59; m['target_timing_pass']=False
        self.assertIn('insufficient_media_coverage',media_decision(m)['reasons'])
    def test_no_self_pair(self):
        media={c:{'qualified':True,'reasons':[]} for c in clips()}
        rows=[{'clip':c,'source_id':'1','clock_qualified':True} for c in clips()]
        result=summarize(rows,media)
        self.assertTrue(all(not c['clip_qualified'] and not c['directed_pairs'] for c in result))
    def test_lexicographic_cycle(self):
        media={c:{'qualified':True,'reasons':[]} for c in clips()}
        rows=[{'clip':c,'source_id':i,'clock_qualified':True} for c in clips() for i in ('2','10','1')]
        self.assertEqual(summarize(rows,media)[0]['directed_pairs'],[['1','10'],['10','2'],['2','1']])


if __name__=='__main__': unittest.main()
