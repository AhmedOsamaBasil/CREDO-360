import io
import json
import math
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from .acquire import acquire, jobs, sha256
from .clocks import HEADER, TRACE, scan_clock
from .geometry import candidate_uv, forward_xyzw
from .media import evaluate_pts, probe
from .diagnose_clocks import inspect


def trace(times):
    return io.StringIO(','.join(HEADER) + '\n' + '\n'.join(
        ','.join(['opaque wall time', str(t)] + ['not a number'] * 7) for t in times))


class ClockTests(unittest.TestCase):
    def test_complete_opaque_pose(self):
        r = scan_clock(trace([i / 20 for i in range(1201)]))
        self.assertTrue(r['eligible']); self.assertEqual(r['targets_covered'], 60)

    def test_duplicate_clock_retained(self):
        r = scan_clock(trace([v for i in range(1201) for v in (i/20, i/20)]))
        self.assertTrue(r['eligible']); self.assertEqual(r['duplicates'], 1200)

    def test_backward(self):
        self.assertIn('backward_playback_time', scan_clock(trace([0, .2, .1]))['reasons'])

    def test_start_missing(self):
        self.assertIn('missing_start', scan_clock(trace([1, 60]))['reasons'])

    def test_end_missing(self):
        self.assertIn('missing_60s_coverage', scan_clock(trace([i / 20 for i in range(1191)]))['reasons'])

    def test_stale(self):
        self.assertIn('missing_or_stale_sample', scan_clock(trace(range(61)))['reasons'])

    def test_nonfinite(self):
        for t in ('nan', 'inf', '-inf', '-1', 'garbage'):
            with self.subTest(t=t):
                self.assertIn('invalid_playback_time', scan_clock(trace([0, t]))['reasons'])

    def test_header(self):
        with self.assertRaises(ValueError): scan_clock(io.StringIO('wrong\n'))

    def test_row_shape(self):
        r = scan_clock(io.StringIO(','.join(HEADER) + '\n0,0\n'))
        self.assertIn('row_shape', r['reasons'])

    def test_oversized(self):
        with self.assertRaises(ValueError): scan_clock(io.StringIO('x' * 4097))

    def test_stops_before_later_values(self):
        stream = trace([i/20 for i in range(1201)])
        stream = io.StringIO(stream.read() + '\ninvalid beyond window')
        self.assertTrue(scan_clock(stream)['eligible'])
        self.assertEqual(stream.readline(), 'invalid beyond window')

    def test_boundary_tolerance(self):
        times = [0] + [i+.6 for i in range(60)] + [60]
        self.assertTrue(scan_clock(trace(times))['eligible'])

    def test_path_mapping(self):
        self.assertEqual(TRACE.fullmatch('Formated_Data/Experiment_2/48/video_8.csv').groups(), ('2','48','8'))
        for name in ('Formated_Data/Experiment_3/1/video_0.csv', 'Formated_Data/Experiment_1/0/video_0.csv',
                     'Formated_Data/Experiment_1/49/video_0.csv', 'Formated_Data/Experiment_1/1/video_9.csv'):
            self.assertIsNone(TRACE.fullmatch(name))

    def test_independent_next_sample(self):
        from bisect import bisect_left
        times = [i/30 for i in range(1801)]
        expected = max(times[bisect_left(times, i+.5)] - i-.5 for i in range(60))
        self.assertAlmostEqual(scan_clock(trace(times))['maximum_next_age_seconds'], expected)


class GeometryTests(unittest.TestCase):
    def test_identity(self): self.assertEqual(forward_xyzw((0,0,0,1)), (0,0,1))

    def test_axes(self):
        s = math.sqrt(.5)
        for q, expected in [((0,s,0,s),(1,0,0)), ((s,0,0,s),(0,-1,0)), ((0,1,0,0),(0,0,-1))]:
            for a,b in zip(forward_xyzw(q),expected): self.assertAlmostEqual(a,b)

    def test_independent_hamilton(self):
        def mul(a,b):
            aw,ax,ay,az=a; bw,bx,by,bz=b
            return (aw*bw-ax*bx-ay*by-az*bz, aw*bx+ax*bw+ay*bz-az*by,
                    aw*by-ax*bz+ay*bw+az*bx, aw*bz+ax*by-ay*bx+az*bw)
        rng = random.Random(735)
        for _ in range(200):
            q = [rng.uniform(-1,1) for _ in range(4)]
            n = math.sqrt(sum(v*v for v in q)); q=[v/n for v in q]
            x,y,z,w=q
            expected=mul(mul((w,x,y,z),(0,0,0,1)),(w,-x,-y,-z))[1:]
            for a,b in zip(forward_xyzw(q),expected): self.assertAlmostEqual(a,b)
            self.assertEqual(forward_xyzw(q),forward_xyzw([-v for v in q]))

    def test_invalid(self):
        for q in ((0,0,0,0),(0,0,0,2),(0,0,float('nan'),1),(0,0,1)):
            with self.assertRaises(ValueError): forward_xyzw(q)

    def test_candidates_differ(self):
        self.assertEqual(candidate_uv((0,0,1),wrap_sign=1),(.25,.5))
        self.assertEqual(candidate_uv((0,0,1),wrap_sign=-1),(.75,.5))
        for sign in (-1,1):
            self.assertEqual(candidate_uv((1,0,0),wrap_sign=sign),(0,.5))

    def test_no_default(self):
        with self.assertRaises(TypeError): candidate_uv((0,0,1))
        with self.assertRaises(ValueError): candidate_uv((0,0,1),wrap_sign=True)


class ClockDiagnosisTests(unittest.TestCase):
    def test_startup_prefix(self):
        r=inspect(trace([1.2,1.2,0,0,.02,60]))
        self.assertEqual(r['prefix_rows'],2)
        self.assertEqual(r['after_zero_backward_steps'],0)
        self.assertTrue(r['does_not_change_primary_eligibility'])
    def test_postzero_backstep(self):
        r=inspect(trace([0,.02,.01,60]))
        self.assertEqual(r['after_zero_backward_steps'],1)
        self.assertAlmostEqual(r['maximum_after_zero_backstep_seconds'],.01)
    def test_no_exact_zero(self):
        r=inspect(trace([.001,.02,60]))
        self.assertFalse(r['first_exact_zero_found'])


class MediaTests(unittest.TestCase):
    def test_regular(self): self.assertTrue(evaluate_pts([i/30 for i in range(1830)])['target_timing_pass'])
    def test_negative(self):
        with self.assertRaises(ValueError): evaluate_pts([-1,0,60])
    def test_duplicate(self):
        with self.assertRaises(ValueError): evaluate_pts([0,0,60])
    def test_nan(self):
        with self.assertRaises(ValueError): evaluate_pts([0,float('nan'),60])
    def test_late_start(self): self.assertFalse(evaluate_pts([i/30 for i in range(1,1830)])['target_timing_pass'])
    def test_missing_end(self): self.assertFalse(evaluate_pts([i/30 for i in range(1800)])['target_timing_pass'])
    def test_sparse(self): self.assertFalse(evaluate_pts(list(range(61)))['target_timing_pass'])
    def test_no_initial_seek(self):
        from types import SimpleNamespace
        data={'streams':[{'width':2,'height':1,'r_frame_rate':'30/1','avg_frame_rate':'30/1',
            'time_base':'1/30','start_time':'0','duration':'61','nb_frames':'1830'}],
            'frames':[{'best_effort_timestamp_time':str(i/30)} for i in range(1830)]}
        def fake(command,**kwargs):
            self.assertEqual(command[command.index('-read_intervals')+1],'%61')
            return SimpleNamespace(stdout=json.dumps(data).encode(),stderr=b'')
        with patch('wu_source.media.subprocess.run',side_effect=fake):
            self.assertTrue(probe(Path('synthetic.mp4'))['target_timing_pass'])


class AcquireTests(unittest.TestCase):
    def test_catalogue(self):
        records=jobs(); self.assertEqual(len(records),19)
        self.assertEqual(sum(j['bytes'] for j in records),3651951337)
        self.assertIn('hp9rf9vs93in6zl',records[-1]['url'])

    def test_fake_download_reuse(self):
        body=b'\x00\x00\x00\x18ftyphello'
        class Response(io.BytesIO):
            status=200
            headers={'Content-Length':str(len(body))}
        job={'name':'x.mp4','id':'x','kind':'mp4','url':'https://example.org/file','bytes':len(body)}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            r=acquire(job,root,opener=lambda *a,**k:Response(body))
            self.assertEqual(r['sha256'],sha256(root/'x.mp4'))
            self.assertEqual(acquire(job,root,opener=lambda *a,**k:self.fail('network during reuse')),r)
            (root/'x.mp4').write_bytes(b'bad')
            with self.assertRaises(ValueError): acquire(job,root)

    def test_partial_preserved(self):
        job={'name':'x.mp4','id':'x','kind':'mp4','url':'unused','bytes':10}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.mp4.part'; p.write_bytes(b'prior')
            with self.assertRaises(ValueError): acquire(job,Path(tmp))
            self.assertEqual(p.read_bytes(),b'prior')


if __name__ == '__main__': unittest.main()
