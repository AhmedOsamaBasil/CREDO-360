"""Integer-quality and exact-clock finite-path sensitivity reference methods."""
from itertools import product
import numpy as np

TICKS = 150000
SLOT = 10 * TICKS
SETUP = 19500
CAP = 1500000
HORIZONS = (1, 2, 4)
TARGETS = (1, 2, 3, 4)  # quarters


def offsets(sizes):
    a, b = map(int, sizes)
    if min(a, b) <= 0:
        raise ValueError("Positive actual-file sizes required")
    return (SETUP + min(2*a, a+b), SETUP + min(2*b, a+b))


def debt(quality, impairment):
    return sum(max(0, int(quality[t, 0, 2] - quality[t, 0, impairment])) for t in (0, 1))


def score(loss, gain):
    if loss < 0 or gain < 0:
        raise ValueError("Nonnegative debt and credit required")
    if loss == 0:
        return {"applicable": False, "unpaid": None, "targets_met": [None] * 4}
    credit = min(loss, gain)
    return {"applicable": True, "unpaid": round((loss-credit)/loss, 12),
            "targets_met": [4*credit >= k*loss for k in TARGETS]}


def path_arrays(costs, horizon, reserve):
    """Enumerate resource-valid paths without using any quality labels."""
    if horizon not in HORIZONS or reserve < 0:
        raise ValueError("Invalid fixed grid")
    menus = [tuple((a, b) for a, b in product(range(2, 6), repeat=2)
                   if costs[t, a] + costs[t, b] <= CAP) for t in range(2, 2+horizon)]
    if any(not p for p in menus):
        raise ValueError("No baseline-capable action")
    choices = np.array(list(product(*menus)), dtype=np.int64)
    n = len(choices)
    spent = np.zeros(n, dtype=np.int64)
    finish = np.zeros((n, 2), dtype=np.int64)
    ends = np.zeros((n, horizon, 2), dtype=np.int64)
    start = np.zeros(n, dtype=np.int64)
    for j in range(horizon):
        t = 2+j
        a, b = costs[t, choices[:, j, 0]], costs[t, choices[:, j, 1]]
        spent += np.maximum(0, a+b-2*costs[t, 2])
        arrival = start[:, None]+SETUP+np.stack((np.minimum(2*a, a+b), np.minimum(2*b, a+b)), axis=1)
        finish = np.maximum(finish, arrival)+SLOT
        ends[:, j] = finish
        start = np.maximum(start+SLOT, arrival.max(axis=1))
    keep = spent <= reserve
    return {"choices": choices[keep], "cost": spent[keep], "ends": ends[keep],
            "resource_paths": int(keep.sum())}


def metric_paths(quality, arrays, horizon):
    paths = arrays["choices"]
    gains = np.zeros((len(paths), horizon), dtype=np.int64)
    safe = np.ones(len(paths), dtype=bool)
    for j in range(horizon):
        t = 2+j
        a, b = quality[t, 0, paths[:, j, 0]], quality[t, 1, paths[:, j, 1]]
        gains[:, j] = np.maximum(0, a-quality[t, 0, 2])
        safe &= (a >= quality[t, 0, 2]) & (b >= quality[t, 1, 2])
    if not safe.any():
        raise ValueError("Original baseline must be strictly feasible")
    return safe, {"media": gains.sum(axis=1),
                  "deadline": (gains*(arrays["ends"][:, :, 0] <= horizon*SLOT)).sum(axis=1)}


def bound(loss, safe, gains, arrays):
    ids = np.flatnonzero(safe)
    maximum = int(gains[ids].max())
    best = ids[gains[ids] == maximum]
    index = int(best[np.argmin(arrays["cost"][best])])
    witnesses = []
    for k in TARGETS:
        passing = ids[4*gains[ids] >= k*loss] if loss else np.array([], dtype=int)
        if not len(passing):
            witnesses.append(None)
        else:
            chosen = int(passing[np.argmin(arrays["cost"][passing])])
            witnesses.append({"extra_bytes": int(arrays["cost"][chosen]),
                              "rungs": arrays["choices"][chosen].tolist(),
                              "gain": int(gains[chosen])})
    return {"loss": loss, "max_gain": maximum, "strict_paths": len(ids),
            "max_gain_path": arrays["choices"][index].tolist(),
            "minimum_cost_witnesses": witnesses, **score(loss, maximum)}


def rescore(quality, saved, horizon, impairment, clock):
    selected = saved["rounds"][:horizon]
    gains = []; donor = recipient = 0
    for row in selected:
        t = row["segment"]; a, b = row["decision"]["rungs"]
        gain = max(0, int(quality[t, 0, a]-quality[t, 0, 2]))
        if clock == "deadline" and round(row["play_end"][0]*TICKS) > horizon*SLOT:
            gain = 0
        gains.append(gain)
        donor += int(quality[t, 1, b] < quality[t, 1, 2])
        recipient += int(quality[t, 0, a] < quality[t, 0, 2])
    loss = debt(quality, impairment)
    return {"loss": loss, "gain": sum(gains), "donor_floor_violations": donor,
            "recipient_floor_violations": recipient, **score(loss, sum(gains))}


def validate_saved_clock(record, saved):
    """Audit actual saved waits/starts against exact nominal fluid timestamps."""
    finish = [0, 0]; prior = 0; spent = 0
    for row in saved["rounds"]:
        t = row["segment"]; start = round(row["start"]*TICKS)
        if start < prior:
            raise ValueError("Saved start precedes previous decision boundary")
        sizes = [int(record["costs"][t, r]) for r in row["decision"]["rungs"]]
        if sum(sizes) > CAP:
            raise ValueError("File cap exceeded")
        spent += max(0, sum(sizes)-2*int(record["costs"][t, 2]))
        arrival = [start+d for d in offsets(sizes)]
        finish = [max(f, a)+SLOT for f, a in zip(finish, arrival)]
        prior = max(start+SLOT, max(arrival))
        for actual, expected in zip(row["arrivals"]+list(row["play_end"])+[row["end"]], arrival+finish+[prior]):
            if abs(actual*TICKS-expected) > 1e-5:
                raise ValueError("Saved timestamp differs from exact nominal clock")
    if spent > record["reserve"]:
        raise ValueError("Saved path exceeds fixed reserve")
    return 4
