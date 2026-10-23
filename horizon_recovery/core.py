"""Joint-mixture service contracts and resource-neutral window recovery."""
from __future__ import annotations
from collections import deque
import numpy as np
from scipy.optimize import linprog
from recovery_pilot.core import all_actions

POLICIES = ("nash", "window_recovery", "memoryless_scaled", "memoryless_unscaled", "fixed_window")


def action_table(predicted, radius, costs, budget):
    predicted, costs = np.asarray(predicted, float), np.asarray(costs, float)
    if (predicted.ndim != 2 or predicted.shape != costs.shape or predicted.shape[1] != 6
            or not np.isfinite(predicted).all() or not np.isfinite(costs).all()
            or np.any((predicted < 1) | (predicted > 5)) or np.any(costs <= 0)
            or not np.isfinite(radius) or radius < 0 or not np.isfinite(budget) or budget <= 0):
        raise ValueError("invalid allocation inputs")
    users = len(predicted)
    actions = all_actions(users)
    total = costs[np.arange(users), actions].sum(axis=1)
    keep = total <= budget + 1e-8
    actions, total = actions[keep], total[keep]
    if not len(actions):
        raise ValueError("no feasible joint allocation")
    q = predicted[np.arange(users), actions]
    base = np.log(np.maximum(1, q - radius)).sum(axis=1)
    ties = np.flatnonzero(np.abs(base - base.max()) <= 1e-12)
    nash = ties[np.argmin(total[ties])]
    cap = float(total[nash])
    # The same stateless reference cap applies to every policy at this context.
    keep = total <= cap + 1e-8
    return {"actions": actions[keep], "bytes": total[keep], "quality": q[keep],
            "base": base[keep], "nash_bytes": cap, "nash_action": actions[nash].copy()}


def contract(predictions, radius, costs, budget):
    """Capped max-min average quality over mixtures of feasible JOINT actions.

    No per-user fractional relaxation is used: every support action fits its
    own period's Nash byte cap. The entitlement is feasible in expectation,
    not an assertion of an integral schedule or realized-quality guarantee.
    """
    predictions, costs = np.asarray(predictions), np.asarray(costs)
    if predictions.ndim != 3 or predictions.shape != costs.shape:
        raise ValueError("period x user x action tables required")
    periods, users, _ = predictions.shape
    tables = [action_table(q, radius, c, budget) for q, c in zip(predictions, costs)]
    counts = [len(t["actions"]) for t in tables]
    offsets = np.r_[0, np.cumsum(counts)]
    q = np.concatenate([t["quality"] for t in tables])
    ceiling = np.minimum(4, np.mean([t["quality"].max(axis=0) for t in tables], axis=0))
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


class WindowLedger:
    def __init__(self, horizon, users):
        if not isinstance(horizon, int) or horizon < 1:
            raise ValueError("positive integral horizon required")
        self.horizon, self.users = horizon, users
        self.rows = deque()

    def state(self, policy):
        if not self.rows:
            return np.zeros(self.users)
        if policy == "memoryless_scaled":
            return self.horizon * np.maximum(self.rows[-1], 0)
        if policy == "memoryless_unscaled":
            return np.maximum(self.rows[-1], 0)
        return np.maximum(np.sum(self.rows, axis=0), 0)

    def update(self, target, outcome):
        residual = np.asarray(target, float) - np.asarray(outcome, float)
        if residual.shape != (self.users,) or not np.isfinite(residual).all():
            raise ValueError("invalid feedback")
        expired = self.rows.popleft() if len(self.rows) == self.horizon else np.zeros(self.users)
        self.rows.append(residual.copy())
        return expired


def select_action(policy, predicted, radius, costs, budget, state, target, horizon, strength):
    if policy not in POLICIES:
        raise ValueError(policy)
    state, target = np.asarray(state), np.asarray(target)
    if (state.shape != (len(predicted),) or target.shape != state.shape or np.any(state < 0)
            or not np.isfinite(state).all() or not np.isfinite(target).all()
            or horizon < 1 or not np.isfinite(strength) or strength < 0):
        raise ValueError("invalid recovery state")
    table = action_table(predicted, radius, costs, budget)
    # Terminal positive deficit is a prediction, NOT a calibrated gain bound.
    terminal = np.maximum(state + target - table["quality"], 0)
    score = table["base"].copy()
    if policy != "nash":
        score -= strength * np.sum(terminal**2, axis=1) / (2 * horizon)
    ties = np.flatnonzero(np.abs(score - score.max()) <= 1e-12)
    selected = ties[np.argmin(table["bytes"][ties])]
    return table["actions"][selected].copy(), {"nash_bytes": table["nash_bytes"],
            "candidate_count": len(score), "objective": float(score[selected]),
            "terminal_deficit": terminal[selected], "nash_action": table["nash_action"]}
