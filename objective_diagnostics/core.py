"""Exact finite-window feedback and direct fairness controls; development only."""
from collections import deque
import numpy as np
from scipy.optimize import linprog
from horizon_recovery.core import action_table

HORIZON, STRENGTH = 24, 8.
DIRECT = ("nash", "instant_maxmin", "window_maxmin", "window_nash")
CANDIDATES = ("floor_bank", "floor_nobank", "floor_memoryless", "fair_bank", "fair_nobank", "fair_memoryless")
POLICIES = DIRECT + CANDIDATES

def contract(predictions, radius, costs, budget, target_cap):
    """Capped max-min average quality over mixtures of feasible JOINT actions.

    No per-user fractional relaxation is used: every support action fits its
    own period's Nash byte cap. The entitlement is feasible in expectation,
    not an assertion of an integral schedule or realized-quality guarantee.
    """
    if not np.isfinite(target_cap) or not 1 <= target_cap <= 5:
        raise ValueError("target cap must be in [1,5]")
    predictions, costs = np.asarray(predictions), np.asarray(costs)
    if predictions.ndim != 3 or predictions.shape != costs.shape:
        raise ValueError("period x user x action tables required")
    periods, users, _ = predictions.shape
    tables = [action_table(q, radius, c, budget) for q, c in zip(predictions, costs)]
    counts = [len(t["actions"]) for t in tables]
    offsets = np.r_[0, np.cumsum(counts)]
    q = np.concatenate([t["quality"] for t in tables])
    ceiling = np.minimum(target_cap, np.mean([t["quality"].max(axis=0) for t in tables], axis=0))
    eq = np.zeros((periods, len(q) + 1))
    for t in range(periods):
        eq[t, offsets[t]:offsets[t+1]] = 1
    objective = np.zeros(len(q) + 1)
    objective[-1] = -1
    lo, solution, height = 1., None, 1.
    for hi in np.unique(ceiling):
        capped = ceiling <= lo + 1e-9
        constraints = np.column_stack((-q.T / periods, (~capped).astype(float)))
        rhs = np.where(capped, -ceiling, 0.)
        solution = linprog(objective, A_ub=constraints, b_ub=rhs, A_eq=eq,
                           b_eq=np.ones(periods), bounds=[(0, None)] * len(q) + [(lo, float(hi))],
                           method="highs")
        if not solution.success:
            raise RuntimeError(f"contract optimization failed: {solution.message}")
        height = float(solution.x[-1])
        if height < hi - 1e-7:
            break
        lo = float(hi)
    target = np.minimum(ceiling, height)
    expected = solution.x[:-1] @ q / periods
    witness = []
    for t, table in enumerate(tables):
        weights = solution.x[offsets[t]:offsets[t+1]]
        if abs(weights.sum() - 1) > 1e-7:
            raise AssertionError("mixture normalization failed")
        for j in np.flatnonzero(weights > 1e-9):
            witness.append({"period": t, "probability": float(weights[j]),
                            "action": table["actions"][j].tolist(),
                            "quality": table["quality"][j].tolist(),
                            "bytes": float(table["bytes"][j]), "byte_cap": table["nash_bytes"]})
    if np.any(expected < target - 1e-7):
        raise AssertionError("contract witness does not achieve target")
    return {"target": target.tolist(), "ceiling": ceiling.tolist(), "height": height,
            "expected_quality": expected.tolist(), "witness": witness, "columns": len(q)}


def mode_for(policy):
    return policy.rsplit("_",1)[-1] if policy in CANDIDATES else "bank"


class Ledger:
    """H-entry bank/suffix-queue; expire before predicting the next H-entry state."""
    def __init__(self, horizon, users):
        if not isinstance(horizon,int) or horizon < 1 or not isinstance(users,int) or users < 1:
            raise ValueError("positive integral dimensions required")
        self.horizon,self.users = horizon,users
        self.residuals,self.qualities = deque(),deque()
        self.last = np.zeros(users)
        self.ready = False

    def balance(self,mode):
        if mode == "memoryless":
            return self.horizon*np.maximum(self.last,0)
        if mode not in {"bank","nobank"}:
            raise ValueError(mode)
        if not self.residuals:
            return np.zeros(self.users)
        rows = np.asarray(self.residuals)
        if mode == "bank":
            return rows.sum(axis=0)
        return np.maximum(np.cumsum(rows[::-1],axis=0).max(axis=0),0)

    def begin(self,mode):
        if self.ready:
            raise RuntimeError("begin called twice without feedback")
        before = np.maximum(self.balance(mode),0)
        expired = np.zeros(self.users)
        if len(self.residuals) == self.horizon:
            expired = self.residuals.popleft()
            self.qualities.popleft()
        after = np.maximum(self.balance(mode),0)
        self.ready = True
        return expired,after-before

    def update(self,target,quality):
        if not self.ready:
            raise RuntimeError("begin required before feedback")
        target,quality = np.asarray(target,float),np.asarray(quality,float)
        if (target.shape != (self.users,) or quality.shape != target.shape or
            not np.isfinite(target).all() or not np.isfinite(quality).all() or
            np.any((target < 1) | (target > 5)) or np.any((quality < 1) | (quality > 5))):
            raise ValueError("invalid objective feedback")
        self.last = target-quality
        self.residuals.append(self.last.copy())
        self.qualities.append(quality.copy())
        self.ready = False


def select(policy,predicted,radius,costs,budget,target,ledger):
    if policy not in POLICIES or not ledger.ready:
        raise ValueError("known policy and begun round required")
    table = action_table(predicted,radius,costs,budget)
    q,base = table["quality"],table["base"]
    eligible = np.arange(len(q))
    balance = ledger.balance(mode_for(policy))
    terminal = np.maximum(balance+np.asarray(target)-q,0)
    score = base.copy()
    if policy in CANDIDATES:
        score -= STRENGTH*np.sum(terminal**2,axis=1)/(2*ledger.horizon)
    elif policy in {"instant_maxmin","window_maxmin"}:
        if policy == "window_maxmin" and ledger.qualities:
            q = (q+np.asarray(ledger.qualities).sum(axis=0))/(len(ledger.qualities)+1)
        ordered = np.sort(q,axis=1)
        for column in range(q.shape[1]):
            best = ordered[eligible,column].max()
            eligible = eligible[np.abs(ordered[eligible,column]-best) <= 1e-12]
    elif policy == "window_nash":
        past = np.asarray(ledger.qualities).sum(axis=0) if ledger.qualities else np.zeros(len(predicted))
        lower = (past+np.maximum(1,q-radius))/(len(ledger.qualities)+1)
        score = np.log(lower).sum(axis=1)
    eligible = eligible[np.abs(score[eligible]-score[eligible].max()) <= 1e-12]
    j = eligible[np.argmin(table["bytes"][eligible])]
    return table["actions"][j].copy(), {"nash_bytes":table["nash_bytes"],"nash_action":table["nash_action"],
            "candidate_count":len(q),"score":float(score[j]),"predicted_terminal":terminal[j]}


def range_cap(predicted):
    """Largest prefix retaining at most half the quality range above rung zero."""
    q = np.asarray(predicted,float)
    if q.shape != (6,) or not np.isfinite(q).all():
        raise ValueError("six finite sender qualities required")
    limit = q[0]+.5*(q.max()-q[0])
    return int(np.flatnonzero(np.maximum.accumulate(q) <= limit+1e-12)[-1])
