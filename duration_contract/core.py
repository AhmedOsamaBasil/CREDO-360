"""Integer media-duration ledger, exact playback queues and pacing semantics."""
from fractions import Fraction
import numpy as np
from metric_contract.core import TICKS, SLOT, offsets

DEADLINE = 40*TICKS


def ticks(value):
    value = Fraction(value)*TICKS
    if value.denominator != 1 or value < 0:
        raise ValueError("Media timestamp must be nonnegative and exactly representable")
    return int(value)


def packet_timeline(packets, time_base):
    rows = sorted((int(p["pts"]), int(p["duration"])) for p in packets)
    if not rows or any(d <= 0 for p, d in rows):
        raise ValueError("Positive presentation intervals required")
    if any(p+d != q for (p,d),(q,e) in zip(rows,rows[1:])):
        raise ValueError("Noncontiguous or duplicate presentation intervals")
    first = rows[0][0]; tb = Fraction(time_base)
    return {"first_pts": first, "time_base": str(tb),
            "pts_ticks": [ticks((p-first)*tb) for p,d in rows],
            "duration_ticks": [ticks(d*tb) for p,d in rows],
            "total_ticks": ticks((rows[-1][0]+rows[-1][1]-first)*tb)}


def playback(arrivals, durations):
    if len(arrivals) != 4 or len(durations) != 4:
        raise ValueError("Four two-user recovery segments required")
    ends = [0,0]; rows = []; waits = [0,0]
    for delivery, duration in zip(arrivals,durations):
        if len(delivery) != 2 or duration <= 0 or min(delivery) < 0:
            raise ValueError("Invalid release/duration")
        start = [max(ends[u], int(delivery[u])) for u in (0,1)]
        for u in (0,1): waits[u] += start[u]-ends[u]
        ends = [s+duration for s in start]
        rows.append({"start_ticks": start, "end_ticks": list(ends)})
    if any(ends[u] != sum(durations)+waits[u] for u in (0,1)):
        raise ValueError("Playback conservation failure")
    return {"segments": rows, "finish_ticks": ends, "wait_ticks": waits,
            "startup_ticks": list(rows[0]["start_ticks"]),
            "later_wait_ticks": [waits[u]-rows[0]["start_ticks"][u] for u in (0,1)]}


def account(negative_mse, durations, choices, ends, deadline=DEADLINE):
    loss = sum(max(0,int(negative_mse[t,0,2]-negative_mse[t,0,0]))*durations[t] for t in (0,1))
    gains = [max(0,int(negative_mse[t,0,a]-negative_mse[t,0,2]))*durations[t]
             for t,(a,b) in zip(range(2,6),choices)]
    floors = [[int(negative_mse[t,u,r] < negative_mse[t,u,2]) for u,r in enumerate(pair)]
              for t,pair in zip(range(2,6),choices)]
    credit = sum(g for g,e in zip(gains,ends) if e[0] <= deadline)
    eventual = sum(gains)
    def fraction(c): return round(max(0,loss-c)/loss,12) if loss else None
    half = 2*credit >= loss if loss else None
    return {"loss_micro_mse_ticks": loss, "segment_gain_micro_mse_ticks": gains,
            "deadline_credit": min(loss,credit), "eventual_credit": min(loss,eventual),
            "deadline_unpaid": fraction(credit), "eventual_unpaid": fraction(eventual),
            "half_by_deadline": half,
            "protected_half_by_deadline": bool(half and not any(sum(x) for x in floors)) if loss else None,
            "recipient_floor_violations": sum(f[0] for f in floors),
            "donor_floor_violations": sum(f[1] for f in floors)}


def baseline_arrivals(costs):
    start = 0; arrivals = []
    for t in range(2,6):
        a = [start+d for d in offsets((costs[t,2],costs[t,2]))]
        arrivals.append(a); start = max(start+SLOT,max(a))
    return arrivals


def frame_record(line):
    fields = [f.strip() for f in line.split(",")]
    if len(fields) != 6 or fields[0] != "0":
        raise ValueError("Invalid framehash record")
    dts, pts, duration, size = map(int,fields[1:5])
    digest = fields[5]
    if duration <= 0 or size <= 0 or len(digest) != 32 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Invalid frame duration/size/hash")
    return {"pts": pts, "duration": duration, "size": size, "md5": digest}


def pacing_step(previous_end_ns, ready_ns, now_ns):
    """No acceleration: decoding delay and scheduling lateness remain distinct."""
    if min(previous_end_ns, ready_ns, now_ns) < 0:
        raise ValueError("Negative clock")
    target = max(previous_end_ns,ready_ns)
    presented = max(target,now_ns)
    return {"target_ns": target, "present_ns": presented,
            "decoder_wait_ns": max(0,ready_ns-previous_end_ns),
            "pacing_late_ns": presented-target}


def oracle(negative_mse, costs, durations, choices, extra):
    """Fixed-cadence future-known bound; scalar independent check is separate."""
    n = len(choices); finish = np.zeros((n,2),dtype=np.int64); start = np.zeros(n,dtype=np.int64)
    safe = np.ones(n,dtype=bool); gain = np.zeros(n,dtype=np.int64); eventual = gain.copy()
    for j,t in enumerate(range(2,6)):
        a,b = choices[:,j,0],choices[:,j,1]
        sa,sb = costs[t,a],costs[t,b]
        arrival = start[:,None]+19500+np.stack((np.minimum(2*sa,sa+sb),np.minimum(2*sb,sa+sb)),axis=1)
        finish = np.maximum(finish,arrival)+durations[t]
        start = np.maximum(start+SLOT,arrival.max(axis=1))
        qa,qb = negative_mse[t,0,a],negative_mse[t,1,b]
        safe &= (qa>=negative_mse[t,0,2]) & (qb>=negative_mse[t,1,2])
        value = np.maximum(0,qa-negative_mse[t,0,2])*durations[t]
        gain += value*(finish[:,0]<=DEADLINE); eventual += value
    loss = sum(max(0,int(negative_mse[t,0,2]-negative_mse[t,0,0]))*durations[t] for t in (0,1))
    ids = np.flatnonzero(safe)
    if not len(ids) or not loss: raise ValueError("Positive-loss feasible baseline required")
    def select(values):
        best = ids[values[ids]==values[ids].max()]; index = int(best[np.argmin(extra[best])])
        passing = ids[2*values[ids]>=loss]
        witness = int(passing[np.argmin(extra[passing])]) if len(passing) else None
        return {"gain": int(values[index]), "unpaid": round(max(0,loss-int(values[index]))/loss,12),
                "max_path": choices[index].tolist(), "half": bool(len(passing)),
                "half_min_extra_bytes": int(extra[witness]) if witness is not None else None,
                "half_path": choices[witness].tolist() if witness is not None else None}
    return {"loss_micro_mse_ticks": loss, "strict_paths": len(ids),
            "deadline": select(gain), "eventual": select(eventual)}
