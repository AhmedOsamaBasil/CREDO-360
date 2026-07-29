"""Paired statistical analysis and publication-style plots for the benchmark."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


PRIMARY = [
    "mean_qoe",
    "worst_user_mean_qoe",
    "cvar10_qoe",
    "jain_user_qoe",
    "group_qoe_gap",
    "mean_debt",
    "terminal_max_debt",
    "service_violation_rate",
    "rebuffer_rate",
]


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    samples = rng.choice(values, size=(20_000, len(values)), replace=True).mean(axis=1)
    return tuple(np.quantile(samples, [0.025, 0.975]))


def holm_adjust(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["p_holm"] = np.nan
    for metric, indices in result.groupby("metric").groups.items():
        ordered = result.loc[indices].sort_values("p_value").index
        running = 0.0
        count = len(ordered)
        for rank, index in enumerate(ordered):
            adjusted = min(1.0, (count - rank) * result.loc[index, "p_value"])
            running = max(running, adjusted)
            result.loc[index, "p_holm"] = running
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--proposed", default="risk_debt")
    args = parser.parse_args()
    seed_metrics = pd.read_csv(args.results / "seed_metrics.csv")
    episodes = pd.read_csv(args.results / "episode_results.csv")
    proposed = seed_metrics[seed_metrics.controller == args.proposed].set_index("seed")
    rng = np.random.default_rng(20260728)

    ci_rows = []
    for (controller, metric), group in seed_metrics.melt(
        id_vars=["controller", "seed"], var_name="metric", value_name="value"
    ).groupby(["controller", "metric"]):
        low, high = bootstrap_ci(group.value.to_numpy(float), rng)
        ci_rows.append(
            {
                "controller": controller,
                "metric": metric,
                "mean": group.value.mean(),
                "ci95_low": low,
                "ci95_high": high,
            }
        )
    pd.DataFrame(ci_rows).to_csv(args.results / "bootstrap_ci.csv", index=False)

    tests = []
    for baseline in sorted(set(seed_metrics.controller) - {args.proposed}):
        comparison = seed_metrics[seed_metrics.controller == baseline].set_index("seed")
        common = proposed.index.intersection(comparison.index)
        for metric in PRIMARY:
            difference = proposed.loc[common, metric] - comparison.loc[common, metric]
            try:
                statistic, p_value = wilcoxon(difference, alternative="two-sided")
            except ValueError:
                statistic, p_value = 0.0, 1.0
            tests.append(
                {
                    "proposed": args.proposed,
                    "baseline": baseline,
                    "metric": metric,
                    "paired_mean_difference": difference.mean(),
                    "wilcoxon_statistic": statistic,
                    "p_value": p_value,
                    "pairs": len(common),
                }
            )
    tests_frame = holm_adjust(pd.DataFrame(tests))
    tests_frame.to_csv(args.results / "paired_wilcoxon_holm.csv", index=False)

    figures = args.results / "figures"
    figures.mkdir(exist_ok=True)
    order = list(seed_metrics.groupby("controller").worst_user_mean_qoe.mean().sort_values().index)
    plot_metrics = [
        ("worst_user_mean_qoe", "Worst-user mean QoE"),
        ("cvar10_qoe", "QoE CVaR (worst 10%)"),
        ("group_qoe_gap", "Device-group QoE gap"),
        ("coverage_post_shift", "Post-shift lower-bound coverage"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for axis, (metric, label) in zip(axes.ravel(), plot_metrics):
        values = [
            seed_metrics[seed_metrics.controller == controller][metric].to_numpy()
            for controller in order
        ]
        axis.boxplot(values, tick_labels=order, showmeans=True)
        axis.set_ylabel(label)
        axis.tick_params(axis="x", rotation=28)
        axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figures / "controller_comparison.png", dpi=220)
    plt.close(fig)

    trajectory = (
        episodes.groupby(["controller", "step"])["qoe"].mean().reset_index()
    )
    fig, axis = plt.subplots(figsize=(10, 4.8))
    for controller, group in trajectory.groupby("controller"):
        axis.plot(group.step, group.qoe, label=controller, linewidth=1.4)
    shift_step = int(episodes.step.max() + 1) // 2
    axis.axvline(shift_step, color="black", linestyle="--", linewidth=1, label="shift")
    axis.set(xlabel="Decision epoch", ylabel="Mean QoE")
    axis.grid(alpha=0.25)
    axis.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(figures / "qoe_trajectory.png", dpi=220)
    plt.close(fig)

    summary = {
        "paired_design": True,
        "seeds": sorted(seed_metrics.seed.unique().tolist()),
        "bootstrap_resamples": 20_000,
        "test": "two-sided paired Wilcoxon signed-rank",
        "multiplicity": "Holm within each metric",
        "warning": (
            "Eight paired seeds provide limited power. Treat p-values as "
            "prototype evidence and increase replications for a submission."
        ),
    }
    (args.results / "analysis_info.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
