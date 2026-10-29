"""Structured scope checks, not automated verification of arbitrary prose."""

SCOPES = {
    'known_trace': {'future_known', 'finite_catalogue', 'not_online_admission'},
    'optimistic_rejection': {'floor_relaxed_upper', 'finite_catalogue', 'fixed_contract'},
    'universal_policy_limit': {'deterministic', 'whole_segment_commitment',
        'unrestricted_sampled_futures', 'per_policy_counterexample',
        'not_expected_randomized', 'not_smooth_human_motion'},
    'failed_temporal_certificate': {'sufficient_lower_only', 'not_coupled_impossibility',
        'empirical_speed_not_guarantee', 'source_clock_only'},
    'paced_measurement': {'scripted_arrivals', 'decode_and_software_pacing',
        'not_pixel_rendering', 'not_network_measurement', 'not_human_qoe'},
}


def validate_claim(claim):
    kind = claim['kind']
    if kind not in SCOPES:
        raise ValueError('Unknown evidence kind')
    if not SCOPES[kind] <= set(claim['qualifiers']):
        raise ValueError('Missing required scope qualifiers')
    if claim.get('deployment_guarantee') or claim.get('human_qoe_validated'):
        raise ValueError('Unsupported promotion to deployment or human QoE')
    return claim


def make_claim(kind, statement, sources):
    return validate_claim({'kind': kind, 'statement': statement, 'sources': sources,
        'qualifiers': sorted(SCOPES[kind]), 'deployment_guarantee': False,
        'human_qoe_validated': False})
