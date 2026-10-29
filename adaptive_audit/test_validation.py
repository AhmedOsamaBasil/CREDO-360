"""Additional input-isolation and published-artifact checks."""
from copy import deepcopy
import unittest
from adaptive_audit.run import projected_entries, OUT, read_gzip, scalar_response_check
from adaptive_audit.core import response_table
from geometric_admission.geometry import family, bounds
import numpy as np


class InputTests(unittest.TestCase):
    def test_future_fields_cannot_enter_debt_projection(self):
        source = {'bounds': [{'key': str(i), 'cohort': 'synthetic', 'scene': 'synthetic',
                  'loss': i+1, 'eta': 'half_second', 'oracle_max_credit': 999} for i in range(168)]}
        original = projected_entries(source)
        changed = deepcopy(source)
        for row in changed['bounds']:
            row['oracle_max_credit'] = -999; row['future_viewport'] = 'unavailable'
        self.assertEqual(original, projected_entries(changed))
        self.assertEqual(set(original[0]), {'key', 'cohort', 'scene', 'loss'})

    def test_invalid_past_ledger_rejected(self):
        with self.assertRaises(ValueError): projected_entries({'bounds': []})

    def test_independent_response_and_tamper(self):
        rng = np.random.default_rng(21)
        maps = rng.uniform(1, 30, (6, 60, 72)); masks = family()
        _, _, w = bounds(maps, masks); _, rows = response_table(maps, masks, w)
        self.assertEqual(scalar_response_check(maps, masks, rows), 96)
        rows[0]['signed_credit_rate'] += 1
        with self.assertRaises(ValueError): scalar_response_check(maps, masks, rows)


@unittest.skipUnless((OUT/'metadata.json').exists(), 'Published analytical artifact not yet present')
class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = read_gzip(OUT/'results.json.gz')

    def test_complete_population_and_contract(self):
        r = self.result
        self.assertEqual(len(r['rows']), 336)
        self.assertEqual(len(r['contexts']), 12)
        self.assertFalse(r['contract_changed'])
        self.assertFalse(r['future_participant_labels_used'])

    def test_upper_bound_and_target_not_relaxed(self):
        for row in self.result['rows']:
            self.assertLessEqual(row['response_credit_upper'], row['generous_credit_upper'])
            self.assertEqual(row['adaptive_universal_half_ruled_out'], 2*row['response_credit_upper'] < row['loss'])

    def test_no_precommit_future_samples(self):
        for context in self.result['contexts']:
            for rows in context['feedback_timing'].values():
                for row in rows:
                    self.assertEqual(row['own_segment_samples_before_commit'], 0)
                    self.assertTrue(all(x['segment'] < row['decision_segment'] for x in row['past_segment_information']))


if __name__ == '__main__':
    unittest.main()
