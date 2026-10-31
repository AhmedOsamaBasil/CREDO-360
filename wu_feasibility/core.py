"""Causal entry projection, independent ledgers and Wu-native response scoring."""
from itertools import product
import math
import numpy as np
from metric_contract.core import CAP, TICKS
from admission_contract.core import forecast, psnr_units, control_path, path_stats, pick
from geometric_admission.geometry import matrix


def entry(past, durations):
    """Accept exactly the completed past: no future-quality argument."""
    past = np.asarray(past)
    if past.shape != (2, 2, 6) or past.dtype.kind not in 'iu' or (past > 0).any():
        raise ValueError('Two completed native-quality parents required')
    return {'loss': sum(max(0, int(past[t, 0, 2])-int(past[t, 0, 0])) * int(durations[t]) for t in (0, 1)),
        'past_reference_mse': (-past[:, :, 2]).tolist(),
        'past_psnr': [[psnr_units(int(past[t, 0, 0])), psnr_units(int(past[t, 1, 2]))] for t in (0, 1)]}


def plan(maps, costs, durations, reserve, completed, arrays, ends, eta):
    """Sender data plus past entry only; future offline labels never enter."""
    if completed['loss'] == 0:
        return {'status': 'no_event', 'selections': {}}
    # Preserve the original predictor's domain instead of introducing a new epsilon.
    if min(x for row in completed['past_reference_mse'] for x in row) <= 0:
        return {'status': 'forecast_domain_invalid', 'selections': {}}
    area = np.repeat(np.cos(np.deg2rad(np.linspace(75, -75, 6))), 12)
    area /= area.sum()
    sphere = (maps * area).sum(axis=2).reshape(6, 6, 10).mean(axis=2).T
    if (sphere <= 0).any():
        return {'status': 'forecast_domain_invalid', 'selections': {}}
    predicted = forecast(maps, completed['past_reference_mse'])
    safe, gain = path_stats(predicted - predicted[:, :, 2:3], arrays['choices'], ends, durations)
    lookup = {tuple(p.flat): i for i, p in enumerate(arrays['choices'])}
    selections = {'point_planner': pick(gain, safe, arrays['cost'], completed['loss'])}
    for name in ('cost_greedy', 'rolling_nash', 'maxmin'):
        chosen = control_path(name, predicted, costs, durations, reserve,
                              completed['past_psnr'], completed['loss'], eta)
        selections[name] = lookup[tuple(chosen.flat)]
    return {'status': 'valid', 'selections': selections, 'safe': safe, 'gain': gain}


def scalar_paths(costs, durations, reserve, eta):
    """Independent DFS resource/timing enumeration; no vector clock reuse."""
    rows = []
    def visit(t, spent, request, previous, path, ends):
        if t == 6:
            rows.append((tuple(path), spent, tuple(ends)))
            return
        for a, b in product(range(2, 6), repeat=2):
            sa, sb = int(costs[t, a]), int(costs[t, b])
            total = sa + sb
            new_spent = spent + max(0, total - 2 * int(costs[t, 2]))
            if total > 1500000 or new_spent > reserve:
                continue
            arrival = tuple(request + 19500 + min(2*n, total) for n in (sa, sb))
            finish = tuple(max(previous[u], arrival[u]) + int(durations[t]) + eta for u in (0, 1))
            visit(t+1, new_spent, max(request+1500000, *arrival), finish,
                  path+[(a, b)], ends+[finish])
    visit(2, 0, 0, (0, 0), [], [])
    return rows


def scalar_maximum(delta, durations, ledger):
    """Exact scalar observed-trace maximum with both late-parent floors."""
    rewards = {(t, a, b): (int(delta[t, 0, a]) >= 0 and int(delta[t, 1, b]) >= 0,
                           max(0, int(delta[t, 0, a])) * int(durations[t]))
               for t, a, b in product(range(2, 6), range(2, 6), range(2, 6))}
    best = -1
    for path, _, ends in ledger:
        credit = 0
        for j, (a, b) in enumerate(path):
            safe, gain = rewards[j+2, a, b]
            if not safe:
                break
            if ends[j][0] <= 6000000:
                credit += gain
        else:
            best = max(best, credit)
    if best < 0:
        raise ValueError('Reference path missing from scalar oracle')
    return best


def scalar_account(q, durations, path, costs, reserve, eta):
    """Independent chosen-path resource, floor and completion ledger."""
    spent = request = credit = eventual = 0
    finish = [0, 0]; floors = [0, 0]; gains = []; ends = []
    loss = sum(max(0, int(q[t, 0, 2])-int(q[t, 0, 0])) * int(durations[t]) for t in (0, 1))
    if len(path) != 4:
        raise ValueError('Four parents required')
    for t, pair in zip(range(2, 6), path):
        if len(pair) != 2 or any(r not in range(2, 6) for r in pair):
            raise ValueError('Invalid rungs')
        a, b = pair; sizes = [int(costs[t, r]) for r in pair]; total = sum(sizes)
        spent += max(0, total - 2 * int(costs[t, 2]))
        if total > CAP or spent > reserve:
            raise ValueError('Resource violation')
        arrival = [request+19500+min(2*n, total) for n in sizes]
        finish = [max(finish[u], arrival[u])+int(durations[t])+eta for u in (0, 1)]
        request = max(request+10*TICKS, *arrival)
        gain = max(0, int(q[t, 0, a])-int(q[t, 0, 2]))*int(durations[t])
        gains.append(gain); eventual += gain; ends.append(list(finish))
        if finish[0] <= 40*TICKS:
            credit += gain
        for u, rung in enumerate(pair):
            floors[u] += int(q[t, u, rung] < q[t, u, 2])
    half = bool(2*credit >= loss) if loss else None
    score = {'loss_micro_mse_ticks': loss, 'segment_gain_micro_mse_ticks': gains,
        'deadline_credit': min(loss, credit), 'eventual_credit': min(loss, eventual),
        'deadline_unpaid': round(max(0, loss-credit)/loss, 12) if loss else None,
        'eventual_unpaid': round(max(0, loss-eventual)/loss, 12) if loss else None,
        'half_by_deadline': half, 'protected_half_by_deadline': bool(half and not any(floors)) if loss else None,
        'recipient_floor_violations': floors[0], 'donor_floor_violations': floors[1]}
    return {'score': score, 'raw_credit': credit, 'extra_bytes': spent, 'ends': ends}


def response(maps, masks, witnesses):
    """Fixed geometric adversary, matching Wu nearest-even negative units."""
    weights = matrix(masks); delta = np.zeros((6, 6), dtype=np.int64); rows = []
    areas = [math.cos(math.radians(75-30*(i//12))) for i in range(72)]
    for t, rung in product(range(2, 6), range(2, 6)):
        ids = [int(x) for x in witnesses['minimum_mask_id'][rung][t*10:(t+1)*10]]
        mse = (maps[:, t*10:(t+1)*10, :]*weights[ids][None, :, :]).sum(axis=2).mean(axis=1)
        native = np.rint(-mse*1e6).astype(np.int64)
        scalar = []
        for r in range(6):
            samples = []
            for j, mid in enumerate(ids):
                bits = int(masks[mid]['mask_hex'], 16)
                tiles = [i for i in range(72) if bits >> i & 1]
                denominator = math.fsum(areas[i] for i in tiles)
                samples.append(math.fsum(float(maps[r, 10*t+j, i])*areas[i] for i in tiles)/denominator)
            scalar.append(round(-math.fsum(samples)/10*1e6))
        if native.tolist() != scalar:
            raise ValueError('Independent Wu response rounding mismatch')
        delta[t, rung] = native[rung]-native[2]
        rows.append({'parent': t, 'recipient_rung': rung, 'mask_ids': ids,
                     'negative_micro_mse': scalar, 'signed_credit_rate': int(delta[t, rung])})
    return delta, rows
