"""Pure synthetic guards; no source media or participant orientations accessed."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from .media import encode_command,timeline,packet_signature
from .metrics import mse_map,aggregate_native,past_only
from .spec import plan,digest,ROOT
from .prepare import authorize


def probe_fixture(seconds=10):
    return {'streams':[{'codec_name':'h264','width':1920,'height':960,'r_frame_rate':'30/1',
        'time_base':'1/30','start_time':'0'}],'format':{'duration':str(seconds)},
        'packets':[{'pts':i,'dts':i-2,'duration':1,'size':100,'data_hash':'SHA256:'+'a'*64,
            'flags':'K_' if i%60==0 else '__'} for i in range(seconds*30)]}


class CommandTests(unittest.TestCase):
    def test_exact_rates(self):
        for rung,rate in enumerate((45,88,253,369,987,3792)):
            command=encode_command(Path('input.mp4'),Path('output.mp4'),rung)
            self.assertEqual(command[command.index('-b:v')+1],f'{rate}k')
            self.assertEqual(command[command.index('-maxrate')+1],f'{rate*2}k')
            self.assertEqual(command[command.index('-bufsize')+1],f'{rate*4}k')
    def test_no_overwrite(self):
        command=encode_command('input','output',0); self.assertIn('-n',command); self.assertNotIn('-y',command)
    def test_no_cpu_fallback(self): self.assertIn('h264_nvenc',encode_command('input','output',0))
    def test_no_original_retiming(self):
        command=encode_command('input','output',0)
        self.assertNotIn('-ss',command); self.assertFalse(any('setpts' in s for s in command))
    def test_filter_and_gop(self):
        command=encode_command('input','output',0)
        self.assertEqual(command[command.index('-vf')+1],'scale=1920:960:flags=lanczos,fps=30')
        self.assertEqual(command[command.index('-g')+1],'60')
    def test_invalid_rung(self):
        for rung in (-1,6,True):
            with self.assertRaises(ValueError): encode_command('i','o',rung)


class TimelineTests(unittest.TestCase):
    def test_contiguous(self): self.assertEqual(len(timeline(probe_fixture(),10)),300)
    def test_decode_order_not_presentation_order(self):
        p=probe_fixture(); p['packets'].reverse(); self.assertEqual(timeline(p,10)[0]['pts'],0)
    def test_nonzero_packet_origin(self):
        p=probe_fixture()
        for row in p['packets']: row['pts']+=1
        with self.assertRaises(ValueError): timeline(p,10)
    def test_nonzero_stream_origin(self):
        p=probe_fixture(); p['streams'][0]['start_time']='0.066667'
        with self.assertRaises(ValueError): timeline(p,10)
    def test_missing_frame(self):
        p=probe_fixture(); p['packets'].pop()
        with self.assertRaises(ValueError): timeline(p,10)
    def test_duplicate_pts(self):
        p=probe_fixture(); p['packets'][2]['pts']=1
        with self.assertRaises(ValueError): timeline(p,10)
    def test_duration(self):
        p=probe_fixture(); p['packets'][2]['duration']=2
        with self.assertRaises(ValueError): timeline(p,10)
    def test_keyframe(self):
        p=probe_fixture(); p['packets'][60]['flags']='__'
        with self.assertRaises(ValueError): timeline(p,10)
    def test_container_tail(self):
        p=probe_fixture(); p['format']['duration']='10.066667'
        with self.assertRaises(ValueError): timeline(p,10)
    def test_codec(self):
        p=probe_fixture(); p['streams'][0]['codec_name']='hevc'
        with self.assertRaises(ValueError): timeline(p,10)
    def test_signature_binds_size(self):
        a=probe_fixture()['packets']; b=copy.deepcopy(a); b[0]['size']+=1
        self.assertNotEqual(packet_signature(a),packet_signature(b))
    def test_signature_binds_payload(self):
        a=probe_fixture()['packets']; b=copy.deepcopy(a); b[0]['data_hash']='other'
        self.assertNotEqual(packet_signature(a),packet_signature(b))


class MetricTests(unittest.TestCase):
    def fixture(self): return np.ones((6,60,6,12),dtype=np.float32),np.tile([90.,0],(60,1))
    def test_pixel_native_mse(self):
        a=np.zeros((1,480,960),dtype=np.float32); b=np.full_like(a,10)
        np.testing.assert_array_equal(mse_map(a,b,1),np.full((1,6,12),100))
    def test_no_min_length_truncation(self):
        a=np.zeros((2,480,960),dtype=np.float32)
        with self.assertRaises(ValueError): mse_map(a,a[:1],2)
    def test_integer_pixels_not_silently_wrapped(self):
        a=np.zeros((1,480,960),dtype=np.uint8)
        with self.assertRaises(ValueError): mse_map(a,a,1)
    def test_invalid_pixels(self):
        a=np.full((1,480,960),256,dtype=np.float32)
        with self.assertRaises(ValueError): mse_map(a,a,1)
    def test_parent_native_micro(self):
        maps,poses=self.fixture(); result=aggregate_native(maps,poses)
        np.testing.assert_array_equal(result['negative_micro_mse'],np.full((6,6),-1000000))
        self.assertEqual(result['duration_ticks'],[1500000]*6)
    def test_secondary_child_duration(self):
        result=aggregate_native(*self.fixture(),2)
        self.assertEqual(np.shape(result['native_mse']),(6,30)); self.assertEqual(result['duration_ticks'],[300000]*30)
    def test_no_rung_isotonic_repair(self):
        maps,poses=self.fixture(); maps[5]=2
        result=aggregate_native(maps,poses)['negative_micro_mse']
        self.assertLess(result[5][0],result[2][0])
    def test_nan_map(self):
        maps,poses=self.fixture(); maps[0,0,0,0]=np.nan
        with self.assertRaises(ValueError): aggregate_native(maps,poses)
    def test_bad_pose(self):
        maps,poses=self.fixture(); poses[0,1]=91
        with self.assertRaises(ValueError): aggregate_native(maps,poses)
    def test_bad_map_shape(self):
        maps,poses=self.fixture()
        with self.assertRaises(ValueError): aggregate_native(maps[:5],poses)
    def test_past_view(self):
        record=aggregate_native(*self.fixture()); view=past_only(record,2)
        self.assertEqual(np.shape(view['negative_micro_mse']),(6,2)); self.assertFalse(view['future_labels_included'])
    def test_empty_history(self):
        view=past_only(aggregate_native(*self.fixture()),0)
        self.assertEqual(view['negative_micro_mse'],[[]]*6)
    def test_bad_decision_boundary(self):
        with self.assertRaises(ValueError): past_only({},7)


class PlanAndGateTests(unittest.TestCase):
    def test_roster_counts(self):
        value=plan(); self.assertEqual(len(value['clips']),16)
        self.assertEqual(sum(c['eligible'] for c in value['clips']),10)
        self.assertEqual(sum(len(c['pairs']) for c in value['clips']),452)
    def test_contract_unchanged(self):
        c=plan()['contract']; self.assertEqual((c['target_fraction'],c['deadline_seconds'],c['parents'],c['pair_cap_bytes']),([1,2],40,4,1500000))
    def test_source_origins_not_repaired(self):
        value=plan(); bad={c['clip']:c for c in value['clips'] if c['clip'] in ('e2v02','e2v09')}
        self.assertTrue(all(not c['eligible'] for c in bad.values()))
    def test_gate_before_runtime_or_sources(self):
        with patch('wu_pipeline.prepare.verify',return_value={'plan':{}}),patch('wu_pipeline.prepare.fingerprint') as fp:
            with self.assertRaises(ValueError): authorize(Path('input'),Path('output'),'not-the-digest')
            fp.assert_not_called()
    def test_software_directory_output_refused(self):
        frozen={'plan':{}}
        with patch('wu_pipeline.prepare.verify',return_value=frozen),patch('wu_pipeline.prepare.fingerprint') as fp:
            with self.assertRaises(ValueError): authorize(Path('input'),ROOT/'new-private-output',digest(frozen))
            fp.assert_not_called()
    def test_existing_directory_refused(self):
        frozen={'plan':{}}
        with tempfile.TemporaryDirectory() as folder,patch('wu_pipeline.prepare.verify',return_value=frozen),patch('wu_pipeline.prepare.fingerprint') as fp:
            with self.assertRaises(ValueError): authorize(Path(folder)/'inputs',Path(folder),digest(frozen))
            fp.assert_not_called()
    def test_source_subdirectory_output_refused(self):
        frozen={'plan':{}}
        with patch('wu_pipeline.prepare.verify',return_value=frozen),patch('wu_pipeline.prepare.fingerprint') as fp:
            with self.assertRaises(ValueError): authorize(Path('input'),Path('input')/'new',digest(frozen))
            fp.assert_not_called()


if __name__=='__main__': unittest.main()
