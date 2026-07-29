"""Combine service-floor screening runs into a compact sensitivity table."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runs = {
        1.5: args.root / "screen_explicit_target15" / "seed_metrics.csv",
        2.0: args.root / "screen_explicit_target20" / "seed_metrics.csv",
        2.5: args.root / "screen_explicit_schema" / "seed_metrics.csv",
    }
    frames = []
    for target, path in runs.items():
        frame = pd.read_csv(path)
        frame["target_qoe"] = target
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    metrics = [
        "mean_qoe",
        "worst_user_mean_qoe",
        "cvar10_qoe",
        "jain_user_qoe",
        "group_qoe_gap",
        "rebuffer_rate",
    ]
    summary = (
        combined.groupby(["target_qoe", "controller"])[metrics]
        .agg(["mean", "std"])
        .reset_index()
    )
    args.output.mkdir(parents=True, exist_ok=True)
    combined.to_csv(args.output / "target_sensitivity_seed_metrics.csv", index=False)
    summary.to_csv(args.output / "target_sensitivity_summary.csv", index=False)

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    selected = [
        ("worst_user_mean_qoe", "Worst-user mean QoE"),
        ("mean_qoe", "Mean QoE"),
        ("jain_user_qoe", "Jain user-QoE index"),
        ("rebuffer_rate", "Rebuffer rate"),
    ]
    for axis, (metric, label) in zip(axes.ravel(), selected):
        means = (
            combined.groupby(["target_qoe", "controller"])[metric]
            .mean()
            .unstack("controller")
        )
        for controller in ["risk_debt", "uncertainty_nash", "conformal_nash"]:
            axis.plot(
                means.index,
                means[controller],
                marker="o",
                label=controller,
            )
        axis.set(xlabel="QoE service floor", ylabel=label)
        axis.grid(alpha=0.25)
    axes[0, 0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(args.output / "target_sensitivity.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()
