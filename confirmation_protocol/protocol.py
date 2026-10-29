"""Pure preflight, integer endpoint checks and dependence-aware summaries.

No network, media decoding, pose loading or experiment launcher is provided.
Metadata declarations are validated, not independently certified as true.
"""
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'confirmation_protocol'
EXTRA_SCOPES = {
    'measured_completion': {'fixed_selected_paths', 'exposed_or_registered_source',
        'software_events_only', 'separate_clock_domains', 'not_physical_display',
        'not_human_qoe', 'not_hard_execution_bound'},
    'matched_timing_sensitivity': {'fixed_parent_rungs',
        'original_and_secondary_accounts_separate', 'shared_service_and_reserve',
        'not_short_action_optimality', 'no_universal_theorem_transfer'},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load(name):
    return json.loads((PACKAGE / name).read_text(encoding='utf-8'))


def sha_valid(value):
    return isinstance(value, str) and bool(re.fullmatch('[0-9a-f]{64}', value)) and value != '0' * 64


def validate_design(design):
    c = design['contract']
    exact = {'users': 2, 'event_media_seconds': [0, 20],
        'recovery_media_seconds': [20, 60], 'target_fraction': [1, 2],
        'deadline_seconds': 40, 'reference_rung': 2, 'impaired_rung': 0,
        'recovery_rungs': [2, 3, 4, 5], 'parent_seconds_nominal': 10,
        'parents': 4, 'pair_cap_bytes': 1500000,
        'service_payload_bytes_per_second': 150000, 'request_setup_seconds': .13,
        'primary_execution_allowance_seconds': .5}
    require(all(c[k] == v for k, v in exact.items()), 'Original numerical contract changed')
    require(design['decision_rules']['no_optional_stopping'] is True, 'Optional stopping')
    require(design['decision_rules']['no_post_result_replacement'] is True, 'Outcome replacement')
    require(design['timing_confirmation']['automatic_retries'] == 0, 'Automatic retries')
    require(design['timing_confirmation']['repetitions'] == 3, 'Timing repeats changed')
    require(design['sampling']['new_subjects_claim'] is False, 'Unsupported new-subject claim')
    require(design['media_pipeline']['ladder_mbps'] ==
            [0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491], 'Encoding ladder changed')
    return design


def validate_claims(register):
    from feasibility_synthesis.claims import SCOPES
    scopes = {**SCOPES, **EXTRA_SCOPES}
    ids = set()
    for claim in register['claims']:
        require(set(claim) == {'id', 'kind', 'statement', 'qualifiers', 'sources', 'external_test'},
                'Unexpected claim fields')
        require(claim['id'] not in ids, 'Duplicate claim')
        ids.add(claim['id'])
        require(claim['kind'] in scopes, 'Unknown claim kind')
        require(scopes[claim['kind']] <= set(claim['qualifiers']), 'Missing claim qualifier')
        require(bool(claim['sources']) and bool(claim['external_test']), 'Unbound claim')
    require(len(ids) == 6, 'Six fixed claim records required')
    return register


def exposure_inventory(catalogue, root=ROOT):
    q = catalogue['qoevave']
    exposed = set()
    bindings = {}
    for relative in q['exposure_manifests']:
        raw = (root / relative).read_text(encoding='utf-8').replace('\r\n', '\n')
        data = json.loads(raw)
        exposed.update(data['contents'])
        bindings[relative] = hashlib.sha256(raw.encode()).hexdigest()
    available = set(q['trace_linked_clips'])
    require(len(available) == len(q['trace_linked_clips']), 'Duplicate catalogue clip')
    require(exposed <= available, 'Exposed manifest not represented in catalogue')
    family = lambda name: re.sub(r'\d+$', '', name)
    exposed_families = {family(name) for name in exposed}
    unused = sorted(available - exposed)
    return {'catalogue_clips': len(available), 'exposed_clips': sorted(exposed),
        'unused_clips': unused, 'unused_scene_families': sorted({family(n) for n in unused} - exposed_families),
        'new_participant_cohort_verified': False, 'manifest_sha256': bindings}


def directed_cycle(ids):
    require(all(isinstance(i, str) and i.strip() for i in ids), 'Nonempty string source IDs required')
    require(len(ids) == len(set(ids)) and len(ids) >= 2, 'Distinct two-user roster required')
    ordered = sorted(ids)
    return [(u, ordered[(i + 1) % len(ordered)]) for i, u in enumerate(ordered)]


def preflight(manifest, design=None, catalogue=None):
    """Return blocking reasons, not permission or proof of truthful declarations."""
    design = validate_design(design or load('design.json'))
    catalogue = catalogue or load('catalogue.json')
    if manifest is None:
        return {'state': 'blocked_before_outcomes', 'declarations_complete': False,
            'reasons': ['external source manifest not frozen', 'source-specific adapter not frozen',
                'paired media, timing alignment and reuse terms not verified'],
            'starts_experiment': False}
    allowed = {'schema', 'dataset_id', 'design_sha256', 'adapter_sha256',
        'source_catalogue_sha256', 'inventory_complete', 'outcomes_accessed',
        'source_collection_distinct', 'reuse_review_reference', 'coordinate_review_reference',
        'alignment_review_reference', 'clips', 'exclusions'}
    require(set(manifest) == allowed, 'Manifest fields must contain metadata only')
    reasons = []
    check = lambda condition, message: reasons.append(message) if not condition else None
    check(manifest['schema'] == 'confirmation-source-freeze-v1', 'Wrong source schema')
    check(manifest['dataset_id'] in {c['id'] for c in catalogue['external_candidates']}, 'Unreviewed source selection')
    check(manifest['design_sha256'] == digest(design), 'Design hash differs')
    for field in ('adapter_sha256', 'source_catalogue_sha256'):
        check(sha_valid(manifest[field]), 'Missing ' + field)
    check(manifest['inventory_complete'] is True, 'Incomplete source inventory')
    check(manifest['outcomes_accessed'] is False, 'Source outcomes already exposed')
    check(manifest['source_collection_distinct'] is True, 'Not a distinct source collection')
    for field in ('reuse_review_reference', 'coordinate_review_reference', 'alignment_review_reference'):
        check(isinstance(manifest[field], str) and bool(manifest[field].strip()), 'Missing ' + field)
    require(isinstance(manifest['clips'], list) and isinstance(manifest['exclusions'], list), 'Invalid roster')
    ids = set(); asset_windows = set()
    for clip in manifest['clips']:
        require(set(clip) == {'id', 'family', 'media_sha256', 'trace_sha256', 'presentation_offset_seconds',
            'available_seconds', 'eligible_source_ids', 'maximum_required_sample_age_seconds',
            'timestamps_complete', 'frame_mapping_verified'}, 'Unexpected clip field or outcome')
        require(isinstance(clip['id'], str) and bool(clip['id'].strip()), 'Invalid source clip ID')
        require(isinstance(clip['family'], str) and bool(clip['family'].strip()), 'Invalid source family')
        check(clip['id'] not in ids, 'Duplicate source clip')
        ids.add(clip['id'])
        check(bool(clip['family']), 'Missing scene family')
        require(isinstance(clip['media_sha256'], str) and isinstance(clip['trace_sha256'], str),
                'Asset hashes must be strings')
        check(sha_valid(clip['media_sha256']) and sha_valid(clip['trace_sha256']), 'Unbound paired assets')
        for field in ('presentation_offset_seconds', 'available_seconds', 'maximum_required_sample_age_seconds'):
            require(type(clip[field]) in (int, float), 'Finite numeric metadata required')
            require(0 <= clip[field] < float('inf'), 'Negative or nonfinite metadata')
        check(clip['available_seconds'] >= 60, 'Insufficient original presentation interval')
        asset_window = (clip['media_sha256'], clip['presentation_offset_seconds'])
        check(asset_window not in asset_windows, 'Duplicate source-media presentation interval')
        asset_windows.add(asset_window)
        check(clip['maximum_required_sample_age_seconds'] <= .1, 'Stale required trace sample')
        check(clip['timestamps_complete'] is True and clip['frame_mapping_verified'] is True, 'Unverified time mapping')
        try:
            directed_cycle(clip['eligible_source_ids'])
        except ValueError as error:
            reasons.append(str(error))
    check(len(ids) >= 2, 'At least two original clips required for cross-clip description')
    for excluded in manifest['exclusions']:
        require(set(excluded) == {'id', 'stage', 'reason'}, 'Invalid exclusion record')
        require(isinstance(excluded['id'], str) and bool(excluded['id'].strip()), 'Invalid excluded clip ID')
        check(excluded['id'] not in ids, 'Selected clip also excluded')
        ids.add(excluded['id'])
        check(excluded['stage'] == 'metadata_preflight' and bool(excluded['reason']), 'Outcome-driven exclusion')
    candidate = next((c for c in catalogue['external_candidates'] if c['id'] == manifest['dataset_id']), {})
    expected = candidate.get('reported_test_clips', candidate.get('reported_clips'))
    check(expected is not None and len(ids) == expected, 'Source catalogue not completely accounted for')
    return {'state': 'blocked_before_outcomes' if reasons else 'metadata_declarations_complete',
        'declarations_complete': not reasons, 'reasons': reasons, 'starts_experiment': False,
        'warning': 'This validates declarations and hashes syntactically, not permissions, scientific truth or author authorization.'}


def endpoint(record):
    """Integer credit thresholds; observed and universal quantifiers stay separate."""
    required = {'clip', 'recipient', 'donor', 'execution_mode', 'loss', 'known_max', 'geometric_lower',
        'geometric_upper', 'convex_upper', 'adaptive_upper', 'witness_credit', 'witness_floors_ok'}
    require(set(record) == required, 'Unexpected endpoint fields')
    require(all(isinstance(record[k], str) and record[k] for k in ('clip', 'recipient', 'donor')), 'Missing identity')
    require(record['recipient'] != record['donor'], 'Self pair')
    require(record['execution_mode'] == 'conditional_half_second', 'Primary endpoint clock changed')
    for k in required - {'clip', 'recipient', 'donor', 'execution_mode', 'witness_credit', 'witness_floors_ok'}:
        require(type(record[k]) is int and record[k] >= 0, 'Nonnegative integer credits required')
    d, known, lower, upper, convex, adaptive = (record[k] for k in
        ('loss', 'known_max', 'geometric_lower', 'geometric_upper', 'convex_upper', 'adaptive_upper'))
    require(lower <= known <= upper <= convex, 'Bound soundness or nesting violation')
    require(lower <= adaptive <= upper, 'Universal lower/response upper inconsistency')
    # An action-response upper need not exceed credit on the recorded trajectory.
    if d == 0:
        require(record['witness_credit'] is None and record['witness_floors_ok'] is None, 'No-event witness is not recovery')
        return {'status': 'no_event', 'additional_rejection': False, 'opportunity_promise_gap': False}
    feasible = 2 * known >= d
    status = 'admit' if 2 * lower >= d else 'impossible' if 2 * upper < d else 'abstain'
    if status == 'admit':
        require(type(record['witness_credit']) is int and lower <= record['witness_credit'] <= known,
                'Missing or unsound admitted witness credit')
        require(record['witness_floors_ok'] is True, 'Admitted witness violates native floors')
    else:
        require(record['witness_credit'] is None and record['witness_floors_ok'] is None,
                'Nonadmission must not claim a fulfilled witness')
    return {'status': status, 'known_trace_feasible': feasible,
        'universal_promise_ruled_out': 2 * adaptive < d,
        'additional_rejection': 2 * upper < d <= 2 * convex,
        'opportunity_promise_gap': feasible and 2 * adaptive < d,
        'normalized_known_minus_lower': str(Fraction(known - lower, d)),
        'normalized_upper_minus_known': str(Fraction(upper - known, d))}


def summarize_endpoints(records, planned_keys):
    require(len(planned_keys) == len(set(planned_keys)), 'Duplicate planned pair')
    seen = set(); grouped = defaultdict(list)
    for row in records:
        key = (row['clip'], row['recipient'], row['donor'])
        require(key in set(planned_keys) and key not in seen, 'Unexpected or duplicated endpoint')
        seen.add(key); grouped[row['clip']].append(endpoint(row))
    clips = []
    for clip in sorted({key[0] for key in planned_keys}):
        rs = grouped[clip]; positive = [r for r in rs if r['status'] != 'no_event']
        counts = Counter(r['status'] for r in rs)
        n = len(positive); admissions = counts['admit']
        clips.append({'clip': clip, 'planned': sum(k[0] == clip for k in planned_keys),
            'observed': len(rs), 'positive_loss': n, 'counts': dict(counts),
            'additional_rejections': sum(r['additional_rejection'] for r in rs),
            'opportunity_promise_gaps': sum(r['opportunity_promise_gap'] for r in rs),
            'admission_fulfillment_fraction': '1' if admissions else None,
            'additional_rejection_fraction': str(Fraction(sum(r['additional_rejection'] for r in rs), n)) if n else None})
    fractions = [Fraction(r['additional_rejection_fraction']) for r in clips if r['additional_rejection_fraction'] is not None]
    complete = len(seen) == len(planned_keys)
    macro = str(sum(fractions, Fraction()) / len(fractions)) if fractions else None
    return {'planned_pairs': len(planned_keys), 'observed_pairs': len(records),
        'missing_pairs': [list(k) for k in sorted(set(planned_keys) - seen)], 'clips': clips,
        'macro_additional_rejection_fraction': macro if complete else None,
        'observed_only_macro_additional_rejection_fraction': macro,
        'macro_contributing_clips': len(fractions), 'population_inference': False,
        'complete': complete}
