"""Locked exploratory progression checks, not a significance claim."""
import numpy as np


def screen(summaries, paired, agreement):
    rows = [r for r in summaries if r['scenario'] == 'known_ceiling']
    metrics = ('worst_user_quality', 'post_restoration_shortfall', 'impaired_restoration_shortfall',
               'mean_quality', 'cumulative_shortfall', 'stall_s_per_user', 'active_state_fraction')
    means = {p: {m: float(np.mean([r[m] for r in rows if r['policy'] == p])) for m in metrics}
             for p in ('window_recovery', 'nash', 'memoryless_scaled')}
    candidate = means['window_recovery']
    checks = {'all_20_paired_seeds': len([r for r in rows if r['policy'] == 'window_recovery']) == 20,
              'active_state_above_5_percent': candidate['active_state_fraction'] > .05}
    for baseline in ('nash', 'memoryless_scaled'):
        other = means[baseline]
        contrast = next(r for r in paired if r['scenario'] == 'known_ceiling' and
                        r['baseline'] == baseline and r['metric'] == 'worst_user_quality')
        checks[baseline+'_worst_quality_ci_above_zero'] = contrast['ci95_low'] > 0
        for metric in ('post_restoration_shortfall', 'impaired_restoration_shortfall'):
            checks[baseline+'_'+metric+'_reduced'] = candidate[metric] < other[metric]
        checks[baseline+'_mean_quality_guard'] = candidate['mean_quality'] >= other['mean_quality']-.03
        checks[baseline+'_fixed_shortfall_guard'] = candidate['cumulative_shortfall'] <= 1.05*other['cumulative_shortfall']
        checks[baseline+'_stall_guard'] = candidate['stall_s_per_user']-other['stall_s_per_user'] <= (
            .05*other['stall_s_per_user'] if other['stall_s_per_user'] else .1)
        relevant = [r for r in agreement if r['scenario'] == 'known_ceiling' and r['baseline'] == baseline]
        checks[baseline+'_action_disagreement_above_1_percent'] = (
            sum(r['disagreements'] for r in relevant) / sum(r['comparisons'] for r in relevant) > .01)
    return all(checks.values()), {'checks': checks, 'known_ceiling_means': means}
