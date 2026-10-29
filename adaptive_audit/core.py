"""Resource/clock Bellman upper bound against an explicit response adversary."""
from functools import lru_cache
from itertools import product
from typing import NamedTuple
import numpy as np
from metric_contract.core import CAP, SLOT, SETUP, TICKS
from duration_contract.core import DEADLINE
from admission_contract.core import ETA
from geometric_admission.geometry import matrix


class State(NamedTuple):
    stage: int = 2
    spent: int = 0
    request: int = 0
    recipient_end: int = 0
    donor_end: int = 0


def advance(state, pair, costs, durations, reserve, eta=ETA, wait=0):
    """Earliest permitted request, plus optional charged nonnegative waiting."""
    if not 2 <= state.stage < 6 or eta < 0 or wait < 0:
        raise ValueError("Invalid stage or timing allowance")
    if len(pair) != 2 or any(r not in range(2, 6) for r in pair):
        raise ValueError("Whole-segment structural rungs 2..5 required")
    t = state.stage; sa, sb = (int(costs[t, r]) for r in pair)
    if min(sa, sb) <= 0 or durations[t] <= 0:
        raise ValueError("Positive file sizes and durations required")
    total = sa+sb; spent = state.spent+max(0, total-2*int(costs[t, 2]))
    if total > CAP or spent > reserve:
        return None
    start = state.request+wait
    arrival = (start+SETUP+min(2*sa, total), start+SETUP+min(2*sb, total))
    ends = (max(state.recipient_end, arrival[0])+int(durations[t])+eta,
            max(state.donor_end, arrival[1])+int(durations[t])+eta)
    return State(t+1, spent, max(start+SLOT, *arrival), *ends)


def response_table(maps, family, witnesses):
    """One actual geometric ten-mask response per committed recipient rung.

    Uses shared masks for reference and selected representation. Responses are
    synthetic counterexamples, not actual participant feedback or predictions.
    Returns signed differences of separately rounded native MSE quantities.
    """
    maps = np.asarray(maps, dtype=float)
    if maps.shape != (6, 60, 72) or not np.isfinite(maps).all():
        raise ValueError("Finite sender map required")
    weights = matrix(family)
    delta = np.zeros((6, 6), dtype=np.int64); rows = []
    for t, rung in product(range(2, 6), range(2, 6)):
        ids = [int(witnesses['minimum_mask_id'][rung][s]) for s in range(t*10, (t+1)*10)]
        selected = weights[ids]
        mses = np.sum(maps[:, t*10:(t+1)*10, :]*selected[None, :, :], axis=2).mean(axis=1)
        native = np.floor(mses*1e6+.5).astype(np.int64)
        delta[t, rung] = native[2]-native[rung]
        rows.append({'segment': t, 'committed_recipient_rung': rung,
                     'mask_ids': ids, 'all_rung_native_mse': native.tolist(),
                     'signed_credit_rate': int(delta[t, rung])})
    return delta, rows


def solve(costs, durations, reserve, reward, eta=ETA):
    """Max total credit against the fixed causal mask response, floors relaxed.

    This is an UPPER bound on the original robust control problem, not its
    exact optimum: the chosen adversary need not minimize rounded credit.
    Future resource states do not depend on observed quality. Full feedback
    about earlier responses therefore adds no branches to this recursion.
    """
    costs = np.asarray(costs, dtype=np.int64)
    reward = np.asarray(reward, dtype=np.int64)
    if costs.shape != (6, 6) or reward.shape != (6, 6) or len(durations) != 6 or reserve < 0:
        raise ValueError("Invalid finite contract arrays")

    @lru_cache(None)
    def visit(state):
        if state.stage == 6:
            return (0, state.spent, ())
        choices = []
        for pair in product(range(2, 6), repeat=2):
            nxt = advance(state, pair, costs, durations, reserve, eta)
            if nxt is None:
                continue
            future, spent, path = visit(nxt)
            credit = max(0, int(reward[state.stage, pair[0]]))*int(durations[state.stage])
            if nxt.recipient_end > DEADLINE:
                credit = 0
            choices.append((credit+future, spent, (pair,)+path))
        if not choices:
            raise ValueError("No resource-valid continuation")
        return min(choices, key=lambda x: (-x[0], x[1], x[2]))

    gain, spent, path = visit(State())
    return {'credit_upper': gain, 'extra_bytes': spent, 'path': [list(a) for a in path],
            'bellman_states': visit.cache_info().currsize}


def score_path(path, costs, durations, reserve, reward, eta=ETA, waits=None):
    state = State(); gain = 0; rows = []
    waits = [0]*4 if waits is None else waits
    if len(path) != 4 or len(waits) != 4:
        raise ValueError("Exactly four whole-segment decisions required")
    for pair, wait in zip(path, waits):
        nxt = advance(state, pair, costs, durations, reserve, eta, wait)
        if nxt is None:
            raise ValueError("Infeasible resource path")
        g = max(0, int(reward[state.stage, pair[0]]))*int(durations[state.stage])
        credited = g if nxt.recipient_end <= DEADLINE else 0
        rows.append({'segment': state.stage, 'pair': list(pair), 'request_ticks': state.request+wait,
                     'recipient_end_ticks': nxt.recipient_end, 'donor_end_ticks': nxt.donor_end,
                     'credit': credited, 'extra_bytes_total': nxt.spent})
        gain += credited; state = nxt
    return {'credit': gain, 'extra_bytes': state.spent, 'steps': rows}


def feedback_visibility(steps, durations, delay_ticks=0):
    """Completed reports and 1 Hz midpoint samples from earlier played segments.

    Timing illustration only: sample telemetry at presentation+delay is an
    optimistic information envelope, not a newly validated wire protocol.
    """
    if delay_ticks < 0:
        raise ValueError("Negative feedback delay")
    rows = []
    for row in steps:
        visible = []
        for earlier in steps:
            if earlier['segment'] >= row['segment']:
                continue
            end = earlier['recipient_end_ticks']
            start = end-int(durations[earlier['segment']])
            samples = sum(start+(2*s+1)*TICKS//2+delay_ticks <= row['request_ticks'] for s in range(10))
            visible.append({'segment': earlier['segment'], 'samples_available': samples,
                            'completed_report_available': end+delay_ticks <= row['request_ticks']})
        rows.append({'decision_segment': row['segment'], 'past_segment_information': visible,
                     'own_segment_samples_before_commit': 0})
    return rows
