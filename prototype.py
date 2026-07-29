"""Proof of concept for risk-limiting temporal QoE fairness.

The experiment is intentionally self-contained and uses only NumPy. It is a
research seed: synthetic outcomes must not be reported as empirical evidence.
"""

from __future__ import annotations

import csv
import itertools
from dataclasses import dataclass
from pathlib import Path

import numpy as np


SEED = 20260728
BITRATES = np.array([0.45, 0.8, 1.4, 2.4, 3.8], dtype=float)
N_USERS = 6
N_STEPS = 260
TARGET_QOE = 3.55


def true_qoe(
    rate: np.ndarray,
    throughput: np.ndarray,
    complexity: np.ndarray,
    device: np.ndarray,
    previous_rate: np.ndarray,
) -> np.ndarray:
    """Latent QoE used only by the simulator to generate observations."""
    effective_rate = rate * device / complexity
    visual = 1.0 + 4.0 * (1.0 - np.exp(-effective_rate / 1.35))
    overload = np.maximum(rate - 0.90 * throughput, 0.0)
    stall = 2.9 * overload / np.maximum(throughput, 0.15)
    switching = 0.28 * np.abs(np.log((rate + 0.05) / (previous_rate + 0.05)))
    return np.clip(visual - stall - switching, 1.0, 5.0)


def features(
    rate: np.ndarray,
    throughput: np.ndarray,
    complexity: np.ndarray,
    device: np.ndarray,
    previous_rate: np.ndarray,
) -> np.ndarray:
    """Features available to the learned QoE surrogate."""
    ratio = rate / np.maximum(throughput, 0.15)
    switch = np.abs(np.log((rate + 0.05) / (previous_rate + 0.05)))
    return np.column_stack(
        [
            np.ones_like(rate),
            rate,
            throughput,
            ratio,
            ratio**2,
            complexity,
            device,
            switch,
            rate / complexity,
        ]
    )


@dataclass
class RidgeQoE:
    weights: np.ndarray

    @classmethod
    def fit(cls, x: np.ndarray, y: np.ndarray, ridge: float = 0.08) -> "RidgeQoE":
        penalty = np.eye(x.shape[1]) * ridge
        penalty[0, 0] = 0.0
        return cls(np.linalg.solve(x.T @ x + penalty, x.T @ y))

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.clip(x @ self.weights, 1.0, 5.0)


def regime(complexity: np.ndarray, device: np.ndarray) -> np.ndarray:
    """Four operational regimes; these are not demographic groups."""
    return (complexity > 1.05).astype(int) * 2 + (device < 0.92).astype(int)


def conformal_quantile(values: np.ndarray, alpha: float = 0.10) -> float:
    if len(values) == 0:
        return 0.45
    rank = min(int(np.ceil((len(values) + 1) * (1.0 - alpha))) - 1, len(values) - 1)
    return float(np.sort(values)[max(rank, 0)])


class OnlineCalibrator:
    def __init__(self, residuals: dict[int, list[float]], window: int = 140):
        self.residuals = {key: list(value) for key, value in residuals.items()}
        self.window = window

    def radius(self, groups: np.ndarray) -> np.ndarray:
        return np.array(
            [conformal_quantile(np.asarray(self.residuals.get(int(g), []))) for g in groups]
        )

    def update(self, groups: np.ndarray, errors: np.ndarray) -> None:
        for group, error in zip(groups, errors):
            bucket = self.residuals.setdefault(int(group), [])
            bucket.append(float(abs(error)))
            del bucket[:-self.window]


def make_training_data(rng: np.random.Generator, n: int = 2400):
    throughput = rng.uniform(2.2, 7.5, n)
    complexity = rng.uniform(0.78, 1.18, n)
    device = rng.choice([0.82, 1.0], n, p=[0.35, 0.65])
    rate = rng.choice(BITRATES, n)
    previous = rng.choice(BITRATES, n)
    y = true_qoe(rate, throughput, complexity, device, previous)
    y += rng.normal(0.0, 0.12, n)
    return features(rate, throughput, complexity, device, previous), np.clip(y, 1, 5), (
        rate,
        throughput,
        complexity,
        device,
        previous,
    )


def feasible_allocations(total_capacity: float) -> np.ndarray:
    combos = np.asarray(list(itertools.product(BITRATES, repeat=N_USERS)), dtype=float)
    feasible = combos[combos.sum(axis=1) <= total_capacity]
    if len(feasible) == 0:
        return np.tile(BITRATES[0], (1, N_USERS))
    return feasible


def choose_allocation(
    controller: str,
    model: RidgeQoE,
    calibrator: OnlineCalibrator,
    throughput: np.ndarray,
    complexity: np.ndarray,
    device: np.ndarray,
    previous: np.ndarray,
    debt: np.ndarray,
    total_capacity: float,
) -> np.ndarray:
    allocations = feasible_allocations(total_capacity)
    n_allocations = len(allocations)
    groups = regime(complexity, device)
    radii = calibrator.radius(groups)
    prediction = model.predict(
        features(
            allocations.reshape(-1),
            np.tile(throughput, n_allocations),
            np.tile(complexity, n_allocations),
            np.tile(device, n_allocations),
            np.tile(previous, n_allocations),
        )
    ).reshape(n_allocations, N_USERS)
    switch_cost = np.mean(
        np.abs(np.log((allocations + 0.05) / (previous[None, :] + 0.05))),
        axis=1,
    )
    if controller == "mean_greedy":
        scores = prediction.sum(axis=1) - 0.08 * switch_cost
    elif controller == "alpha_fair":
        scores = np.log(np.maximum(prediction, 1.0)).sum(axis=1)
        scores -= 0.08 * switch_cost
    elif controller == "risk_debt":
        lower = np.clip(prediction - radii[None, :], 1.0, 5.0)
        scores = ((1.0 + 0.62 * debt[None, :]) * np.log(lower)).sum(axis=1)
        scores -= 0.10 * switch_cost
    else:
        raise ValueError(controller)
    return allocations[int(np.argmax(scores))]


def jain(values: np.ndarray) -> float:
    denominator = len(values) * np.square(values).sum()
    return float(values.sum() ** 2 / denominator) if denominator else 1.0


def run_controller(name: str, model: RidgeQoE, seed: int):
    rng = np.random.default_rng(seed)
    device = np.array([0.82, 0.82, 1.0, 1.0, 1.0, 1.0])
    complexity = rng.uniform(0.82, 1.12, N_USERS)
    throughput = rng.uniform(2.4, 6.4, N_USERS)
    previous = np.full(N_USERS, BITRATES[1])
    debt = np.zeros(N_USERS)

    # Independent initial calibration stream.
    x_cal, y_cal, raw_cal = make_training_data(rng, 720)
    pred_cal = model.predict(x_cal)
    groups_cal = regime(raw_cal[2], raw_cal[3])
    residuals = {
        group: list(np.abs(y_cal[groups_cal == group] - pred_cal[groups_cal == group]))
        for group in range(4)
    }
    calibrator = OnlineCalibrator(residuals)
    records = []

    for step in range(N_STEPS):
        # Autocorrelated user access links.
        baseline = 3.7 + 1.45 * np.sin(step / 22 + np.arange(N_USERS))
        throughput = 0.72 * throughput + 0.28 * baseline + rng.normal(0, 0.30, N_USERS)
        throughput = np.clip(throughput, 0.65, 7.5)

        # Distribution shift: harder content and a shared capacity squeeze.
        shifted = step >= N_STEPS // 2
        if shifted:
            complexity = np.clip(
                0.94 * complexity + 0.06 * rng.uniform(1.15, 1.48, N_USERS),
                0.8,
                1.5,
            )
            shared_capacity = 8.4 + 1.0 * np.sin(step / 15)
        else:
            complexity = np.clip(
                0.96 * complexity + 0.04 * rng.uniform(0.80, 1.14, N_USERS),
                0.75,
                1.25,
            )
            shared_capacity = 11.4 + 1.2 * np.sin(step / 15)

        allocation = choose_allocation(
            name,
            model,
            calibrator,
            throughput,
            complexity,
            device,
            previous,
            debt,
            shared_capacity,
        )
        observed = true_qoe(allocation, throughput, complexity, device, previous)
        observed += rng.normal(0, 0.08, N_USERS)
        observed = np.clip(observed, 1, 5)
        prediction = model.predict(
            features(allocation, throughput, complexity, device, previous)
        )
        groups = regime(complexity, device)
        lower = np.clip(prediction - calibrator.radius(groups), 1, 5)
        covered = observed >= lower
        calibrator.update(groups, observed - prediction)

        debt = np.maximum(0.0, 0.94 * debt + TARGET_QOE - observed)
        for user in range(N_USERS):
            records.append(
                {
                    "controller": name,
                    "step": step,
                    "shifted": int(shifted),
                    "user": user,
                    "device_tier": "constrained" if device[user] < 0.92 else "standard",
                    "throughput_mbps": throughput[user],
                    "content_complexity": complexity[user],
                    "allocated_mbps": allocation[user],
                    "predicted_qoe": prediction[user],
                    "lower_qoe": lower[user],
                    "observed_qoe": observed[user],
                    "covered": int(covered[user]),
                    "fairness_debt": debt[user],
                }
            )
        previous = allocation
    return records


def summarise(rows: list[dict]) -> dict[str, float]:
    qoe = np.array([row["observed_qoe"] for row in rows])
    covered = np.array([row["covered"] for row in rows])
    debt = np.array([row["fairness_debt"] for row in rows])
    user_means = np.array(
        [
            np.mean([row["observed_qoe"] for row in rows if row["user"] == user])
            for user in range(N_USERS)
        ]
    )
    temporal_low = []
    for user in range(N_USERS):
        series = np.array(
            [row["observed_qoe"] for row in rows if row["user"] == user]
        )
        temporal_low.append(np.quantile(series, 0.10))
    return {
        "mean_qoe": float(qoe.mean()),
        "worst_user_mean": float(user_means.min()),
        "jain_user_mean": jain(user_means),
        "mean_user_p10": float(np.mean(temporal_low)),
        "lower_bound_coverage": float(covered.mean()),
        "terminal_mean_debt": float(
            np.mean([row["fairness_debt"] for row in rows[-N_USERS:]])
        ),
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    x_train, y_train, _ = make_training_data(rng)
    model = RidgeQoE.fit(x_train, y_train)

    all_rows = []
    summaries = {}
    # Common random numbers make controller comparisons paired and reproducible.
    for controller in ["mean_greedy", "alpha_fair", "risk_debt"]:
        rows = run_controller(controller, model, SEED + 100)
        all_rows.extend(rows)
        summaries[controller] = summarise(rows)

    output = Path(__file__).with_name("results.csv")
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)

    metrics = list(next(iter(summaries.values())))
    print("Synthetic feasibility experiment (not paper evidence)")
    print("-" * 86)
    print(f"{'controller':<14}" + "".join(f"{metric:>18}" for metric in metrics))
    for controller, values in summaries.items():
        print(
            f"{controller:<14}"
            + "".join(f"{values[metric]:>18.4f}" for metric in metrics)
        )
    print(f"\nDetailed results: {output}")


if __name__ == "__main__":
    main()
