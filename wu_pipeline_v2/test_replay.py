"""Independent scalar-replay checks using generated arrays only."""
import copy
import unittest
import numpy as np
from wu_pose.core import project_selected
from wu_pipeline.metrics import aggregate_native
from .replay import scalar_labels, compare, validate_report
from .spec import verify


class ReplayTests(unittest.TestCase):
    def fixture(self):
        return np.ones((6, 60, 6, 12), dtype='<f4'), [['0', '0', '0', '1']] * 60

    def test_constant_map_parent(self):
        means, micro = scalar_labels(*self.fixture(), 10)
        np.testing.assert_allclose(means, 1., rtol=0, atol=1e-15)
        np.testing.assert_array_equal(micro, np.full((6, 6), -1000000))

    def test_constant_map_children(self):
        means, micro = scalar_labels(*self.fixture(), 2)
        self.assertEqual(np.shape(means), (6, 30))
        np.testing.assert_array_equal(micro, np.full((6, 30), -1000000))

    def test_random_generated_maps_and_rotations(self):
        rng = np.random.default_rng(73921)
        maps = rng.uniform(1, 2000, (6, 60, 6, 12)).astype('<f4')
        q = rng.normal(size=(60, 4))
        q /= np.linalg.norm(q, axis=1)[:, None]
        fields = [[str(v) for v in row] for row in q]
        _, poses = project_selected(fields)
        for unit in (2, 10):
            with self.subTest(unit=unit):
                primary = aggregate_native(maps, poses, unit)
                self.assertTrue(compare(primary, *scalar_labels(maps, fields, unit))['pass'])

    def test_negative_quaternion_equivalence(self):
        maps, fields = self.fixture()
        self.assertEqual(scalar_labels(maps, fields, 10), scalar_labels(maps, [['0', '0', '0', '-1']] * 60, 10))

    def test_incorrect_norm_rejected(self):
        maps, fields = self.fixture()
        fields = copy.deepcopy(fields)
        fields[0][3] = '2'
        with self.assertRaises(ValueError):
            scalar_labels(maps, fields, 10)

    def test_missing_frame_rejected(self):
        maps, fields = self.fixture()
        with self.assertRaises(ValueError):
            scalar_labels(maps[:, :-1], fields, 10)

    def test_nonfinite_map_rejected(self):
        maps, fields = self.fixture()
        maps[0, 0, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            scalar_labels(maps, fields, 10)

    def test_micro_mismatch_retained(self):
        means, micro = scalar_labels(*self.fixture(), 10)
        wrong = copy.deepcopy(micro)
        wrong[0][0] += 1
        result = compare({'native_mse': means, 'negative_micro_mse': wrong}, means, micro)
        self.assertFalse(result['pass'])
        self.assertEqual(result['micro_mse_mismatches'], 1)

    def test_native_mismatch_retained(self):
        means, micro = scalar_labels(*self.fixture(), 10)
        wrong = copy.deepcopy(means)
        wrong[0][0] += 2e-9
        self.assertFalse(compare({'native_mse': wrong, 'negative_micro_mse': micro}, means, micro)['pass'])

    def report(self):
        rows = []
        for c in verify()['plan']['clips']:
            if c['eligible']:
                for identity in c['source_ids']:
                    rows.append({'clip': c['clip'], 'source_id': identity,
                        'parent': {'cells': 36, 'maximum_native_mse_difference': 0., 'micro_mse_mismatches': 0, 'pass': True},
                        'child': {'cells': 180, 'maximum_native_mse_difference': 0., 'micro_mse_mismatches': 0, 'pass': True}})
        return {'schema': 'wu-independent-scalar-label-replay-v1', 'rows': rows, 'traces': 452,
                'passed': True, 'micro_mse_mismatches': 0, 'maximum_native_mse_difference': 0.,
                'new_encoding_or_recovery_run': False, 'original_outputs_modified': False}

    def test_complete_synthetic_report(self):
        validate_report(self.report())

    def test_report_false_success_rejected(self):
        report = self.report()
        report['rows'][0]['parent']['micro_mse_mismatches'] = 1
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_report_missing_row_rejected(self):
        report = self.report()
        report['rows'].pop()
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_report_scope_rejected(self):
        report = self.report()
        report['new_encoding_or_recovery_run'] = True
        with self.assertRaises(ValueError):
            validate_report(report)


if __name__ == '__main__':
    unittest.main()
