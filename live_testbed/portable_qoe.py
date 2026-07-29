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


def candidate_allocations(ladder: np.ndarray, users: int, capacity: float) -> np.ndarray:
    feasible = np.asarray(
        [a for a in itertools.product(ladder, repeat=users) if sum(a) <= capacity],
        dtype=float,
    )
    if len(feasible) <= 384:
        return feasible
    indices = np.unique(np.linspace(0, len(feasible) - 1, 384, dtype=int))
    return feasible[indices]


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
    radius: float,
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
    lower = np.clip(mean - radius, 1.0, 5.0)
    switching = np.mean(
        np.abs(np.log((feasible + 0.05) / (previous_rate[None, :] + 0.05))),
        axis=1,
    )
    if controller == "uncertainty_nash":
        score = np.log(np.clip(mean - 1.28 * uncertainty, 1.0, 5.0)).sum(axis=1)
    elif controller == "conformal_nash":
        score = np.log(lower).sum(axis=1)
    elif controller == "risk_debt":
        recoverable = np.maximum(lower - lower[0][None, :], 0)
        normalized_debt = debt / (1.0 + debt.mean())
        score = np.log(lower).sum(axis=1)
        score += debt_weight * (normalized_debt[None, :] * recoverable).sum(axis=1)
    else:
        raise ValueError(f"Unknown controller: {controller}")
    score -= switch_weight * switching
    selected = int(np.argmax(score))
    return feasible[selected], {
        "candidate_count": int(rows),
        "objective": float(score[selected]),
    }
