import unittest
from unittest.mock import Mock
import numpy as np
from .adapter import adapt_arrays,select_indices,adapt_calibration_trace,validate_spec


class AdapterTests(unittest.TestCase):
    def fixture(self):
        t=np.arange(1201)/20; q=np.tile([0,0,0,1.],(len(t),1))
        return t.copy(),t,q
    def test_complete(self):
        status,pose=adapt_arrays(*self.fixture())
        self.assertTrue(status['accepted']); self.assertEqual(pose.shape,(60,2))
        np.testing.assert_allclose(pose,np.tile([90,0],(60,1)))
    def test_early_reversal_without_crossing(self):
        w,t,q=self.fixture(); t[2]=.01
        self.assertTrue(adapt_arrays(w,t,q)[0]['accepted'])
    def test_multiple_returns_no_partial_pose(self):
        w,t,q=self.fixture(); t[12]=.4
        status,pose=adapt_arrays(w,t,q)
        self.assertFalse(status['accepted']); self.assertIsNone(pose)
        self.assertEqual(status['indices'],[]); self.assertEqual(status['ambiguous_targets'],[.5])
    def test_missing_returns_no_partial_pose(self):
        w,t,q=self.fixture(); t[10:13]=.49; t[13]=.65
        status,pose=adapt_arrays(w,t,q)
        self.assertFalse(status['accepted']); self.assertIsNone(pose)
    def test_wrong_wall_order(self):
        w,t,q=self.fixture(); w[100]=-1
        self.assertFalse(adapt_arrays(w,t,q)[0]['accepted'])
    def test_duplicate_wall_allowed(self):
        w,t,q=self.fixture(); w[3]=w[2]
        self.assertTrue(adapt_arrays(w,t,q)[0]['accepted'])
    def test_bad_selected_quaternion(self):
        w,t,q=self.fixture(); q[10]=0
        with self.assertRaises(ValueError): adapt_arrays(w,t,q)
    def test_no_unselected_pose_repair_needed(self):
        w,t,q=self.fixture(); q[2]=0
        self.assertTrue(adapt_arrays(w,t,q)[0]['accepted'])
    def test_reserved_rejected(self):
        z=Mock()
        with self.assertRaises(ValueError): adapt_calibration_trace(z,'e1v01','1')
        z.open.assert_not_called()
    def test_evidence_binding(self): self.assertEqual(validate_spec()['texture']['wrap_sign'],-1)
    def test_axes_to_existing_tile_coordinates(self):
        w,t,q=self.fixture(); s=np.sqrt(.5); q[:]=[0,s,0,s]
        status,pose=adapt_arrays(w,t,q)
        # +X lies at the seam: +/-180 are the same angular-window coordinate.
        self.assertTrue(np.all(np.abs(np.abs(pose[:,0])-180)<1e-10))
    def test_shape_mismatch(self):
        with self.assertRaises(ValueError): select_indices([0,1],[0])
    def test_stale_repeated_crossing_still_ambiguous(self):
        w,t,q=self.fixture(); t[12]=.4
        status,_=adapt_arrays(w,t,q)
        self.assertIn(.5,status['ambiguous_targets'])
    def test_missing_initial_bracket(self):
        w,t,q=self.fixture(); t[0]=.6
        self.assertIn('missing_initial_bracket',adapt_arrays(w,t,q)[0]['reasons'])
    def test_coverage_through_60(self):
        w,t,q=self.fixture()
        self.assertIn('missing_60s_coverage',adapt_arrays(w[:-1],t[:-1],q[:-1])[0]['reasons'])


if __name__=='__main__': unittest.main()
