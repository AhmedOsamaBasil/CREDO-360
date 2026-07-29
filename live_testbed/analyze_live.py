"""Seed-level analysis for the paired live CREDO-360 Mininet campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import rankdata, wilcoxon


PRIMARY_METRICS = [
    "mean_operational_qoe",
    "worst_user_mean_operational_qoe",
    "cvar10_operational_qoe",
    "jain_user_mean_operational_qoe",
    "service_violation_rate",
    "total_stall_s",
    "switch_rate",
]
CONFIRMATORY_BASELINES = ["conformal_nash", "conformal_debt_ungated"]
CONFIRMATORY_METRICS = [
    "worst_user_mean_operational_qoe",
    "jain_user_mean_operational_qoe",
    "total_stall_s",
]


def cvar(values: np.ndarray, proportion: float = 0.10) -> float:
    count = max(1, int(np.ceil(len(values) * proportion)))
    return float(np.sort(values)[:count].mean())


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    total = len(p_values)
    for rank, index in enumerate(order):
        running = max(running, (total - rank) * p_values[index])
        adjusted[index] = min(running, 1.0)
    return adjusted


def paired_bootstrap(
    proposed: np.ndarray,
    baseline: np.ndarray,
    rng: np.random.Generator,
    draws: int = 10000,
) -> tuple[float, float]:
    delta = proposed - baseline
    indices = rng.integers(0, len(delta), size=(draws, len(delta)))
    sampled = delta[indices].mean(axis=1)
    return tuple(np.quantile(sampled, [0.025, 0.975]))


def matched_rank_biserial(delta: np.ndarray) -> float:
    nonzero = delta[~np.isclose(delta, 0)]
    if not len(nonzero):
        return 0.0
    ranks = rankdata(np.abs(nonzero))
    return float(
        (ranks[nonzero > 0].sum() - ranks[nonzero < 0].sum()) / ranks.sum()
    )


def prepare_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "seed" not in frame:
        frame["seed"] = 0
    if "regime" not in frame:
        frame["regime"] = "legacy"
    if "controller_position" not in frame:
        frame["controller_position"] = 0
    if "warmup" not in frame:
        frame["warmup"] = 0
    if "decision_ms" not in frame:
        frame["decision_ms"] = np.nan
    if "capacity_slack_mbps" not in frame:
        epoch_sum = frame.groupby(["seed", "controller", "epoch"])[
            "allocated_mbps"
        ].transform("sum")
        frame["capacity_slack_mbps"] = frame["capacity_mbps"] - epoch_sum
    if "opportunity_gain" not in frame:
        frame["opportunity_gain"] = 0.0
    if "debt_term" not in frame:
        frame["debt_term"] = 0.0
    return frame[frame["warmup"].astype(int) == 0].copy()


def seed_metrics(frame: pd.DataFrame, target: float) -> pd.DataFrame:
    records = []
    for (seed, regime, controller), group in frame.groupby(
        ["seed", "regime", "controller"], sort=False
    ):
        user_means = group.groupby("user")["operational_qoe"].mean().to_numpy()
        qoe = group["operational_qoe"].to_numpy()
        epoch_rows = group.drop_duplicates(["epoch"])
        records.append(
            {
                "seed": int(seed),
                "regime": regime,
                "controller": controller,
                "controller_position": int(group["controller_position"].iloc[0]),
                "mean_operational_qoe": qoe.mean(),
                "worst_user_mean_operational_qoe": user_means.min(),
                "cvar10_operational_qoe": cvar(qoe),
                "jain_user_mean_operational_qoe": user_means.sum() ** 2
                / (len(user_means) * np.square(user_means).sum()),
                "service_floor": target,
                "service_violation_rate": np.mean(qoe < target),
                "mean_service_shortfall": np.maximum(target - qoe, 0).mean(),
                "mean_throughput_mbps": group["throughput_mbps"].mean(),
                "total_stall_s": group["stall_s"].sum(),
                "switch_rate": group["switched"].mean(),
                "mean_debt_after": group["debt_after"].mean(),
                "terminal_max_debt": group.loc[
                    group["epoch"] == group["epoch"].max(), "debt_after"
                ].max(),
                "opportunity_activation_rate": np.mean(
                    group["opportunity_gain"] > 1e-9
                ),
                "debt_objective_activation_rate": np.mean(
                    epoch_rows["debt_term"] > 1e-9
                ),
                "mean_decision_ms": group["decision_ms"].mean(),
                "p95_decision_ms": group["decision_ms"].quantile(0.95),
                "mean_epoch_wall_s": group["epoch_wall_s"].mean(),
                "maximum_allocation_capacity_excess_mbps": max(
                    0.0, -group["capacity_slack_mbps"].min()
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def aggregate_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    numeric = [
        column
        for column in metrics.select_dtypes(include=[np.number]).columns
        if column not in {"seed", "controller_position"}
    ]
    rows = []
    for controller, group in metrics.groupby("controller", sort=False):
        for metric in numeric:
            values = group[metric].dropna().to_numpy()
            if not len(values):
                continue
            half_width = (
                1.96 * values.std(ddof=1) / np.sqrt(len(values))
                if len(values) > 1
                else np.nan
            )
            rows.append(
                {
                    "controller": controller,
                    "metric": metric,
                    "n": len(values),
                    "mean": values.mean(),
                    "std": values.std(ddof=1) if len(values) > 1 else np.nan,
                    "ci95_low": values.mean() - half_width,
                    "ci95_high": values.mean() + half_width,
                }
            )
    return pd.DataFrame(rows)


def stratified_metrics(metrics: pd.DataFrame, stratum: str) -> pd.DataFrame:
    outcomes = [
        "mean_operational_qoe",
        "worst_user_mean_operational_qoe",
        "jain_user_mean_operational_qoe",
        "service_violation_rate",
        "total_stall_s",
        "switch_rate",
        "mean_decision_ms",
    ]
    rows = []
    for (controller, value), group in metrics.groupby(
        ["controller", stratum], sort=False
    ):
        for metric in outcomes:
            observations = group[metric].dropna().to_numpy()
            rows.append(
                {
                    "controller": controller,
                    stratum: value,
                    "metric": metric,
                    "n": len(observations),
                    "mean": observations.mean(),
                    "std": (
                        observations.std(ddof=1)
                        if len(observations) > 1
                        else np.nan
                    ),
                }
            )
    return pd.DataFrame(rows)


def audit_campaign(raw: pd.DataFrame) -> dict:
    pair_counts = raw.groupby(["seed", "controller"]).size()
    profile_capacity_nunique = raw.groupby(["seed", "run_epoch"])[
        "capacity_mbps"
    ].nunique()
    profile_segment_nunique = raw.groupby(["seed", "run_epoch"])[
        "segment_number"
    ].nunique()
    order_balance = (
        raw.drop_duplicates(["seed", "controller"])[
            ["controller", "controller_position"]
        ]
        .value_counts()
        .sort_index()
    )
    return {
        "rows": int(len(raw)),
        "seeds": int(raw.seed.nunique()),
        "controllers": int(raw.controller.nunique()),
        "controller_seed_pairs": int(len(pair_counts)),
        "minimum_rows_per_pair": int(pair_counts.min()),
        "maximum_rows_per_pair": int(pair_counts.max()),
        "warmup_rows": int((raw.warmup.astype(int) == 1).sum()),
        "analysed_rows": int((raw.warmup.astype(int) == 0).sum()),
        "capacity_profile_mismatch_cells": int(
            (profile_capacity_nunique != 1).sum()
        ),
        "segment_profile_mismatch_cells": int(
            (profile_segment_nunique != 1).sum()
        ),
        "maximum_capacity_excess_mbps": float(
            max(0.0, -raw["capacity_slack_mbps"].min())
        ),
        "controller_position_counts": {
            f"{controller}@{position}": int(count)
            for (controller, position), count in order_balance.items()
        },
    }


def paired_inference(
    metrics: pd.DataFrame, proposed_name: str = "risk_debt"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(20260729)
    tests, intervals = [], []
    proposed = metrics[metrics.controller == proposed_name].set_index("seed")
    for baseline_name in metrics.controller.unique():
        if baseline_name == proposed_name:
            continue
        baseline = metrics[metrics.controller == baseline_name].set_index("seed")
        common = proposed.index.intersection(baseline.index)
        for metric in PRIMARY_METRICS:
            left = proposed.loc[common, metric].to_numpy()
            right = baseline.loc[common, metric].to_numpy()
            delta = left - right
            if np.allclose(delta, 0):
                statistic, p_value = 0.0, 1.0
            else:
                statistic, p_value = wilcoxon(
                    left, right, alternative="two-sided", zero_method="wilcox"
                )
            low, high = paired_bootstrap(left, right, rng)
            tests.append(
                {
                    "proposed": proposed_name,
                    "baseline": baseline_name,
                    "metric": metric,
                    "n_pairs": len(common),
                    "proposed_mean": left.mean(),
                    "baseline_mean": right.mean(),
                    "mean_delta": delta.mean(),
                    "median_delta": np.median(delta),
                    "positive_pairs": int((delta > 0).sum()),
                    "negative_pairs": int((delta < 0).sum()),
                    "rank_biserial": matched_rank_biserial(delta),
                    "wilcoxon_statistic": statistic,
                    "p_value": p_value,
                }
            )
            intervals.append(
                {
                    "proposed": proposed_name,
                    "baseline": baseline_name,
                    "metric": metric,
                    "n_pairs": len(common),
                    "mean_delta": delta.mean(),
                    "bootstrap_ci95_low": low,
                    "bootstrap_ci95_high": high,
                }
            )
    tests_frame = pd.DataFrame(tests)
    tests_frame["p_holm_global"] = holm_adjust(
        tests_frame["p_value"].to_numpy()
    )
    tests_frame["p_holm_within_metric"] = tests_frame.groupby("metric")[
        "p_value"
    ].transform(lambda values: holm_adjust(values.to_numpy()))
    confirmatory = tests_frame.baseline.isin(
        CONFIRMATORY_BASELINES
    ) & tests_frame.metric.isin(CONFIRMATORY_METRICS)
    tests_frame["p_holm_confirmatory"] = np.nan
    tests_frame.loc[confirmatory, "p_holm_confirmatory"] = holm_adjust(
        tests_frame.loc[confirmatory, "p_value"].to_numpy()
    )
    return tests_frame, pd.DataFrame(intervals)


def controller_figure(metrics: pd.DataFrame, output: Path) -> None:
    labels = {
        "mean_greedy": "Mean\ngreedy",
        "proportional_fair": "Prop.\nfair",
        "uncertainty_nash": "Uncertainty\nNash",
        "conformal_nash": "Conformal\nNash",
        "conformal_debt_ungated": "Ungated\ndebt",
        "risk_debt": "CREDO-360",
    }
    order = [name for name in labels if name in set(metrics.controller)]
    panels = [
        ("mean_operational_qoe", "Mean operational QoE", False),
        ("worst_user_mean_operational_qoe", "Worst-user mean QoE", False),
        ("jain_user_mean_operational_qoe", "Jain fairness", False),
        ("service_violation_rate", "Service-violation rate", True),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.2))
    for axis, (metric, title, lower_is_better) in zip(axes.flat, panels):
        groups = [metrics.loc[metrics.controller == name, metric] for name in order]
        means = np.array([group.mean() for group in groups])
        errors = np.array(
            [
                1.96 * group.std(ddof=1) / np.sqrt(len(group))
                if len(group) > 1
                else 0
                for group in groups
            ]
        )
        colors = [
            "#1f77b4" if name == "risk_debt" else "#a7b7c7" for name in order
        ]
        positions = np.arange(len(order))
        axis.errorbar(
            positions,
            means,
            yerr=errors,
            fmt="none",
            ecolor="#303030",
            elinewidth=1.2,
            capsize=3,
            zorder=2,
        )
        axis.scatter(
            positions,
            means,
            s=58,
            c=colors,
            edgecolor="#303030",
            linewidth=0.5,
            zorder=3,
        )
        axis.set_xticks(np.arange(len(order)), [labels[name] for name in order])
        axis.set_title(title)
        axis.grid(axis="y", alpha=0.25)
        lower = np.min(means - errors)
        upper = np.max(means + errors)
        padding = max((upper - lower) * 0.24, 0.002)
        axis.set_ylim(lower - padding, upper + padding)
        if lower_is_better:
            axis.text(
                0.98,
                0.96,
                "lower is better",
                transform=axis.transAxes,
                ha="right",
                va="top",
                fontsize=8,
            )
    fig.suptitle("Paired live Mininet campaign (mean ± 95% normal CI)")
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def mechanism_figure(frame: pd.DataFrame, output: Path) -> None:
    credo = frame[frame.controller == "risk_debt"].copy()
    if credo.empty:
        return
    per_epoch = (
        credo.groupby(["seed", "epoch"])
        .agg(
            debt=("debt_before", "mean"),
            opportunity=("opportunity_gain", lambda values: np.mean(values > 1e-9)),
            debt_term=("debt_term", "first"),
        )
        .reset_index()
    )
    summary = per_epoch.groupby("epoch").agg(
        debt=("debt", "mean"),
        debt_sem=("debt", "sem"),
        opportunity=("opportunity", "mean"),
        opportunity_sem=("opportunity", "sem"),
        debt_term=("debt_term", "mean"),
    )
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 5.2), sharex=True)
    x = summary.index.to_numpy()
    axes[0].plot(x, summary.debt, marker="o", color="#d62728", label="Mean debt")
    axes[0].fill_between(
        x,
        summary.debt - 1.96 * summary.debt_sem.fillna(0),
        summary.debt + 1.96 * summary.debt_sem.fillna(0),
        color="#d62728",
        alpha=0.16,
    )
    axes[0].set_ylabel("QoE-deprivation debt")
    axes[0].grid(alpha=0.25)
    axes[1].plot(
        x,
        summary.debt_term,
        marker="s",
        color="#1f77b4",
        label="Debt objective contribution",
    )
    axes[1].set_ylabel("Selected debt term")
    axes[1].set_xlabel("Analysed segment epoch")
    axes[1].grid(alpha=0.25)
    activation_min = 100.0 * float(summary.opportunity.min())
    activation_max = 100.0 * float(summary.opportunity.max())
    axes[1].text(
        0.98,
        0.95,
        f"gate active for {activation_min:.1f}–{activation_max:.1f}% of users",
        transform=axes[1].transAxes,
        ha="right",
        va="top",
        fontsize=8,
    )
    fig.suptitle("CREDO-360 debt state and objective contribution")
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def regime_delta_figure(metrics: pd.DataFrame, output: Path) -> None:
    proposed = metrics[metrics.controller == "risk_debt"].set_index("seed")
    baseline = metrics[metrics.controller == "conformal_nash"].set_index("seed")
    common = proposed.index.intersection(baseline.index)
    panels = [
        ("worst_user_mean_operational_qoe", "Worst-user mean QoE"),
        ("jain_user_mean_operational_qoe", "Jain fairness"),
        ("mean_operational_qoe", "Mean operational QoE"),
        ("service_violation_rate", "Service-violation rate"),
    ]
    regimes = ["stable", "bursty", "shift"]
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 5.8))
    for axis, (metric, title) in zip(axes.flat, panels):
        means, errors = [], []
        for regime in regimes:
            seeds = [
                seed
                for seed in common
                if proposed.loc[seed, "regime"] == regime
            ]
            delta = (
                proposed.loc[seeds, metric].to_numpy()
                - baseline.loc[seeds, metric].to_numpy()
            )
            means.append(delta.mean())
            errors.append(
                1.96 * delta.std(ddof=1) / np.sqrt(len(delta))
                if len(delta) > 1
                else 0
            )
        positions = np.arange(len(regimes))
        axis.axhline(0, color="#555555", linewidth=0.9)
        axis.errorbar(
            positions,
            means,
            yerr=errors,
            fmt="o",
            color="#1f77b4",
            capsize=4,
        )
        axis.set_xticks(positions, [name.capitalize() for name in regimes])
        axis.set_title(title)
        axis.set_ylabel(r"$\Delta$ CREDO-360 $-$ conformal Nash")
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle("Paired live effect by capacity regime")
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    output = args.output_dir or args.input.parent
    output.mkdir(parents=True, exist_ok=True)
    metadata_path = args.input.parent / "run_metadata.json"
    metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.exists()
        else {}
    )
    target = float(metadata.get("target_operational_qoe", 4.0))
    raw = pd.read_csv(args.input)
    audit = audit_campaign(raw)
    frame = prepare_frame(args.input)
    metrics = seed_metrics(frame, target)
    aggregate = aggregate_metrics(metrics)
    regime = stratified_metrics(metrics, "regime")
    order = stratified_metrics(metrics, "controller_position")
    tests, intervals = paired_inference(metrics)

    metrics.to_csv(output / "live_seed_metrics.csv", index=False)
    aggregate.to_csv(output / "live_aggregate_metrics.csv", index=False)
    regime.to_csv(output / "live_regime_metrics.csv", index=False)
    order.to_csv(output / "live_order_metrics.csv", index=False)
    tests.to_csv(output / "live_paired_tests.csv", index=False)
    intervals.to_csv(output / "live_bootstrap_ci.csv", index=False)
    controller_figure(metrics, output / "live_controller_comparison.png")
    mechanism_figure(frame, output / "live_debt_mechanism.png")
    regime_delta_figure(metrics, output / "live_regime_deltas.png")
    (output / "campaign_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )

    summary = {
        "metadata": metadata,
        "audit": audit,
        "completed_seeds": int(metrics.seed.nunique()),
        "controllers": metrics.controller.unique().tolist(),
        "aggregate": aggregate.to_dict(orient="records"),
        "paired_tests": tests.to_dict(orient="records"),
        "interpretation": (
            "Operational QoE is model-estimated from measured transfers. "
            "Statistical inference describes this emulated mechanism and does "
            "not substitute for independent subjective validation."
        ),
    }
    (output / "live_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "completed_seeds": summary["completed_seeds"],
                "controllers": summary["controllers"],
                "primary_tests": len(tests),
                "output_dir": str(output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
