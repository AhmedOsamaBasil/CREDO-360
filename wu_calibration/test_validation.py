import json
import unittest
from .core import PACKAGE,mapping_gate
from .replication import compare
from .check_adapter import scalar_select,scalar_yaw_pitch,scalar_weights
from .adapter import select_indices


class ValidationTests(unittest.TestCase):
    def test_primary_report(self):
        r=json.loads((PACKAGE/'results/calibration_v1/report.json').read_text())
        self.assertEqual(len(r['clock_rows']),96); self.assertEqual(len(r['geometry_cells']),20)
        self.assertEqual(mapping_gate(r['geometry_cells'])['supported_sign'],-1)
        self.assertEqual(r['confirmation_clips_accessed'],[])
    def test_adapter_artifact(self):
        r=json.loads((PACKAGE/'results/adapter_v1/report.json').read_text())
        self.assertEqual(sum(x['accepted'] for x in r['rows']),48)
        self.assertTrue(all(not x['accepted'] for x in r['rows'] if x['clip']=='e1v02'))
        self.assertEqual(r['independent_projection_samples'],2880)
        self.assertEqual(r['confirmation_pose_files_opened'],0)
    def test_roundoff_accepted_not_hidden(self):
        r=compare({'error_degrees':0.0},{'error_degrees':1e-6})
        self.assertFalse(r['bit_identical']); self.assertEqual(r['differing_float_values'],1)
    def test_angle_drift_rejected(self):
        with self.assertRaises(ValueError): compare({'error_degrees':0.0},{'error_degrees':.001})
    def test_clock_drift_rejected(self):
        with self.assertRaises(ValueError): compare({'seconds':0.0},{'seconds':1e-6})
    def test_discrete_drift_rejected(self):
        with self.assertRaises(ValueError): compare({'decision':True},{'decision':False})
    def test_scalar_indices(self):
        t=[i/20 for i in range(1201)]
        a,b=scalar_select(t,t); s=select_indices(t,t)
        self.assertTrue(a); self.assertEqual(b,s['indices'])
    def test_scalar_independent_identity(self):
        self.assertEqual(scalar_yaw_pitch([0,0,0,1]),(90,0))
        self.assertAlmostEqual(sum(sum(row) for row in scalar_weights(90,0)),1)


if __name__=='__main__': unittest.main()
