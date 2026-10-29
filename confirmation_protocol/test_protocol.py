"""Synthetic design tests and frozen development-evidence checks only."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
import unittest

from confirmation_protocol.protocol import (
    PACKAGE, canonical, digest, directed_cycle, endpoint, exposure_inventory,
    load, preflight, sha_valid, summarize_endpoints, validate_claims, validate_design,
)
from confirmation_protocol.register import OUT, evidence, registration


def row(**changes):
    value = {'clip': 'A', 'recipient': '1', 'donor': '2',
        'execution_mode': 'conditional_half_second', 'loss': 100,
        'known_max': 30, 'geometric_lower': 0, 'geometric_upper': 40,
        'convex_upper': 60, 'adaptive_upper': 20,
        'witness_credit': None, 'witness_floors_ok': None}
    value.update(changes)
    return value


def manifest():
    return {'schema': 'confirmation-source-freeze-v1', 'dataset_id': 'corbillon2017',
        'design_sha256': digest(load('design.json')), 'adapter_sha256': '12' * 32,
        'source_catalogue_sha256': '34' * 32, 'inventory_complete': True,
        'outcomes_accessed': False, 'source_collection_distinct': True,
        'reuse_review_reference': 'synthetic test review',
        'coordinate_review_reference': 'synthetic axis/coordinate test',
        'alignment_review_reference': 'synthetic presentation mapping',
        'clips': [{'id': str(i), 'family': 'synthetic_' + str(i),
            'media_sha256': digest(['synthetic_media', i]), 'trace_sha256': '78' * 32,
            'presentation_offset_seconds': 0, 'available_seconds': 70,
            'eligible_source_ids': ['1', '2', '3'],
            'maximum_required_sample_age_seconds': .02,
            'timestamps_complete': True, 'frame_mapping_verified': True} for i in range(5)],
        'exclusions': []}


class DesignTests(unittest.TestCase):
    def test_original_contract(self):
        self.assertEqual(validate_design(load('design.json'))['contract']['target_fraction'], [1, 2])

    def test_no_relaxed_deadline(self):
        value = load('design.json'); value['contract']['deadline_seconds'] = 41
        with self.assertRaises(ValueError): validate_design(value)

    def test_no_retuned_ladder(self):
        value = load('design.json'); value['media_pipeline']['ladder_mbps'][0] = .1
        with self.assertRaises(ValueError): validate_design(value)

    def test_no_optional_stopping(self):
        value = load('design.json'); value['decision_rules']['no_optional_stopping'] = False
        with self.assertRaises(ValueError): validate_design(value)

    def test_claim_qualifiers(self):
        self.assertEqual(len(validate_claims(load('claims.json'))['claims']), 6)

    def test_cannot_omit_unrestricted_future_qualifier(self):
        value = load('claims.json')
        value['claims'][1]['qualifiers'].remove('unrestricted_sampled_futures')
        with self.assertRaises(ValueError): validate_claims(value)

    def test_no_duplicate_claim(self):
        value = load('claims.json'); value['claims'][1]['id'] = value['claims'][0]['id']
        with self.assertRaises(ValueError): validate_claims(value)

    def test_unsupported_promotion_field_rejected(self):
        value = load('claims.json'); value['claims'][0]['deployment_guarantee'] = True
        with self.assertRaises(ValueError): validate_claims(value)

    def test_cycle_balances_roles_without_outcomes(self):
        pairs = directed_cycle(['2', '10', '1'])
        self.assertEqual(pairs, [('1', '10'), ('10', '2'), ('2', '1')])
        self.assertEqual(sorted(a for a, b in pairs), sorted(b for a, b in pairs))

    def test_bad_roster(self):
        for ids in ([], ['1'], ['1', '1'], ['1', 2]):
            with self.assertRaises(ValueError): directed_cycle(ids)

    def test_existing_inventory_has_no_new_scene_family(self):
        value = exposure_inventory(load('catalogue.json'))
        self.assertEqual(value['catalogue_clips'], 14)
        self.assertEqual(len(value['exposed_clips']), 12)
        self.assertEqual(value['unused_clips'], ['ForestWalk02', 'Skateboarding05'])
        self.assertEqual(value['unused_scene_families'], [])


class PreflightTests(unittest.TestCase):
    def test_actual_state_is_blocked(self):
        self.assertFalse(preflight(None)['declarations_complete'])

    def test_synthetic_complete_metadata_does_not_launch(self):
        value = preflight(manifest())
        self.assertTrue(value['declarations_complete'])
        self.assertFalse(value['starts_experiment'])

    def test_requires_bound_design(self):
        value = manifest(); value['design_sha256'] = 'ab' * 32
        self.assertFalse(preflight(value)['declarations_complete'])

    def test_rejects_already_exposed_source(self):
        value = manifest(); value['outcomes_accessed'] = True
        self.assertIn('Source outcomes already exposed', preflight(value)['reasons'])

    def test_outcome_field_is_not_metadata(self):
        value = manifest(); value['clips'][0]['repayment'] = .9
        with self.assertRaises(ValueError): preflight(value)

    def test_unknown_or_same_source_blocked(self):
        value = manifest(); value['dataset_id'] = 'qoevave'
        self.assertFalse(preflight(value)['declarations_complete'])

    def test_short_or_stale_clip_blocked(self):
        for key, bad in (('available_seconds', 59.99), ('maximum_required_sample_age_seconds', .1001)):
            value = manifest(); value['clips'][0][key] = bad
            self.assertFalse(preflight(value)['declarations_complete'])

    def test_nonfinite_or_boolean_metadata_rejected(self):
        for bad in (float('nan'), float('inf'), -1, True):
            value = manifest(); value['clips'][0]['available_seconds'] = bad
            with self.assertRaises(ValueError): preflight(value)

    def test_missing_mapping_blocked(self):
        value = manifest(); value['clips'][0]['frame_mapping_verified'] = False
        self.assertFalse(preflight(value)['declarations_complete'])

    def test_unaccounted_clip_blocked(self):
        value = manifest(); value['clips'].pop()
        self.assertFalse(preflight(value)['declarations_complete'])

    def test_metadata_exclusion_is_retained(self):
        value = manifest(); excluded = value['clips'].pop()
        value['exclusions'] = [{'id': excluded['id'], 'stage': 'metadata_preflight', 'reason': 'unavailable paired asset'}]
        self.assertTrue(preflight(value)['declarations_complete'])

    def test_post_result_exclusion_blocked(self):
        value = manifest(); excluded = value['clips'].pop()
        value['exclusions'] = [{'id': excluded['id'], 'stage': 'after_outcomes', 'reason': 'bad recovery'}]
        self.assertFalse(preflight(value)['declarations_complete'])

    def test_duplicate_clip_blocked(self):
        value = manifest(); value['clips'][1]['id'] = value['clips'][0]['id']
        self.assertFalse(preflight(value)['declarations_complete'])

    def test_duplicate_media_window_blocked(self):
        value = manifest(); value['clips'][1]['media_sha256'] = value['clips'][0]['media_sha256']
        self.assertFalse(preflight(value)['declarations_complete'])

    def test_invalid_clip_label_rejected(self):
        value = manifest(); value['clips'][0]['id'] = []
        with self.assertRaises(ValueError): preflight(value)

    def test_identity_roster_not_filtered_into_single_user(self):
        value = manifest(); value['clips'][0]['eligible_source_ids'] = ['1']
        self.assertFalse(preflight(value)['declarations_complete'])

    def test_unknown_hash_not_accepted(self):
        self.assertFalse(sha_valid('0' * 64))
        self.assertFalse(sha_valid('unverified'))
        value = manifest(); value['adapter_sha256'] = None
        self.assertFalse(preflight(value)['declarations_complete'])


class EndpointTests(unittest.TestCase):
    def test_geometric_additional_rejection(self):
        result = endpoint(row())
        self.assertEqual(result['status'], 'impossible')
        self.assertTrue(result['additional_rejection'])

    def test_recorded_opportunity_and_universal_failure_compatible(self):
        result = endpoint(row(known_max=70, geometric_upper=90, convex_upper=100, adaptive_upper=40))
        self.assertEqual(result['status'], 'abstain')
        self.assertTrue(result['opportunity_promise_gap'])

    def test_equal_target_is_not_rejection(self):
        self.assertEqual(endpoint(row(geometric_upper=50))['status'], 'abstain')

    def test_zero_debt_not_success(self):
        self.assertEqual(endpoint(row(loss=0))['status'], 'no_event')

    def test_missing_witness_not_admission(self):
        with self.assertRaises(ValueError):
            endpoint(row(geometric_lower=50, known_max=70, geometric_upper=90, convex_upper=100, adaptive_upper=60))

    def test_valid_positive_admission(self):
        result = endpoint(row(geometric_lower=50, known_max=70, geometric_upper=90, convex_upper=100,
                              adaptive_upper=60, witness_credit=55, witness_floors_ok=True))
        self.assertEqual(result['status'], 'admit')

    def test_unsound_witness_or_floor_rejected(self):
        base = row(geometric_lower=50, known_max=70, geometric_upper=90, convex_upper=100,
                   adaptive_upper=60, witness_credit=55, witness_floors_ok=True)
        for key, bad in (('witness_credit', 49), ('witness_credit', 71), ('witness_floors_ok', False)):
            value = deepcopy(base); value[key] = bad
            with self.assertRaises(ValueError): endpoint(value)

    def test_unsound_optimistic_bound_rejected(self):
        with self.assertRaises(ValueError): endpoint(row(known_max=60))

    def test_non_nested_bounds_rejected(self):
        with self.assertRaises(ValueError): endpoint(row(convex_upper=39))

    def test_universal_lower_and_upper_cannot_contradict(self):
        with self.assertRaises(ValueError): endpoint(row(geometric_lower=25, adaptive_upper=20))

    def test_mixed_clock_not_primary(self):
        with self.assertRaises(ValueError): endpoint(row(execution_mode='ideal'))

    def test_native_integer_credit_required(self):
        for bad in (30.1, True, -1):
            with self.assertRaises(ValueError): endpoint(row(known_max=bad))

    def test_complete_small_integer_threshold_grid(self):
        checked = 0
        for d, known, upper, convex in product(range(1, 8), range(7), range(7), range(7)):
            if not known <= upper <= convex: continue
            result = endpoint(row(loss=d, known_max=known, geometric_upper=upper, convex_upper=convex, adaptive_upper=0))
            self.assertEqual(result['status'] == 'impossible', Fraction(upper, d) < Fraction(1, 2))
            self.assertEqual(result['additional_rejection'], Fraction(upper, d) < Fraction(1, 2) <= Fraction(convex, d))
            checked += 1
        self.assertEqual(checked, 588)

    def test_zero_admission_fraction_undefined(self):
        report = summarize_endpoints([row()], [('A', '1', '2')])
        self.assertIsNone(report['clips'][0]['admission_fulfillment_fraction'])

    def test_macro_is_not_pooled_episode_rate(self):
        rows = [row()] + [row(clip='B', recipient=str(i), donor=str(i+1), geometric_upper=50) for i in range(3)]
        keys = [(r['clip'], r['recipient'], r['donor']) for r in rows]
        self.assertEqual(summarize_endpoints(rows, keys)['macro_additional_rejection_fraction'], '1/2')

    def test_missing_rows_withhold_primary_macro(self):
        report = summarize_endpoints([row()], [('A', '1', '2'), ('B', '1', '2')])
        self.assertFalse(report['complete'])
        self.assertEqual(report['missing_pairs'], [['B', '1', '2']])
        self.assertIsNone(report['macro_additional_rejection_fraction'])

    def test_duplicate_or_unplanned_row_rejected(self):
        with self.assertRaises(ValueError): summarize_endpoints([row(), row()], [('A', '1', '2')])
        with self.assertRaises(ValueError): summarize_endpoints([row()], [])


class EvidenceTests(unittest.TestCase):
    def test_existing_evidence_not_independent_confirmation(self):
        current, hashes = evidence()
        self.assertFalse(current['independent_confirmation'])
        self.assertEqual(current['browser_valid'], 74)
        self.assertEqual(current['timing_replay_cells'], 2688)
        self.assertEqual(len(hashes), 4)

    def test_all_claim_sources_and_registration_bindings(self):
        current = registration()
        self.assertEqual(current['readiness']['state'], 'blocked_before_outcomes')
        self.assertEqual(current['new_measurements'], 0)
        self.assertFalse(current['fresh_outcomes_accessed'])
        self.assertEqual(len(current['claim_ids']), 6)

    @unittest.skipUnless((OUT / 'registration.json').exists(), 'Design not yet frozen')
    def test_published_registration_is_unchanged(self):
        saved = json.loads((OUT / 'registration.json').read_text())
        self.assertEqual(saved, registration())
        self.assertEqual(json.loads((OUT / 'metadata.json').read_text())['scientific_sha256'], digest(saved))


if __name__ == '__main__':
    unittest.main()
