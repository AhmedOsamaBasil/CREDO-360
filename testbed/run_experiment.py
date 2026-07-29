"""Run the GPU-backed predictor and multi-user controller benchmark."""

from __future__ import annotations

import argparse
import copy
import csv
import itertools
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.model_selection import GroupShuffleSplit

from calibration import AdaptiveConformal
from model import train_ensemble

FEATURE_NAMES = [
    "BufferLength",
    "BitrateDownloading",
    "IndexDownloading",
    "CurrentIndex",
    "MaxIndex",
    "DropedFrames",
    "MinimumLatency",
    "AverageLatency",
    "MaxLatency",
    "MinimumDownload",
    "AverageDownload",
    "MaxDownload",
    "Resolution",
]


def load_dataset(path: Path):
    frame = pd.read_csv(path)
    x = frame[FEATURE_NAMES].to_numpy(float)
    y = frame["mos_mean"].to_numpy(float)
    y_var = np.square(frame["mos_std"].to_numpy(float))
    groups = frame["stimulus_group"].to_numpy(int)
    return x, y, y_var, groups


def split_dataset(x, y, y_var, groups, seed):
    outer = GroupShuffleSplit(n_splits=1, test_size=0.22, random_state=seed)
    train_cal, test = next(outer.split(x, y, groups))
    inner = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed + 1)
    train_rel, cal_rel = next(
        inner.split(x[train_cal], y[train_cal], groups[train_cal])
    )
    return train_cal[train_rel], train_cal[cal_rel], test


def regime_from_features(x: np.ndarray) -> np.ndarray:
    # Operational regimes based on observed source-order feature ranges.
    bitrate_high = x[:, 12] > 503_270
    impairment_high = (x[:, 5] > 0) | (x[:, 8] > np.median(x[:, 8]))
    return bitrate_high.astype(int) * 2 + impairment_high.astype(int)


def load_traces(trace_dir: Path) -> list[np.ndarray]:
    traces = []
    for path in sorted(trace_dir.glob("*.csv")):
        values = pd.read_csv(path)["observed_traffic_mbps"].to_numpy(float)
        active = values[values > 0]
        if len(active) >= 10:
            # A floor avoids treating capture silence as measured zero capacity.
            floor = max(float(np.quantile(active, 0.05)), 0.20)
            traces.append(np.maximum(values, floor))
    if not traces:
        raise RuntimeError(f"No prepared traces found in {trace_dir}")
    return traces


def build_features(
    template: np.ndarray,
    rate_mbps: np.ndarray,
    throughput: np.ndarray,
    buffer_s: np.ndarray,
    previous_rate: np.ndarray,
    latency_s: np.ndarray,
) -> np.ndarray:
    template = np.asarray(template, dtype=float)
    if template.ndim == 1:
        x = np.repeat(template[None, :], len(rate_mbps), axis=0)
    elif len(template) == len(rate_mbps):
        x = template.copy()
    elif len(rate_mbps) % len(template) == 0:
        x = np.tile(template, (len(rate_mbps) // len(template), 1))
    else:
        raise ValueError("Template rows do not align with user/action rows")
    representation = np.array([1, 2, 6, 8, 12, 20], dtype=float)
    ladder = np.array(
        [0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491]
    )
    rate_index = representation[
        np.abs(rate_mbps[:, None] - ladder[None, :]).argmin(axis=1)
    ]
    previous_index = representation[
        np.abs(previous_rate[:, None] - ladder[None, :]).argmin(axis=1)
    ]
    download_s = 2.0 * rate_mbps / np.maximum(throughput, 0.05)
    overload = np.maximum(rate_mbps - throughput, 0) / np.maximum(
        throughput, 0.05
    )
    x[:, 0] = np.clip(buffer_s, 0, 30)
    x[:, 1] = rate_mbps * 1000
    x[:, 2] = rate_index
    x[:, 3] = previous_index
    x[:, 4] = 20
    x[:, 5] = np.clip(60 * overload, 0, 250)
    x[:, 6] = np.clip(0.5 * latency_s, 0, 1)
    x[:, 7] = np.clip(latency_s, 0, 2)
    x[:, 8] = np.clip(2.0 * latency_s, 0, 4)
    x[:, 9] = np.clip(0.8 * download_s, 0, 20)
    x[:, 10] = np.clip(download_s, 0, 20)
    x[:, 11] = np.clip(1.2 * download_s, 0, 20)
    x[:, 12] = rate_mbps * 1e6
    return x


def all_allocations(ladder: np.ndarray, users: int) -> np.ndarray:
    return np.asarray(list(itertools.product(ladder, repeat=users)), dtype=float)


def select_action(
    controller,
    model,
    calibrator,
    allocations,
    capacity,
    template,
    throughput,
    buffer_s,
    previous,
    latency_s,
    debt,
    device_group,
    switch_weight,
    debt_weight,
):
    feasible = allocations[allocations.sum(axis=1) <= capacity + 1e-9]
    if len(feasible) == 0:
        feasible = allocations[:1]
    # Deterministic coverage of the feasible joint-action space. This reduces
    # each decision to one large GPU batch while retaining extreme actions.
    if len(feasible) > 384:
        indices = np.unique(
            np.linspace(0, len(feasible) - 1, num=384, dtype=int)
        )
        feasible = feasible[indices]
    count, users = feasible.shape
    feature_rows = build_features(
        template,
        feasible.reshape(-1),
        np.tile(throughput, count),
        np.tile(buffer_s, count),
        np.tile(previous, count),
        np.tile(latency_s, count),
    )
    mean, uncertainty = model.predict(feature_rows)
    mean = mean.reshape(count, users)
    uncertainty = uncertainty.reshape(count, users)
    groups = np.tile(device_group, count)
    radius = calibrator.radius(groups).reshape(count, users)
    lower = np.clip(mean - radius, 1.0, 5.0)
    switching = np.mean(
        np.abs(np.log((feasible + 0.05) / (previous[None, :] + 0.05))), axis=1
    )
    if controller == "mean_greedy":
        score = mean.sum(axis=1)
    elif controller == "proportional_fair":
        score = np.log(mean).sum(axis=1)
    elif controller == "uncertainty_nash":
        heuristic_lower = np.clip(mean - 1.28 * uncertainty, 1.0, 5.0)
        score = np.log(heuristic_lower).sum(axis=1)
    elif controller == "conformal_nash":
        score = np.log(lower).sum(axis=1)
    elif controller in {"risk_debt", "risk_debt_static"}:
        # Debt is spent only where the model predicts a recoverable calibrated
        # QoE gain over the minimum feasible allocation. This avoids assigning
        # scarce bitrate to a user whose current impairment is not actionable.
        reference = lower[0]
        recoverable_gain = np.maximum(lower - reference[None, :], 0)
        normalized_debt = debt / (1.0 + debt.mean())
        score = np.log(lower).sum(axis=1)
        score += debt_weight * (
            normalized_debt[None, :] * recoverable_gain
        ).sum(axis=1)
    else:
        raise ValueError(controller)
    score -= switch_weight * switching
    return feasible[int(np.argmax(score))]


def observed_qoe(
    model,
    template,
    allocation,
    throughput,
    buffer_s,
    previous,
    latency_s,
    user_bias,
    device_group,
    shifted,
    rng,
):
    x = build_features(
        template,
        allocation,
        throughput,
        buffer_s,
        previous,
        latency_s,
    )
    overload = np.maximum(allocation - throughput, 0) / np.maximum(throughput, 0.1)
    switch = np.abs(np.log((allocation + 0.05) / (previous + 0.05)))
    viewport_miss = rng.beta(2.0, 12.0, len(allocation))
    if shifted:
        viewport_miss += 0.11 + 0.06 * device_group
    quality = np.log(allocation / 0.045373 + 1.0) / np.log(
        3.792491 / 0.045373 + 1.0
    )
    buffer_risk = np.maximum(2.0 - buffer_s, 0) / 2.0
    # Transparent replay oracle: learned predictions drive decisions, while
    # outcomes follow declared media/network factors rather than model output.
    outcome = 1.0 + 3.5 * quality + user_bias
    outcome -= (
        2.2 * overload
        + 0.22 * switch
        + 1.1 * viewport_miss
        + 0.7 * buffer_risk
        + 0.5 * latency_s
    )
    outcome += rng.normal(0, 0.10 + 0.06 * device_group, len(allocation))
    return np.clip(outcome, 1.0, 5.0), x


def run_episode(
    controller,
    model,
    base_calibrator,
    traces,
    x_templates,
    config,
    seed,
):
    rng = np.random.default_rng(seed)
    users = config["users"]
    steps = config["steps"]
    ladder = np.asarray(config["bitrate_ladder_mbps"], dtype=float)
    allocations = all_allocations(ladder, users)
    calibrator = copy.deepcopy(base_calibrator)
    if controller == "risk_debt_static":
        calibrator.adaptive = False
    chosen_traces = [traces[int(i)] for i in rng.integers(0, len(traces), users)]
    offsets = rng.integers(0, 200, users)
    templates = x_templates[rng.integers(0, len(x_templates), users)]
    device_group = np.array([0, 0, 0, 1, 1])[:users]
    rng.shuffle(device_group)
    user_bias = rng.normal(0, 0.12, users) - 0.10 * device_group
    buffer_s = np.full(users, 4.0)
    previous = np.full(users, ladder[1])
    debt = np.zeros(users)
    records = []

    for step in range(steps):
        shifted = step >= steps // 2
        throughput = np.array(
            [
                trace[(step + offset) % len(trace)]
                for trace, offset in zip(chosen_traces, offsets)
            ]
        )
        # Convert measured traffic replay into heterogeneous access-link service.
        throughput = np.clip(0.35 + 2.6 * throughput, 0.25, 8.0)
        if shifted:
            throughput *= np.where(device_group == 1, 0.62, 0.82)
        latency_s = 0.04 + 0.18 / np.maximum(throughput, 0.2)
        shared_capacity = max(
            ladder[0] * users,
            float(np.quantile(throughput, 0.65) * users * (0.62 if shifted else 0.78)),
        )
        action = select_action(
            controller,
            model,
            calibrator,
            allocations,
            shared_capacity,
            templates,
            throughput,
            buffer_s,
            previous,
            latency_s,
            debt,
            device_group,
            config["switch_weight"],
            config["debt_weight"],
        )
        outcome, feature_rows = observed_qoe(
            model,
            templates,
            action,
            throughput,
            buffer_s,
            previous,
            latency_s,
            user_bias,
            device_group,
            shifted,
            rng,
        )
        prediction, _ = model.predict(feature_rows)
        radius = calibrator.radius(device_group)
        lower = np.clip(prediction - radius, 1, 5)
        covered = outcome >= lower
        calibrator.update(device_group, np.maximum(prediction - outcome, 0))

        download_ratio = throughput / np.maximum(action, 0.1)
        buffer_s = np.clip(buffer_s + 2.0 * download_ratio - 2.0, 0, 15)
        rebuffer = buffer_s <= 0.01
        debt = np.maximum(
            0,
            config["debt_decay"] * debt + config["target_qoe"] - outcome,
        )
        for user in range(users):
            records.append(
                {
                    "controller": controller,
                    "seed": seed,
                    "step": step,
                    "shifted": int(shifted),
                    "user": user,
                    "device_group": int(device_group[user]),
                    "throughput_mbps": throughput[user],
                    "capacity_mbps": shared_capacity,
                    "allocation_mbps": action[user],
                    "qoe": outcome[user],
                    "target_qoe": config["target_qoe"],
                    "predicted_qoe": prediction[user],
                    "lower_qoe": lower[user],
                    "covered": int(covered[user]),
                    "debt": debt[user],
                    "rebuffer": int(rebuffer[user]),
                    "switched": int(action[user] != previous[user]),
                }
            )
        previous = action
    return records


def cvar(values: np.ndarray, proportion: float = 0.10) -> float:
    count = max(1, int(np.ceil(len(values) * proportion)))
    return float(np.sort(values)[:count].mean())


def summarise(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (controller, seed), group in frame.groupby(["controller", "seed"]):
        user_means = group.groupby("user")["qoe"].mean().to_numpy()
        rows.append(
            {
                "controller": controller,
                "seed": seed,
                "mean_qoe": group["qoe"].mean(),
                "worst_user_mean_qoe": user_means.min(),
                "cvar10_qoe": cvar(group["qoe"].to_numpy()),
                "jain_user_qoe": user_means.sum() ** 2
                / (len(user_means) * np.square(user_means).sum()),
                "group_qoe_gap": abs(
                    group[group.device_group == 0]["qoe"].mean()
                    - group[group.device_group == 1]["qoe"].mean()
                ),
                "mean_debt": group["debt"].mean(),
                "terminal_max_debt": group[group.step == group.step.max()]
                ["debt"].max(),
                "service_violation_rate": (
                    group["qoe"] < group["target_qoe"]
                ).mean(),
                "coverage": group["covered"].mean(),
                "coverage_pre_shift": group[group.shifted == 0]["covered"].mean(),
                "coverage_post_shift": group[group.shifted == 1]["covered"].mean(),
                "rebuffer_rate": group["rebuffer"].mean(),
                "switch_rate": group["switched"].mean(),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    seed = int(config["seed"])
    device = "cuda" if torch.cuda.is_available() else "cpu"
    x, y, y_var, groups = load_dataset(args.data / "published_qoe.csv")
    train, calibration, test = split_dataset(x, y, y_var, groups, seed)
    predictor = config["predictor"]
    started = time.time()
    model = train_ensemble(
        x[train],
        y[train],
        y_var[train],
        ensemble_size=predictor["ensemble_size"],
        epochs=predictor["epochs"],
        width=predictor["hidden_width"],
        learning_rate=predictor["learning_rate"],
        weight_decay=predictor["weight_decay"],
        seed=seed,
        device=device,
    )
    cal_prediction, _ = model.predict(x[calibration])
    cal_residual = np.maximum(cal_prediction - y[calibration], 0)
    # Begin globally calibrated. Online updates then create separate residual
    # histories for the two operational device regimes encountered in replay.
    cal_group = np.zeros(len(calibration), dtype=int)
    exp = config["experiment"]
    base_calibrator = AdaptiveConformal.fit(
        cal_residual,
        cal_group,
        alpha=exp["conformal_alpha"],
        window=exp["online_window"],
        adaptive=True,
    )

    test_prediction, test_uncertainty = model.predict(x[test])
    predictor_metrics = {
        "test_rows": int(len(test)),
        "test_groups": int(len(np.unique(groups[test]))),
        "mae": float(np.mean(np.abs(test_prediction - y[test]))),
        "rmse": float(np.sqrt(np.mean(np.square(test_prediction - y[test])))),
        "mean_predictive_std": float(test_uncertainty.mean()),
        "device": device,
        "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
    }
    traces = load_traces(args.data / "traces")
    all_records = []
    for controller in config["controllers"]:
        for run_seed in range(seed, seed + exp["seeds"]):
            all_records.extend(
                run_episode(
                    controller,
                    model,
                    base_calibrator,
                    traces,
                    x[train],
                    exp,
                    run_seed,
                )
            )
    args.output.mkdir(parents=True, exist_ok=True)
    raw = pd.DataFrame(all_records)
    summary = summarise(raw)
    raw.to_csv(args.output / "episode_results.csv", index=False)
    summary.to_csv(args.output / "seed_metrics.csv", index=False)
    aggregate = summary.groupby("controller").agg(["mean", "std"])
    aggregate.to_csv(args.output / "aggregate_metrics.csv")
    run_info = {
        "predictor": predictor_metrics,
        "elapsed_seconds": time.time() - started,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "platform": platform.platform(),
        "config": config,
        "methodological_caveat": (
            "This is a GPU-backed replay/simulation testbed grounded in published "
            "subjective ratings and captured traffic. It is not a live multi-user "
            "VR network experiment and must not be reported as one."
        ),
    }
    (args.output / "run_info.json").write_text(
        json.dumps(run_info, indent=2), encoding="utf-8"
    )
    print(json.dumps(predictor_metrics, indent=2))
    print(aggregate.round(4).to_string())


if __name__ == "__main__":
    main()
