"""Synthetic integration tests; no new Wu feasibility outcomes are queried."""
import copy
import json
import unittest
from unittest.mock import patch
import numpy as np
from metric_contract.core import path_arrays, TICKS
from duration_contract.core import account
from admission_contract.core import clocks, path_stats, ETA
from geometric_admission.geometry import family, bounds
from confirmation_protocol.protocol import endpoint
from .core import entry, plan, scalar_paths, scalar_maximum, scalar_account, response
from .run import evaluate_clip, summarize, execute
from .spec import REGISTRATION, verify, digest


def fixture():
    maps = np.broadcast_to(np.array([100., 80., 60., 20., 10., 5.])[:, None, None], (6, 60, 72)).copy()
    costs = np.tile([50000, 70000, 100000, 110000, 2000000, 3000000], (6, 1))
    q = np.tile(-np.array([100, 80, 60, 20, 10, 5])*1000000, (6, 2, 1))
    return maps, costs, [1500000]*6, q, 800000


class CausalTests(unittest.TestCase):
    def test_entry_accepts_only_completed_parents(self):
        _, _, ds, q, _ = fixture()
        self.assertEqual(entry(q[:2], ds[:2])['loss'], 120000000000000)
        with self.assertRaises(ValueError): entry(q, ds)

    def test_future_changes_do_not_change_plan(self):
        maps, costs, ds, q, reserve = fixture()
        arrays = path_arrays(costs, 4, reserve); ends = clocks(costs, arrays['choices'], ds, ETA)
        a = plan(maps, costs, ds, reserve, entry(q[:2], ds), arrays, ends, ETA)
        q[2:] = -1000000
        b = plan(maps, costs, ds, reserve, entry(q[:2], ds), arrays, ends, ETA)
        self.assertEqual(a['selections'], b['selections'])
        np.testing.assert_array_equal(a['gain'], b['gain'])

    def test_no_event_not_success(self):
        maps, costs, ds, q, reserve = fixture(); q[:2, 0, 0] = q[:2, 0, 2]
        arrays = path_arrays(costs, 4, reserve)
        self.assertEqual(plan(maps, costs, ds, reserve, entry(q[:2], ds), arrays, None, ETA)['status'], 'no_event')

    def test_zero_reference_not_smoothed(self):
        maps, costs, ds, q, reserve = fixture(); q[:2, :, 2] = 0
        arrays = path_arrays(costs, 4, reserve)
        self.assertEqual(plan(maps, costs, ds, reserve, entry(q[:2], ds), arrays, None, ETA)['status'], 'forecast_domain_invalid')

    def test_zero_sender_sphere_not_smoothed(self):
        maps, costs, ds, q, reserve = fixture(); maps[3] = 0
        arrays = path_arrays(costs, 4, reserve)
        self.assertEqual(plan(maps, costs, ds, reserve, entry(q[:2], ds), arrays, None, ETA)['status'], 'forecast_domain_invalid')

    def test_zero_single_sample_does_not_change_predictor_domain(self):
        maps, costs, ds, q, reserve = fixture(); maps[3, 0] = 0
        arrays = path_arrays(costs, 4, reserve); ends = clocks(costs, arrays['choices'], ds, ETA)
        self.assertEqual(plan(maps, costs, ds, reserve, entry(q[:2], ds), arrays, ends, ETA)['status'], 'valid')


class AccountingTests(unittest.TestCase):
    def test_scalar_complete_path_clocks(self):
        _, costs, ds, _, reserve = fixture()
        for eta in (0, ETA):
            arrays = path_arrays(costs, 4, reserve); ends = clocks(costs, arrays['choices'], ds, eta)
            ledger = scalar_paths(costs, ds, reserve, eta)
            self.assertEqual(len(ledger), len(ends))
            for i, (path, spent, finish) in enumerate(ledger):
                self.assertEqual(path, tuple(map(tuple, arrays['choices'][i])))
                self.assertEqual(spent, arrays['cost'][i])
                self.assertEqual(finish, tuple(map(tuple, ends[i])))

    def test_scalar_oracle_and_score(self):
        _, costs, ds, q, reserve = fixture()
        arrays = path_arrays(costs, 4, reserve); ends = clocks(costs, arrays['choices'], ds, ETA)
        delta = q-q[:, :, 2:3]; safe, gain = path_stats(delta, arrays['choices'], ends, ds)
        self.assertEqual(scalar_maximum(delta, ds, scalar_paths(costs, ds, reserve, ETA)), int(gain[safe].max()))
        for i in (0, 17, len(ends)-1):
            p = arrays['choices'][i].tolist()
            self.assertEqual(scalar_account(q, ds, p, costs, reserve, ETA)['score'], account(q, ds, p, ends[i].tolist()))

    def test_scalar_oracle_late_floors_change_maximum(self):
        _, costs, ds, q, reserve = fixture()
        q[3, 0, 3] = q[3, 0, 2]-1
        q[4, 1, 3] = q[4, 1, 2]-1
        arrays = path_arrays(costs, 4, reserve); ends = clocks(costs, arrays['choices'], ds, ETA)
        delta = q-q[:, :, 2:3]; safe, gain = path_stats(delta, arrays['choices'], ends, ds)
        self.assertFalse(safe.all())
        self.assertEqual(scalar_maximum(delta, ds, scalar_paths(costs, ds, reserve, ETA)), int(gain[safe].max()))

    def test_late_parent_floor_retained(self):
        _, costs, ds, q, reserve = fixture(); q[5, 1, 3] = q[5, 1, 2]-1
        result = scalar_account(q, ds, [[3, 3]]*4, costs, reserve, ETA)
        self.assertGreater(result['ends'][-1][0], 40*TICKS)
        self.assertEqual(result['score']['donor_floor_violations'], 1)
        self.assertFalse(result['score']['protected_half_by_deadline'])

    def test_no_event_account_nullable(self):
        _, costs, ds, q, reserve = fixture(); q[:2, 0, 0] = q[:2, 0, 2]
        result = scalar_account(q, ds, [[3, 3]]*4, costs, reserve, ETA)
        self.assertIsNone(result['score']['protected_half_by_deadline'])
        self.assertIsNone(result['score']['deadline_unpaid'])

    def test_invalid_resource_paths_rejected(self):
        _, costs, ds, q, reserve = fixture()
        with self.assertRaises(ValueError): scalar_account(q, ds, [[5, 5]]*4, costs, reserve, ETA)
        with self.assertRaises(ValueError): scalar_account(q, ds, [[3, 3]]*4, costs, 0, ETA)
        with self.assertRaises(ValueError): scalar_account(q, ds, [[1, 2]]*4, costs, reserve, ETA)

    def test_response_negative_nearest_even_ties(self):
        maps = np.full((6, 60, 72), .0078125)  # 7812.5 micro units, exactly representable
        masks = [{'mask_hex': (1).to_bytes(9, 'big').hex()}]
        witnesses = {'minimum_mask_id': [[0]*60 for _ in range(6)]}
        delta, rows = response(maps, masks, witnesses)
        self.assertEqual(rows[0]['negative_micro_mse'], [-7812]*6)
        self.assertFalse(delta.any())

    def test_response_scalar_complete_geometric_family(self):
        maps, _, _, _, _ = fixture(); masks = family(); _, _, witnesses = bounds(maps, masks)
        reward, rows = response(maps, masks, witnesses)
        self.assertEqual(len(rows), 16)
        self.assertEqual(reward[2, 3], 40000000)


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.masks = family()
        maps, costs, ds, q, reserve = fixture()
        cls.clip = {'clip': 'fixture', 'condition': 'free', 'experiment': 1, 'eligible': True,
                    'parent_exclusion_reasons': [], 'phase_diagnostic': {},
                    'pairs': [{'recipient': 'a', 'donor': 'b', 'usable': True, 'failed_source_ids': []}]}
        cls.inputs = (maps, costs, ds, {'a': q[:, 0, :], 'b': q[:, 1, :]})
        with patch('wu_feasibility.run.unpack', return_value=cls.inputs):
            cls.result = evaluate_clip(cls.clip, cls.masks)

    def test_full_synthetic_integration(self):
        r = self.result
        self.assertEqual(r['disposition'], 'evaluated')
        self.assertEqual(r['soundness_violations'], 0)
        self.assertTrue(r['primary_endpoint_summary']['complete'])
        self.assertEqual(r['pairs'][0]['modes'][0]['primary_endpoint']['status'], 'admit')

    def test_primary_witness_is_lower_max_not_min_cost(self):
        m = self.result['pairs'][0]['modes'][0]
        self.assertGreaterEqual(m['lower_max_witness']['raw_credit'], m['geometric_certificate']['lower_max_credit'])
        operational = next(c for c in m['controls'] if c['method'] == 'certified_planner')
        self.assertTrue(operational['score']['protected_half_by_deadline'])

    def test_unbounded_never_admits(self):
        self.assertNotEqual(self.result['pairs'][0]['unbounded_certificate']['status'], 'admit')

    def test_reference_infeasible_retained(self):
        maps, costs, ds, labels = copy.deepcopy(self.inputs); costs[3, 2] = 750001
        with patch('wu_feasibility.run.unpack', return_value=(maps, costs, ds, labels)):
            r = evaluate_clip(self.clip, self.masks)
        self.assertEqual(r['disposition'], 'reference_infeasible')
        self.assertEqual(len(r['pairs']), 1)
        summary = summarize([r]); self.assertEqual(summary['clips'][0]['primary_denominator'], 0)
        self.assertEqual(summary['clips'][0]['reference_infeasible'], 1)

    def test_exclusion_retained_without_input_access(self):
        clip = {**self.clip, 'eligible': False, 'parent_exclusion_reasons': ['clock']}
        with patch('wu_feasibility.run.unpack', side_effect=AssertionError('No access')):
            r = evaluate_clip(clip, self.masks)
        self.assertEqual(r['disposition'], 'retained_metadata_exclusion')

    def test_conditions_not_pooled(self):
        second = copy.deepcopy(self.result); second.update(clip='second', condition='focused')
        summary = summarize([self.result, second])
        self.assertEqual(len(summary['conditions']), 2)
        self.assertEqual([c['equal_clip_macro']['admission_fraction']['contributing_clips'] for c in summary['conditions']], [1, 1])

    def test_zero_admissions_undefined(self):
        clip = {**self.clip, 'eligible': False}
        result = evaluate_clip(clip, self.masks)
        self.assertIsNone(summarize([result])['clips'][0]['fulfilled_admission_fraction'])

    def test_soundness_failure_detected(self):
        row = {'clip': 'x', 'recipient': 'a', 'donor': 'b', 'execution_mode': 'conditional_half_second',
               'loss': 10, 'known_max': 2, 'geometric_lower': 3, 'geometric_upper': 4,
               'convex_upper': 5, 'adaptive_upper': 4, 'witness_credit': None, 'witness_floors_ok': None}
        with self.assertRaises(ValueError): endpoint(row)

    def test_old_directory_not_overwritten(self):
        with patch('wu_feasibility.run.verify', return_value={}), \
             patch('wu_feasibility.run.verify_export'), \
             patch('wu_feasibility.run.evaluate_clip', side_effect=AssertionError('No evaluation')):
            with self.assertRaises(FileExistsError): execute(REGISTRATION.parent)

    def test_registration_when_frozen(self):
        if not REGISTRATION.exists(): self.skipTest('Before method freeze')
        self.assertEqual(len(digest(verify())), 64)

    def test_registration_change_rejected(self):
        if not REGISTRATION.exists(): self.skipTest('Before method freeze')
        with patch('wu_feasibility.spec.registration', return_value={'changed': True}):
            with self.assertRaises(ValueError): verify()


if __name__ == '__main__':
    unittest.main()
