"""Create the paired primary-outcome figure for TMM Experiment A."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROPOSED = "risk_debt"
BASELINE = "resource_debt_ungated"
PANELS = [
    (
        "mean_wasted_allocation_mbps",
        "Wasted allocation (Mb/s)",
        "Wasted service allocation",
    ),
    (
        "worst_unimpaired_user_mean_operational_qoe",
        "Operational QoE",
        "Worst unimpaired user",
    ),
    (
        "debt_weighted_opportunity_activation",
        "Debt-weighted activation",
        "Opportunity activation",
    ),
    (
        "total_stall_s",
        "Total stall (s)",
        "Aggregate stall",
    ),
]


def mean_interval(values: np.ndarray) -> tuple[float, float, float]:
    mean = float(values.mean())
    half_width = (
        1.96 * float(values.std(ddof=1)) / np.sqrt(len(values))
        if len(values) > 1
        else 0.0
    )
    return mean, mean - half_width, mean + half_width


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--tests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    metrics = pd.read_csv(args.metrics)
    tests = pd.read_csv(args.tests).set_index("metric")
    metrics = metrics[metrics["condition"] == "non_actionable"]
    proposed = metrics[metrics["controller"] == PROPOSED].set_index("seed")
    baseline = metrics[metrics["controller"] == BASELINE].set_index("seed")
    seeds = proposed.index.intersection(baseline.index).sort_values()
    if len(seeds) != 30:
        raise ValueError(f"Expected 30 paired seeds, found {len(seeds)}")

    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axes = plt.subplots(2, 2, figsize=(8.0, 6.2))
    colors = ["#C84C39", "#315A91"]
    for axis, (metric, ylabel, title) in zip(axes.flat, PANELS):
        left = baseline.loc[seeds, metric].to_numpy(float)
        right = proposed.loc[seeds, metric].to_numpy(float)
        for first, second in zip(left, right):
            axis.plot([0, 1], [first, second], color="#9A9A9A", alpha=0.32, lw=0.8)
        axis.scatter(
            np.zeros(len(left)),
            left,
            color=colors[0],
            alpha=0.75,
            s=15,
            zorder=3,
        )
        axis.scatter(
            np.ones(len(right)),
            right,
            color=colors[1],
            alpha=0.75,
            s=15,
            zorder=3,
        )
        for position, values, color in zip([0, 1], [left, right], colors):
            mean, low, high = mean_interval(values)
            axis.errorbar(
                position,
                mean,
                yerr=[[mean - low], [high - mean]],
                fmt="D",
                color="black",
                markerfacecolor=color,
                markersize=6,
                capsize=4,
                linewidth=1.5,
                zorder=4,
            )
        p_holm = float(tests.loc[metric, "p_holm"])
        axis.set_title(f"{title}\nHolm $p$={p_holm:.3g}", fontsize=10)
        axis.set_ylabel(ylabel)
        axis.set_xticks([0, 1], ["Resource debt", "CREDO-360"])
        axis.tick_params(axis="x", labelrotation=8)
        axis.grid(axis="x", visible=False)

    figure.suptitle(
        "Non-actionable impairment: paired seed-level outcomes",
        fontsize=12,
    )
    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=220, bbox_inches="tight")
    figure.savefig(args.output.with_suffix(".pdf"), bbox_inches="tight")
    print(args.output)


if __name__ == "__main__":
    main()
