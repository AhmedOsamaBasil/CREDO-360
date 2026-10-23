"""Forecast-feasible anti-windup recovery; no test labels in the policy API."""
from __future__ import annotations

import hashlib
import numpy as np
from recovery_pilot.core import all_actions, LADDER

POLICIES = ("bounded_nash", "fixed_debt", "ceiling_debt", "feasible_recovery",
            "memoryless_feasible", "max_min")


def partition(subjects):
    if len(set(subjects)) != 28:
        raise ValueError("protocol requires 28 source IDs")
    ordered = sorted(set(subjects), key=lambda sid: hashlib.sha256(
        f"feasibility-v2-{sid}".encode()).digest())
    return {"calibration": ordered[:9], "test": ordered[9:]}


def quality_radius(predicted, calibration):
    predicted, calibration = np.asarray(predicted), np.asarray(calibration)
    if calibration.shape != (9,) + predicted.shape or not np.all(np.isfinite(calibration)):
        raise ValueError("nine complete finite calibration panels required")
    scores = np.max(np.abs(calibration - predicted[None]), axis=(1, 2))
    return float(np.max(scores)), scores


def feasible_reference(lower, costs, budget):
    """Capped water level with a simultaneous feasible witness, not n optima.

    For a candidate level each user selects its cheapest qualifying action;
    their summed cost is the minimum possible for that threshold vector.
    Feasibility changes only at finite quality values or individual caps.
    """
    lower, costs = np.asarray(lower, float), np.asarray(costs, float)
    if (lower.ndim != 2 or costs.shape != lower.shape
            or not np.isfinite(lower).all() or not np.isfinite(costs).all()
            or np.any((lower < 1) | (lower > 5)) or np.any(costs <= 0)
            or not np.isfinite(budget) or budget <= 0):
        raise ValueError("invalid feasibility table")
    cheapest = costs.min(axis=1)
    if cheapest.sum() > budget + 1e-8:
        raise ValueError("no feasible allocation: explicit admission failure")
    admissible = costs + (cheapest.sum() - cheapest)[:, None] <= budget + 1e-8
    ceiling = np.minimum(4, np.where(admissible, lower, -np.inf).max(axis=1))
    levels = np.unique(np.r_[1.0, ceiling, lower[lower <= 4]])
    floor, witness, height = np.ones(len(lower)), costs.argmin(axis=1), 1.0
    for level in levels:
        threshold = np.minimum(ceiling, level)
        qualifying = lower >= threshold[:, None] - 1e-12
        candidate = np.where(qualifying, costs, np.inf).argmin(axis=1)
        if costs[np.arange(len(lower)), candidate].sum() <= budget + 1e-8:
            floor, witness, height = threshold, candidate, float(level)
    return floor, ceiling, witness, height


def select_action(policy, predicted, radius, costs, budget, debt, last, previous):
    if policy not in POLICIES:
        raise ValueError(policy)
    predicted, costs = np.asarray(predicted, float), np.asarray(costs, float)
    users, levels = predicted.shape
    debt, last, previous = np.asarray(debt), np.asarray(last), np.asarray(previous)
    if (levels != 6 or not np.isfinite(radius) or radius < 0
            or not np.all(np.isfinite(predicted)) or np.any((predicted < 1) | (predicted > 5))
            or debt.shape != (users,) or last.shape != (users,) or previous.shape != (users,)
            or not np.isfinite(debt).all() or not np.isfinite(last).all()
            or np.any(debt < 0) or np.any(last < 0)
            or np.any((previous < 0) | (previous >= levels))):
        raise ValueError("invalid policy inputs")
    lower = np.maximum(1, predicted - radius)
    floor, ceiling, witness, height = feasible_reference(lower, costs, budget)
    actions = all_actions(users, levels)
    total = costs[np.arange(users), actions].sum(axis=1)
    keep = total <= budget + 1e-8
    actions, total = actions[keep], total[keep]
    state = last if policy == "memoryless_feasible" else debt
    weighted = np.log(lower)
    if policy not in {"bounded_nash", "max_min"}:
        weighted = weighted + (state / (1 + state.mean()))[:, None] * lower
    score = weighted[np.arange(users), actions].sum(axis=1)
    score -= .08 * np.abs(np.log((LADDER[actions] + .05) /
                                (LADDER[previous] + .05))).mean(axis=1)
    if policy == "max_min":
        q = lower[np.arange(users), actions]
        best = np.lexsort((np.arange(len(actions)), total, -q.mean(axis=1), -q.min(axis=1)))[0]
    else:
        ties = np.flatnonzero(np.abs(score - score.max()) <= 1e-12)
        best = ties[np.argmin(total[ties])]
    action = actions[best].copy()
    target = (floor if policy in {"feasible_recovery", "memoryless_feasible"}
              else ceiling if policy == "ceiling_debt" else np.full(users, 4.0))
    return action, {"floor": floor, "ceiling": ceiling, "target": target,
                    "witness": witness, "waterlevel": height, "candidate_count": len(actions),
                    "lower": lower[np.arange(users), action],
                    "mean": predicted[np.arange(users), action], "objective": float(score[best])}


def update_debt(debt, target, outcome):
    debt, target, outcome = map(lambda v: np.asarray(v, float), (debt, target, outcome))
    if debt.shape != target.shape or debt.shape != outcome.shape or not np.isfinite(
            np.r_[debt, target, outcome]).all() or np.any(debt < 0):
        raise ValueError("invalid queue update")
    return np.maximum(.9 * debt + target - outcome, 0)
