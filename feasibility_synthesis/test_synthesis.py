"""Adversarial join, accounting and claim-scope checks for the synthesis."""
import copy
import unittest
from feasibility_synthesis.claims import SCOPES, make_claim, validate_claim
from feasibility_synthesis.synthesize import load_inputs, summarize, digest, report, index


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_inputs()
        cls.result = summarize(cls.data)

    def changed_geometry(self, action):
        data = dict(self.data); data['geometry'] = copy.deepcopy(data['geometry'])
        action(data['geometry'])
        return data

    def test_sampling_units(self):
        s = self.result['sampling']
        self.assertEqual(s['directed_episodes'], 168)
        self.assertEqual(s['participant_identifiers'], 28)
        self.assertEqual(len(s['scenes']), 6)
        self.assertEqual(s['timing_rows_not_independent_episodes'], 336)
        self.assertFalse(s['independent_replication'])

    def test_partition_and_information_gap(self):
        for r in self.result['summary']:
            self.assertEqual(sum(r['categories'].values()), r['episodes'])
            if r['group'] == 'all':
                self.assertEqual(r['categories'], {'optimistic_infeasible': 134,
                    'trace_feasible_not_guaranteed': 27, 'trace_infeasible_without_optimistic_rejection': 7})
                self.assertEqual(r['unrestricted_universal_ruled_out'], 168)
                self.assertEqual(r['point_promises'], 28)
                self.assertEqual(r['point_fulfilled'], 27)

    def test_metric_cells_remain_separate(self):
        rows = self.result['metric_sensitivity_separate_contract']
        counts = {(r['metric'], r['clock']): r['half_feasible'] for r in rows}
        self.assertEqual([counts[m, 'media'] for m in ('index', 'fine_index', 'psnr_db', 'negative_mse')], [96, 96, 168, 28])
        self.assertEqual(counts['negative_mse', 'deadline'], 27)
        self.assertTrue(all('nominal' in r['contract'] for r in rows))

    def test_failed_controller_retained(self):
        counts = self.result['historical_actual_duration_ideal_replay']['protected_half_by_policy']
        self.assertEqual(counts['prefix_mpc'], 1)
        self.assertEqual(counts['prefix_cost_greedy'], 10)
        self.assertFalse(self.result['submission_ready'])
        self.assertEqual(self.result['new_experiments'], 0)

    def test_measurement_is_not_rendering(self):
        p = self.result['paced_measurement']
        self.assertEqual((p['sessions'], p['frames']), (19, 45594))
        self.assertIn('not rendering/HMD/network', p['scope'])
        self.assertTrue(p['negative_control_zero_credit'])

    def test_duplicate_join_rejected(self):
        d = self.changed_geometry(lambda g: g['bounds'].append(g['bounds'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'): summarize(d)

    def test_missing_timing_cell_rejected(self):
        d = self.changed_geometry(lambda g: g['bounds'].pop())
        with self.assertRaisesRegex(ValueError, 'Missing'): summarize(d)

    def test_debt_mismatch_rejected(self):
        def change(g): g['bounds'][0]['loss'] += 1
        with self.assertRaisesRegex(ValueError, 'Loss ledger'): summarize(self.changed_geometry(change))

    def test_optimistic_rejection_cannot_contradict_trace(self):
        def change(g):
            r = next(r for r in g['bounds'] if r['certificate']['status'] == 'impossible')
            r['oracle_feasible'] = True
        with self.assertRaisesRegex(ValueError, 'contradicts known trace'): summarize(self.changed_geometry(change))

    def test_control_equivalence_checked_not_assumed(self):
        def change(g):
            r = next(r for r in g['rows'] if r['eta'] == 'ideal' and r['method'] == 'point_planner')
            r['executed_path'][0][0] = 5
        with self.assertRaisesRegex(ValueError, 'equivalent'): summarize(self.changed_geometry(change))

    def test_adaptive_scope_not_promoted(self):
        d = dict(self.data); d['adaptive'] = dict(d['adaptive'], future_participant_labels_used=True)
        with self.assertRaisesRegex(ValueError, 'scope'): summarize(d)

    def test_holdout_contamination_rejected(self):
        d = dict(self.data); d['metric'] = dict(d['metric'], fresh_holdout=True)
        with self.assertRaisesRegex(ValueError, 'holdout'): summarize(d)

    def test_all_temporal_models_retained(self):
        for c in self.result['cases']:
            self.assertEqual(len(c['temporal_model_certificates']), 9)
            self.assertFalse(any(c['temporal_model_certificates'].values()))

    def test_source_values_change_hash(self):
        a = {'a': 1, 'b': 2}
        self.assertEqual(digest(a), digest({'b': 2, 'a': 1}))
        self.assertNotEqual(digest(a), digest({'a': 1, 'b': 3}))
        with self.assertRaises(ValueError): digest({'nan': float('nan')})

    def test_report_keeps_negative_scope(self):
        text = report(self.result)
        self.assertIn('no new experiment', text)
        self.assertIn('not an impossibility result for coupled motion', text)
        self.assertIn('not new subjects', text)


class ScopeTests(unittest.TestCase):
    def test_each_qualifier_is_required(self):
        for kind, qualifiers in SCOPES.items():
            for q in qualifiers:
                c = make_claim(kind, 'Example', ['source']); c['qualifiers'].remove(q)
                with self.assertRaisesRegex(ValueError, 'qualifiers'): validate_claim(c)

    def test_deployment_and_human_promotions_rejected(self):
        for field in ('deployment_guarantee', 'human_qoe_validated'):
            c = make_claim('known_trace', 'Example', ['source']); c[field] = True
            with self.assertRaisesRegex(ValueError, 'promotion'): validate_claim(c)

    def test_unknown_scope_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            validate_claim({'kind': 'all_streaming_impossible', 'qualifiers': []})

    def test_index_rejects_unknown_cells(self):
        with self.assertRaisesRegex(ValueError, 'unexpected'):
            index([{'key': 'new'}], ('key',), {('old',)})


if __name__ == '__main__':
    unittest.main()
