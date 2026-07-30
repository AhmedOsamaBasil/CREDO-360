"""Frozen paired analysis for Experiment C."""

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

PROPOSED = "risk_debt"
BASELINE = "conformal_nash"
EXPECTED_CONTROLLERS = {
    "mean_nash",
    "conformal_nash",
    "mean_debt_ungated",
    "mean_debt_gated",
    "conformal_debt_ungated",
    "risk_debt",
    "fair_edge_nsw_proxy",
    "aci_nash",
}
PRIMARY = [
    ("worst_user_vw_psnr_db", 1, "Worst-user VW-PSNR (dB)"),
    ("worst_user_vw_ssim", 1, "Worst-user VW-SSIM"),
    ("jain_viewport_quality", 1, "Jain viewport-quality fairness"),
    ("total_stall_s", -1, "Total stall (s)"),
    ("switch_rate", -1, "Representation-switch rate"),
]
ABLATION_CONTRASTS = [
    ("calibration_without_debt", "conformal_nash", "mean_nash"),
    (
        "debt_given_calibration",
        "conformal_debt_ungated",
        "conformal_nash",
    ),
    (
        "gate_given_calibrated_debt",
        "risk_debt",
        "conformal_debt_ungated",
    ),
    ("calibration_given_gated_debt", "risk_debt", "mean_debt_gated"),
    (
        "gate_given_mean_debt",
        "mean_debt_gated",
        "mean_debt_ungated",
    ),
]


def jain(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    return float(values.sum() ** 2 / (len(values) * np.sum(values**2)))


def paired_bootstrap(
    differences: np.ndarray,
    *,
    seed: int = 20260729,
    resamples: int = 20_000,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(
        0, len(differences), size=(resamples, len(differences))
    )
    samples = differences[indices].mean(axis=1)
    return tuple(np.quantile(samples, [0.025, 0.975]).tolist())


def rank_biserial(differences: np.ndarray) -> float:
    nonzero = differences[np.abs(differences) > 1e-12]
    if not len(nonzero):
        return 0.0
    ranks = rankdata(np.abs(nonzero), method="average")
    positive = ranks[nonzero > 0].sum()
    negative = ranks[nonzero < 0].sum()
    return float((positive - negative) / (positive + negative))


def holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.zeros(len(p_values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, (len(p_values) - rank) * p_values[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted.tolist()


def audit(frame: pd.DataFrame, expected_seeds: int) -> dict:
    key = ["seed", "controller", "epoch", "user"]
    duplicates = int(frame.duplicated(key).sum())
    pair_counts = (
        frame.groupby(["seed", "controller"]).size().unstack(fill_value=0)
    )
    controllers = sorted(frame["controller"].unique())
    expected_rows = int(frame["epoch"].nunique() * frame["user"].nunique())
    incomplete = int((pair_counts != expected_rows).sum().sum())
    plan_fields = ["regime", "content", "subject", "capacity_mbps"]
    mismatches = 0
    for field in plan_fields:
        counts = frame.groupby(["seed", "epoch", "user"])[field].nunique()
        mismatches += int((counts != 1).sum())
    test_only = bool(
        (frame["subject"] > 0).all()
        and "split" in frame
        and (frame["split"] == "test").all()
    )
    passed = (
        duplicates == 0
        and incomplete == 0
        and mismatches == 0
        and frame["seed"].nunique() == expected_seeds
        and set(controllers) == EXPECTED_CONTROLLERS
        and test_only
    )
    return {
        "passed": passed,
        "rows": len(frame),
        "seeds": int(frame["seed"].nunique()),
        "controllers": controllers,
        "expected_rows_per_controller_seed": expected_rows,
        "duplicate_rows": duplicates,
        "incomplete_pair_cells": incomplete,
        "paired_plan_mismatches": mismatches,
        "held_out_test_traces_only": test_only,
    }


def build_seed_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    for (seed, controller), group in frame.groupby(["seed", "controller"]):
        user_quality = group.groupby("user")["vw_psnr_db"].mean()
        user_ssim = group.groupby("user")["vw_ssim"].mean()
        user_quality_index = group.groupby("user")[
            "viewport_quality_index"
        ].mean()
        ordered = group.sort_values(["user", "epoch"])
        log_switch = []
        for _, user_group in ordered.groupby("user"):
            rate = user_group["allocated_mbps"].to_numpy()
            if len(rate) > 1:
                log_switch.extend(
                    np.abs(np.diff(np.log(rate + 0.05))).tolist()
                )
        records.append(
            {
                "seed": seed,
                "regime": group["regime"].iloc[0],
                "controller": controller,
                "mean_vw_psnr_db": group["vw_psnr_db"].mean(),
                "worst_user_vw_psnr_db": user_quality.min(),
                "mean_vw_ssim": group["vw_ssim"].mean(),
                "worst_user_vw_ssim": user_ssim.min(),
                "jain_viewport_quality": jain(
                    user_quality_index.to_numpy()
                ),
                "total_stall_s": group["stall_s"].sum(),
                "switch_rate": group["switched"].mean(),
                "mean_log_switch": (
                    float(np.mean(log_switch)) if log_switch else 0.0
                ),
            }
        )
    return pd.DataFrame(records)


def primary_tests(metrics: pd.DataFrame) -> pd.DataFrame:
    rows, raw_p = [], []
    for outcome, direction, label in PRIMARY:
        pivot = metrics.pivot(index="seed", columns="controller", values=outcome)
        differences = (
            pivot[PROPOSED].to_numpy() - pivot[BASELINE].to_numpy()
        )
        if np.allclose(differences, 0):
            p_value = 1.0
        else:
            p_value = float(
                wilcoxon(
                    differences,
                    alternative="two-sided",
                    zero_method="pratt",
                    method="auto",
                ).pvalue
            )
        low, high = paired_bootstrap(differences)
        raw_p.append(p_value)
        rows.append(
            {
                "outcome": outcome,
                "label": label,
                "direction": direction,
                "credo360_mean": pivot[PROPOSED].mean(),
                "conformal_nash_mean": pivot[BASELINE].mean(),
                "mean_delta": differences.mean(),
                "ci95_low": low,
                "ci95_high": high,
                "wilcoxon_p": p_value,
                "rank_biserial": rank_biserial(differences),
                "pairs_positive": int((differences > 0).sum()),
                "pairs_negative": int((differences < 0).sum()),
                "pairs_tied": int((differences == 0).sum()),
            }
        )
    adjusted = holm(raw_p)
    for row, value in zip(rows, adjusted):
        row["holm_p"] = value
    return pd.DataFrame(rows)


def paired_test_family(
    metrics: pd.DataFrame,
    comparisons: list[tuple[str, str, str]],
    outcomes: list[tuple[str, int, str]],
) -> pd.DataFrame:
    """Multiplicity-corrected paired comparisons for declared contrasts."""
    rows: list[dict] = []
    raw_p: list[float] = []
    for contrast, proposed, baseline in comparisons:
        for outcome, direction, label in outcomes:
            pivot = metrics.pivot(
                index="seed", columns="controller", values=outcome
            )
            differences = (
                pivot[proposed].to_numpy() - pivot[baseline].to_numpy()
            )
            p_value = (
                1.0
                if np.allclose(differences, 0)
                else float(
                    wilcoxon(
                        differences,
                        alternative="two-sided",
                        zero_method="pratt",
                        method="auto",
                    ).pvalue
                )
            )
            low, high = paired_bootstrap(differences)
            raw_p.append(p_value)
            rows.append(
                {
                    "contrast": contrast,
                    "proposed": proposed,
                    "baseline": baseline,
                    "outcome": outcome,
                    "label": label,
                    "direction": direction,
                    "paired_seeds": len(differences),
                    "proposed_mean": pivot[proposed].mean(),
                    "baseline_mean": pivot[baseline].mean(),
                    "mean_delta": differences.mean(),
                    "ci95_low": low,
                    "ci95_high": high,
                    "wilcoxon_p": p_value,
                    "rank_biserial": rank_biserial(differences),
                }
            )
    for row, adjusted in zip(rows, holm(raw_p)):
        row["holm_p_family"] = adjusted
    return pd.DataFrame(rows)


def content_effects(frame: pd.DataFrame) -> pd.DataFrame:
    values = (
        frame.groupby(["seed", "controller", "content"])
        .agg(
            mean_vw_psnr_db=("vw_psnr_db", "mean"),
            mean_vw_ssim=("vw_ssim", "mean"),
            total_stall_s=("stall_s", "sum"),
        )
        .reset_index()
    )
    rows = []
    for content, group in values.groupby("content"):
        for outcome in [
            "mean_vw_psnr_db",
            "mean_vw_ssim",
            "total_stall_s",
        ]:
            pivot = group.pivot(
                index="seed", columns="controller", values=outcome
            ).dropna()
            differences = pivot[PROPOSED] - pivot[BASELINE]
            low, high = paired_bootstrap(differences.to_numpy())
            rows.append(
                {
                    "content": content,
                    "outcome": outcome,
                    "paired_seeds": len(differences),
                    "mean_delta": differences.mean(),
                    "ci95_low": low,
                    "ci95_high": high,
                }
            )
    return pd.DataFrame(rows)


def plot_primary(metrics: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.1))
    for axis, (outcome, direction, label) in zip(axes, PRIMARY[:3]):
        pivot = metrics.pivot(index="seed", columns="controller", values=outcome)
        for _, row in pivot.iterrows():
            axis.plot(
                [0, 1],
                [row[BASELINE], row[PROPOSED]],
                color="#a7a7a7",
                alpha=0.42,
                linewidth=0.8,
            )
        means = [pivot[BASELINE].mean(), pivot[PROPOSED].mean()]
        standard = [
            1.96 * pivot[BASELINE].sem(),
            1.96 * pivot[PROPOSED].sem(),
        ]
        axis.errorbar(
            [0, 1],
            means,
            yerr=standard,
            fmt="D",
            color="#a51c30",
            capsize=4,
            markersize=5,
            zorder=4,
        )
        axis.set_xticks([0, 1], ["Conformal Nash", "CREDO-360"])
        axis.set_ylabel(label)
        axis.grid(axis="y", alpha=0.2)
        arrow = "higher is better" if direction > 0 else "lower is better"
        axis.set_title(arrow, fontsize=9)
    fig.suptitle(
        "Objective viewport-quality fairness (30 held-out-trace seeds)",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_complexity(content_path: Path, output: Path) -> None:
    content = pd.read_csv(content_path)
    fig, axis = plt.subplots(figsize=(6.4, 4.4))
    colours = {"low": "#4c78a8", "medium": "#f2a541", "high": "#a51c30"}
    offsets = {
        "BuskingCity01": (6, 5, "left"),
        "Lake01": (6, 5, "left"),
        "ConferenceCenter01": (6, -12, "left"),
        "Skateboarding01": (6, 8, "left"),
        "Badminton05": (-6, -17, "right"),
        "ForestWalk03": (-6, -9, "right"),
    }
    for _, row in content.iterrows():
        axis.scatter(
            row["spatial_information"],
            row["temporal_information"],
            s=70,
            color=colours[row["relative_complexity"]],
            label=row["relative_complexity"],
        )
        x_offset, y_offset, horizontal = offsets.get(
            row["content"], (6, 5, "left")
        )
        axis.annotate(
            row["content"],
            (row["spatial_information"], row["temporal_information"]),
            xytext=(x_offset, y_offset),
            textcoords="offset points",
            ha=horizontal,
        )
    handles, labels = axis.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    axis.legend(unique.values(), unique.keys(), title="Relative rank")
    axis.set_xlabel("Spatial information (P.910-style SI)")
    axis.set_ylabel("Temporal information (P.910-style TI)")
    axis.margins(x=0.08, y=0.10)
    axis.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_ablation(metrics: pd.DataFrame, output: Path) -> None:
    controllers = [
        "mean_nash",
        "conformal_nash",
        "mean_debt_ungated",
        "mean_debt_gated",
        "conformal_debt_ungated",
        "risk_debt",
    ]
    labels = ["000", "100", "010", "011", "110", "111"]
    outcomes = PRIMARY[:3]
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.2))
    for axis, (outcome, _, label) in zip(axes, outcomes):
        groups = [
            metrics[metrics["controller"] == controller][outcome]
            for controller in controllers
        ]
        means = np.asarray([group.mean() for group in groups])
        intervals = np.asarray([1.96 * group.sem() for group in groups])
        colours = [
            "#4c78a8",
            "#72a7cf",
            "#f2a541",
            "#df8f2d",
            "#c85c5c",
            "#a51c30",
        ]
        axis.errorbar(
            np.arange(len(groups)),
            means,
            yerr=intervals,
            fmt="none",
            ecolor="#444444",
            capsize=3,
            linewidth=1,
        )
        axis.scatter(
            np.arange(len(groups)),
            means,
            c=colours,
            s=52,
            zorder=3,
        )
        axis.set_xticks(np.arange(len(groups)), labels)
        axis.set_xlabel("Calibration / debt / gate")
        axis.set_ylabel(label)
        axis.grid(axis="y", alpha=0.2)
    fig.suptitle(
        "Component ablation (30 paired seeds; mean and 95% normal interval)",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def write_report(
    path: Path,
    audit_result: dict,
    tests: pd.DataFrame,
    content: pd.DataFrame,
    effects: pd.DataFrame,
    ablations: pd.DataFrame,
    recent_baselines: pd.DataFrame,
) -> None:
    lines = [
        "# Experiment C: independent multimedia generalization",
        "",
        "## Validation",
        "",
        f"- Audit: **{'PASS' if audit_result['passed'] else 'FAIL'}**",
        f"- Raw paired rows: {audit_result['rows']:,}",
        f"- Seeds: {audit_result['seeds']}",
        "- Outcomes: objective viewport-weighted luma PSNR and SSIM; not "
        "subjective MOS.",
        "",
        "## Content complexity",
        "",
        "| Content | SI | TI | Relative rank | Held-out users |",
        "|---|---:|---:|---|---:|",
    ]
    for _, row in content.iterrows():
        lines.append(
            f"| {row['content']} | {row['spatial_information']:.2f} | "
            f"{row['temporal_information']:.2f} | "
            f"{row['relative_complexity']} | {int(row['test_subjects'])} |"
        )
    lines.extend(
        [
            "",
            "## Prespecified CREDO-360 versus conformal Nash tests",
            "",
            "| Outcome | CREDO | Baseline | Delta [95% CI] | Holm p | Rank-biserial |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in tests.iterrows():
        lines.append(
            f"| {row['label']} | {row['credo360_mean']:.5f} | "
            f"{row['conformal_nash_mean']:.5f} | {row['mean_delta']:+.5f} "
            f"[{row['ci95_low']:+.5f}, {row['ci95_high']:+.5f}] | "
            f"{row['holm_p']:.4g} | {row['rank_biserial']:+.3f} |"
        )
    lines.extend(
        [
            "",
            "## Component ablation",
            "",
            "The six estimable calibration/debt/gate cells are executable. "
            "The two gate-on/debt-off cells are algebraically identical to "
            "their gate-off counterparts and are therefore structural aliases.",
            "",
            "| Contrast | Outcome | Delta [95% CI] | Holm p |",
            "|---|---|---:|---:|",
        ]
    )
    for _, row in ablations.iterrows():
        lines.append(
            f"| {row['contrast']} | {row['label']} | "
            f"{row['mean_delta']:+.5f} [{row['ci95_low']:+.5f}, "
            f"{row['ci95_high']:+.5f}] | {row['holm_p_family']:.4g} |"
        )
    lines.extend(
        [
            "",
            "## Recent-method executable adaptations",
            "",
            "`fair_edge_nsw_proxy` implements the uncertainty-adjusted Nash "
            "edge objective but not the published MARL/GNN policy. `aci_nash` "
            "implements per-user adaptive conformal alpha feedback but not the "
            "single-user viewport model from Risk as a Resource.",
            "",
            "| Comparator | Outcome | CREDO delta [95% CI] | Holm p |",
            "|---|---|---:|---:|",
        ]
    )
    for _, row in recent_baselines.iterrows():
        lines.append(
            f"| {row['baseline']} | {row['label']} | "
            f"{row['mean_delta']:+.5f} [{row['ci95_low']:+.5f}, "
            f"{row['ci95_high']:+.5f}] | {row['holm_p_family']:.4g} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The experiment tests controller behaviour under independently sourced "
            "content, measured VBR segment sizes, and held-out public HMD traces. "
            "VW-PSNR, VW-SSIM, and the declared quality index are objective "
            "engineering measures. They do not establish subjective "
            "perceptual superiority.",
            "",
            "Content-stratified effects are secondary and are retained in "
            "`content_effects.csv`; they are not additional confirmatory tests. "
            "They are heterogeneous and therefore do not support a claim of "
            "mean-quality improvement for every content.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--measurements",
        type=Path,
        default=Path(
            "multimedia_testbed/results/generalization_v2_30seed/measurements.csv"
        ),
    )
    parser.add_argument(
        "--content-metrics",
        type=Path,
        default=Path(
            "multimedia_testbed/artifacts/qoevave/content_metrics.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("multimedia_testbed/results/generalization_v2_analysis"),
    )
    parser.add_argument("--expected-seeds", type=int, default=30)
    args = parser.parse_args()
    frame = pd.read_csv(args.measurements)
    result = audit(frame, args.expected_seeds)
    if not result["passed"]:
        raise RuntimeError(f"Campaign audit failed: {result}")
    args.output.mkdir(parents=True, exist_ok=True)
    metrics = build_seed_metrics(frame)
    tests = primary_tests(metrics)
    ablations = paired_test_family(
        metrics,
        ABLATION_CONTRASTS,
        PRIMARY[:3],
    )
    recent_baselines = paired_test_family(
        metrics,
        [
            ("credo_vs_fair_edge_proxy", PROPOSED, "fair_edge_nsw_proxy"),
            ("credo_vs_aci_nash", PROPOSED, "aci_nash"),
        ],
        PRIMARY,
    )
    effects = content_effects(frame)
    content = pd.read_csv(args.content_metrics)
    metrics.to_csv(args.output / "seed_metrics.csv", index=False)
    numeric_metrics = [
        column
        for column in metrics.select_dtypes(include=[np.number]).columns
        if column != "seed"
    ]
    metrics.groupby("controller")[numeric_metrics].agg(
        ["mean", "std"]
    ).to_csv(args.output / "controller_summary.csv")
    tests.to_csv(args.output / "primary_tests.csv", index=False)
    ablations.to_csv(args.output / "ablation_contrasts.csv", index=False)
    recent_baselines.to_csv(
        args.output / "recent_baseline_tests.csv", index=False
    )
    effects.to_csv(args.output / "content_effects.csv", index=False)
    (args.output / "audit.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    plot_primary(metrics, args.output / "primary_outcomes.png")
    plot_complexity(
        args.content_metrics, args.output / "content_complexity.png"
    )
    plot_ablation(metrics, args.output / "component_ablation.png")
    write_report(
        args.output / "EXPERIMENT_C_REPORT.md",
        result,
        tests,
        content,
        effects,
        ablations,
        recent_baselines,
    )
    print(tests.to_string(index=False))


if __name__ == "__main__":
    main()
