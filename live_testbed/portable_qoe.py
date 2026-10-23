"""Portable NumPy inference and CREDO-360 controller utilities."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

REPRESENTATION_INDEX = np.array([1, 2, 6, 8, 12, 20], dtype=float)


class PortableEnsemble:
    def __init__(self, path: Path):
        self.payload = json.loads(path.read_text(encoding="utf-8"))
        if self.payload["format"] != "credo360-portable-ensemble-v1":
            raise ValueError("Unsupported portable model format")
        self.mean = np.asarray(self.payload["scaler_mean"], dtype=float)
        self.scale = np.asarray(self.payload["scaler_scale"], dtype=float)
        self.members = [
            (
                [np.asarray(x, dtype=float) for x in member["weights"]],
                [np.asarray(x, dtype=float) for x in member["biases"]],
            )
            for member in self.payload["members"]
        ]

    @staticmethod
    def _silu(x: np.ndarray) -> np.ndarray:
        return x / (1.0 + np.exp(-np.clip(x, -40, 40)))

    def predict(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        z = (np.asarray(x, dtype=float) - self.mean) / self.scale
        member_means, member_vars = [], []
        for weights, biases in self.members:
            hidden = self._silu(z @ weights[0].T + biases[0])
            hidden = self._silu(hidden @ weights[1].T + biases[1])
            output = hidden @ weights[2].T + biases[2]
            mean = 1.0 + 4.0 / (1.0 + np.exp(-np.clip(output[:, 0], -40, 40)))
            member_means.append(mean)
            member_vars.append(np.exp(np.clip(output[:, 1], -5, 2)))
        stacked = np.stack(member_means)
        predictive_mean = stacked.mean(axis=0)
        variance = stacked.var(axis=0) + np.stack(member_vars).mean(axis=0)
        return predictive_mean, np.sqrt(variance)

    def verify_export(self) -> float:
        check = self.payload["self_check"]
        predicted, _ = self.predict(np.asarray(check["features"], dtype=float))
        maximum_error = float(np.max(np.abs(predicted - np.asarray(check["mean"]))))
        if maximum_error > float(check["max_tolerance"]):
            raise RuntimeError(f"Portable inference mismatch: {maximum_error:g}")
        return maximum_error


def conformal_radius(residuals: list[float], alpha: float) -> float:
    values = np.sort(np.asarray(residuals, dtype=float))
    rank = int(np.ceil((len(values) + 1) * (1 - alpha))) - 1
    return float(values[np.clip(rank, 0, len(values) - 1)])


def build_features(
    template: np.ndarray,
    rate_mbps: np.ndarray,
    throughput_mbps: np.ndarray,
    buffer_s: np.ndarray,
    previous_rate: np.ndarray,
    latency_s: np.ndarray,
) -> np.ndarray:
    count = len(rate_mbps)
    templates = np.tile(np.asarray(template, dtype=float), (count, 1))
    ladder = np.array([0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491])
    rate_index = REPRESENTATION_INDEX[
        np.abs(rate_mbps[:, None] - ladder[None, :]).argmin(axis=1)
    ]
    previous_index = REPRESENTATION_INDEX[
        np.abs(previous_rate[:, None] - ladder[None, :]).argmin(axis=1)
    ]
    download_s = 10.0 * rate_mbps / np.maximum(throughput_mbps, 0.02)
    overload = np.maximum(rate_mbps - throughput_mbps, 0) / np.maximum(
        throughput_mbps, 0.02
    )
    templates[:, 0] = np.clip(buffer_s, 0, 30)
    templates[:, 1] = rate_mbps * 1000
    templates[:, 2] = rate_index
    templates[:, 3] = previous_index
    templates[:, 4] = 20
    templates[:, 5] = np.clip(60 * overload, 0, 250)
    templates[:, 6] = np.clip(0.5 * latency_s, 0, 1)
    templates[:, 7] = np.clip(latency_s, 0, 2)
    templates[:, 8] = np.clip(2.0 * latency_s, 0, 4)
    templates[:, 9] = np.clip(0.8 * download_s, 0, 20)
    templates[:, 10] = np.clip(download_s, 0, 20)
    templates[:, 11] = np.clip(1.2 * download_s, 0, 20)
    templates[:, 12] = rate_mbps * 1e6
    return templates


def _first_primes(count: int) -> list[int]:
    """Return enough small primes to construct a deterministic Halton cover."""
    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        if all(candidate % prime for prime in primes if prime * prime <= candidate):
            primes.append(candidate)
        candidate += 1
    return primes


def _radical_inverse(index: int, base: int) -> float:
    value = 0.0
    factor = 1.0 / base
    while index:
        index, digit = divmod(index, base)
        value += digit * factor
        factor /= base
    return value


def _repair_to_capacity(
    indices: np.ndarray,
    ladder: np.ndarray,
    capacity: float,
) -> np.ndarray:
    """Project ladder indices to feasibility with deterministic round-robin cuts."""
    repaired = indices.copy()
    cursor = 0
    while ladder[repaired].sum() > capacity + 1e-9 and repaired.max() > 0:
        reducible = np.flatnonzero(repaired > 0)
        user = reducible[cursor % len(reducible)]
        repaired[user] -= 1
        cursor += 1
    return repaired


def candidate_allocations(
    ladder: np.ndarray,
    users: int,
    capacity: float,
    max_candidates: int = 384,
) -> np.ndarray:
    """Build a deterministic feasible action cover without exponential materialization.

    Exact enumeration is retained for small systems. Above that threshold, a
    low-discrepancy Halton cover is combined with minimum, uniform, and
    single-user extreme actions, then projected to the discrete capacity set.
    This makes the journal scalability experiment executable at 10--30 users
    while preserving deterministic paired comparisons.
    """
    ladder = np.asarray(ladder, dtype=float)
    minimum = float(ladder[0]) * users
    if minimum > capacity + 1e-9:
        raise ValueError("Capacity is below the minimum feasible allocation")
    total = len(ladder) ** users
    if total <= 250_000:
        feasible = np.asarray(
            [
                action
                for action in itertools.product(ladder, repeat=users)
                if sum(action) <= capacity + 1e-9
            ],
            dtype=float,
        )
        if len(feasible) <= max_candidates:
            return feasible
        selected = np.unique(
            np.linspace(0, len(feasible) - 1, max_candidates, dtype=int)
        )
        return feasible[selected]

    index_rows: list[np.ndarray] = [np.zeros(users, dtype=int)]
    for level in range(1, len(ladder)):
        uniform = np.full(users, level, dtype=int)
        index_rows.append(_repair_to_capacity(uniform, ladder, capacity))
    for user in range(users):
        extreme = np.zeros(users, dtype=int)
        extreme[user] = len(ladder) - 1
        index_rows.append(_repair_to_capacity(extreme, ladder, capacity))

    primes = _first_primes(users)
    sample_index = 1
    while len(index_rows) < max_candidates * 2:
        row = np.asarray(
            [
                min(
                    int(_radical_inverse(sample_index, base) * len(ladder)),
                    len(ladder) - 1,
                )
                for base in primes
            ],
            dtype=int,
        )
        index_rows.append(_repair_to_capacity(row, ladder, capacity))
        sample_index += 1

    unique = np.unique(np.stack(index_rows), axis=0)
    if len(unique) > max_candidates:
        selected = np.unique(
            np.linspace(0, len(unique) - 1, max_candidates, dtype=int)
        )
        unique = unique[selected]
    return ladder[unique]


def select_action(
    controller: str,
    model: PortableEnsemble,
    template: np.ndarray,
    ladder: np.ndarray,
    capacity_mbps: float,
    throughput_mbps: np.ndarray,
    buffer_s: np.ndarray,
    previous_rate: np.ndarray,
    latency_s: np.ndarray,
    debt: np.ndarray,
    radius: float | np.ndarray,
    debt_weight: float = 1.0,
    switch_weight: float = 0.08,
) -> tuple[np.ndarray, dict]:
    users = len(buffer_s)
    feasible = candidate_allocations(ladder, users, capacity_mbps)
    rows = len(feasible)
    features = build_features(
        template,
        feasible.reshape(-1),
        np.tile(throughput_mbps, rows),
        np.tile(buffer_s, rows),
        np.tile(previous_rate, rows),
        np.tile(latency_s, rows),
    )
    mean, uncertainty = model.predict(features)
    mean, uncertainty = mean.reshape(rows, users), uncertainty.reshape(rows, users)
    radius_array = np.asarray(radius, dtype=float)
    if radius_array.ndim > 1 or (
        radius_array.ndim == 1 and len(radius_array) != users
    ):
        raise ValueError("radius must be scalar or one value per user")
    lower = np.clip(mean - radius_array, 1.0, 5.0)
    reference = lower[0]
    # Historical score, not a calibrated improvement bound. For lower>=reference
    # this is only an action-independent shift of absolute quality-debt reward.
    # The objective-target/direct-gain pilot is implemented in recovery_pilot/.
    recoverable = np.maximum(lower - reference[None, :], 0)
    normalized_debt = debt / (1.0 + debt.mean())
    switching = np.mean(
        np.abs(np.log((feasible + 0.05) / (previous_rate[None, :] + 0.05))),
        axis=1,
    )
    debt_term = np.zeros(rows, dtype=float)
    if controller == "mean_greedy":
        score = mean.sum(axis=1)
    elif controller in {"proportional_fair", "mean_nash"}:
        score = np.log(np.clip(mean, 1.0, 5.0)).sum(axis=1)
    elif controller in {"uncertainty_nash", "fair_edge_nsw_proxy"}:
        # Executable objective-aligned proxy for uncertainty-aware Nash edge
        # coordination. It is not a reproduction of a trained MARL/GNN policy.
        score = np.log(np.clip(mean - 1.28 * uncertainty, 1.0, 5.0)).sum(axis=1)
    elif controller in {"conformal_nash", "aci_nash"}:
        score = np.log(lower).sum(axis=1)
    elif controller == "mean_debt_ungated":
        mean_floor = np.clip(mean, 1.0, 5.0)
        debt_term = debt_weight * (
            normalized_debt[None, :] * mean_floor
        ).sum(axis=1)
        score = np.log(mean_floor).sum(axis=1) + debt_term
    elif controller == "mean_debt_gated":
        mean_floor = np.clip(mean, 1.0, 5.0)
        mean_reference = mean_floor[0]
        mean_recoverable = np.maximum(
            mean_floor - mean_reference[None, :], 0
        )
        debt_term = debt_weight * (
            normalized_debt[None, :] * mean_recoverable
        ).sum(axis=1)
        score = np.log(mean_floor).sum(axis=1) + debt_term
    elif controller == "conformal_debt_ungated":
        # Conventional QoE-debt weighting: a deprived user's absolute
        # calibrated floor is rewarded without asking whether the candidate
        # improves that user relative to minimum service.
        debt_term = debt_weight * (normalized_debt[None, :] * lower).sum(axis=1)
        score = np.log(lower).sum(axis=1) + debt_term
    elif controller == "resource_debt_ungated":
        # Resource-obligation comparator for the journal gate experiment.
        # Debt directly rewards allocated representation rate, irrespective
        # of whether that rate has calibrated QoE opportunity for the user.
        normalized_rate = feasible / float(ladder[-1])
        debt_term = debt_weight * (
            normalized_debt[None, :] * normalized_rate
        ).sum(axis=1)
        score = np.log(lower).sum(axis=1) + debt_term
    elif controller == "risk_debt":
        debt_term = debt_weight * (
            normalized_debt[None, :] * recoverable
        ).sum(axis=1)
        score = np.log(lower).sum(axis=1) + debt_term
    else:
        raise ValueError(f"Unknown controller: {controller}")
    score -= switch_weight * switching
    selected = int(np.argmax(score))
    return feasible[selected], {
        "candidate_count": int(rows),
        "objective": float(score[selected]),
        "debt_term": float(debt_term[selected]),
        "switching_term": float(switch_weight * switching[selected]),
        "selected_mean": mean[selected].tolist(),
        "selected_uncertainty": uncertainty[selected].tolist(),
        "selected_lower": lower[selected].tolist(),
        "selected_opportunity": recoverable[selected].tolist(),
        "capacity_slack_mbps": float(capacity_mbps - feasible[selected].sum()),
    }
