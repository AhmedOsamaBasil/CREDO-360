import gzip
import json
import unittest
import numpy as np
from feedback_opportunity.feedback import weights
from geometric_admission.geometry import family,bounds,matrix
from geometric_admission.diagnose import upper_on_worst,SOURCE


class WorstCaseTests(unittest.TestCase):
    def test_rounding_guard_upper_covers_constructed_minima(self):
        rows=family();w=matrix(rows);rng=np.random.default_rng(787)
        maps=rng.uniform(1,100,(6,60,72));lower,_,witness=bounds(maps,rows);upper=upper_on_worst(lower)
        for t in range(6):
            for rung in range(6):
                chosen=[witness['minimum_mask_id'][rung][s] for s in range(10*t,10*t+10)]
                mse=(maps[:,t*10:(t+1)*10,:]*w[chosen][None,:,:]).sum(axis=2).mean(axis=1)
                native=np.floor(mse*1e6+.5).astype(np.int64)
                self.assertLessEqual(native[2]-native[rung],upper[t,rung])

    def test_reference_never_gets_artificial_credit(self):
        upper=upper_on_worst(np.zeros((6,6),dtype=np.int64))
        self.assertTrue((upper[:,2]==0).all())


@unittest.skipUnless(SOURCE.exists(),'Published geometric batch unavailable')
class ArtifactTests(unittest.TestCase):
    def setUp(self):
        with gzip.open(SOURCE,'rt') as f:self.result=json.load(f)

    def test_full_mask_and_batch_coverage(self):
        self.assertEqual(len(self.result['family']),216);self.assertEqual(len(self.result['rows']),3192)
        self.assertEqual(self.result['checks']['unchanged_point_controls'],1344)
        self.assertEqual(self.result['checks']['weighted_values_checked'],466560)

    def test_interval_nesting(self):
        for s in self.result['scene_envelopes']:
            self.assertTrue((np.array(s['lower'])>=np.array(s['convex_lower'])).all())
            self.assertTrue((np.array(s['upper'])<=np.array(s['convex_upper'])).all())

    def test_rejections_preserved_and_never_false_on_exposed_data(self):
        for b in self.result['bounds']:
            if b['convex_certificate']['status']=='impossible':self.assertEqual(b['certificate']['status'],'impossible')
            if b['certificate']['status']=='impossible':self.assertFalse(b['oracle_feasible'])

    def test_zero_admission_precision_is_undefined(self):
        for r in self.result['summary']:
            if r['admitted']==0:self.assertIsNone(r['precision'])


if __name__=='__main__':unittest.main()
