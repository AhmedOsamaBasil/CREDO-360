"""Independent scalar enumeration; does not call the vectorized path optimizer."""
from itertools import product


def scalar_frontier(quality, costs, horizon, reserve):
    candidates = []

    def visit(j, spent, start, ends, gains, path):
        if j == horizon:
            candidates.append((spent, sum(g for g, end in gains),
                               sum(g for g, end in gains if end <= horizon*1500000), path))
            return
        t = j+2
        for a, b in product(range(2, 6), repeat=2):
            qa, qb = int(quality[t, 0, a]), int(quality[t, 1, b])
            if qa < quality[t, 0, 2] or qb < quality[t, 1, 2]:
                continue
            sa, sb, baseline = int(costs[t, a]), int(costs[t, b]), 2*int(costs[t, 2])
            next_spent = spent+max(0, sa+sb-baseline)
            if sa+sb > 1500000 or next_spent > reserve:
                continue
            transfer = (2*sa if sa <= sb else sa+sb, 2*sb if sb <= sa else sa+sb)
            arrivals = tuple(start+19500+x for x in transfer)
            next_ends = tuple(max(e, ar)+1500000 for e, ar in zip(ends, arrivals))
            visit(j+1, next_spent, max(start+1500000, *arrivals), next_ends,
                  gains+((max(0, qa-int(quality[t, 0, 2])), next_ends[0]),), path+((a, b),))

    visit(0, 0, 0, (0, 0), (), ())
    return candidates


def compare(candidates, result, clock):
    column = 1 if clock == "media" else 2
    loss = result["loss"]
    if max(p[column] for p in candidates) != result["max_gain"]:
        raise ValueError("Independent maximum gain mismatch")
    if len(candidates) != result["strict_paths"]:
        raise ValueError("Independent feasible-path count mismatch")
    for k, witness in enumerate(result["minimum_cost_witnesses"], 1):
        passing = [p for p in candidates if 4*p[column] >= k*loss] if loss else []
        expected = min((p[0] for p in passing), default=None)
        if (None if witness is None else witness["extra_bytes"]) != expected:
            raise ValueError("Independent minimum-cost witness mismatch")
        if witness is not None:
            path = tuple(tuple(x) for x in witness["rungs"])
            selected = next(p for p in passing if p[3] == path)
            if selected[0] != witness["extra_bytes"] or selected[column] != witness["gain"]:
                raise ValueError("Invalid reported witness")
    return True
