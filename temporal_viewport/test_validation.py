import unittest
import numpy as np
from temporal_viewport.run import OUT, DATA, score_arrays, independent, scalar_witness
from adaptive_audit.run import read_gzip
from metric_contract.core import path_arrays, TICKS
from admission_contract.core import clocks, ETA


class ScoringTests(unittest.TestCase):
    def test_independent_full_search(self):
        costs = np.tile([1, 1, 100000, 200000, 400000, 800000], (6, 1)); ds = [10*TICKS]*6; reserve = 800000
        arrays = path_arrays(costs, 4, reserve); ends = clocks(costs, arrays['choices'], ds, ETA)
        table = {'parts': [{str(int(e)): {'lower': [0, 1, 4, 6], 'full_family_samples': 10}
                          for e in np.unique(ends[:, j, :])} for j in range(4)]}
        tables = [table, table]; safe, gain, full = score_arrays(tables, arrays['choices'], ends, ds)
        maximum, minimum, count = independent(tables, costs, ds, reserve, 10*TICKS, ETA)
        self.assertEqual(maximum, int(gain[safe].max())); self.assertEqual(count, len(gain))
        self.assertTrue((full == 40).all())
        path = arrays['choices'][int(np.argmax(gain))].tolist()
        self.assertEqual(scalar_witness(tables, path, costs, ds, reserve, ETA)[1], maximum)


@unittest.skipUnless((OUT/'metadata.json').exists(), 'Results not published yet')
class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = read_gzip(OUT/'results.json.gz'); cls.features = read_gzip(DATA/'features.json.gz')

    def test_complete_fixed_grid(self):
        self.assertEqual(len(self.result['rows']), 168*9*2)
        self.assertEqual(len(self.result['summary']), 18)
        self.assertFalse(self.result['service_contract_changed'])

    def test_training_is_disjoint(self):
        for c in self.features['configurations']:
            if not c['model'].startswith('crossfit'): continue
            _, scene, a, b = c['key'].split(':')
            self.assertEqual(len(c['training_keys']), 130)
            self.assertTrue(all(k.split(':')[1] != scene and k.split(':')[2] not in (a, b) for k in c['training_keys']))

    def test_no_raw_poses_or_anchors_published(self):
        forbidden = {'yaw', 'pitch', 'poseTime', 'mediaTime', 'anchor', 'mask_ids'}
        def walk(obj):
            if isinstance(obj, dict):
                self.assertFalse(forbidden & set(obj))
                for value in obj.values(): walk(value)
            elif isinstance(obj, list):
                for value in obj: walk(value)
        walk(self.features)


if __name__ == '__main__':
    unittest.main()
