"""Post-freeze tests for exact platform-difference retention."""
import unittest
from .replication import differences, witness_only


class DifferenceTests(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(differences({'a': [1, None]}, {'a': [1, None]}), [])

    def test_type_not_coerced(self):
        self.assertEqual(len(differences(True, 1)), 1)

    def test_complete_path(self):
        self.assertEqual(differences({'a': [1, 2]}, {'a': [1, 3]}),
                         [{'path': '/a/1', 'primary': 2, 'replica': 3}])

    def test_missing_keys(self):
        self.assertEqual(len(differences({'a': 1}, {'a': 1, 'b': 2})), 1)

    def test_missing_rows(self):
        self.assertEqual(len(differences([1], [1, 2])), 1)

    def test_witness_classification(self):
        self.assertTrue(witness_only([{'path': '/extremal_mask_witnesses/maximum_mask_id/5/0', 'primary': 132, 'replica': 84}]))

    def test_no_bound_tolerance(self):
        self.assertFalse(witness_only([{'path': '/lower/2/3', 'primary': 1, 'replica': 2}]))

    def test_witness_ids_validated(self):
        self.assertFalse(witness_only([{'path': '/extremal_mask_witnesses/minimum_mask_id/2/60', 'primary': 132, 'replica': 84}]))
        self.assertFalse(witness_only([{'path': '/extremal_mask_witnesses/minimum_mask_id/2/0', 'primary': 216, 'replica': 84}]))


if __name__ == '__main__':
    unittest.main()
