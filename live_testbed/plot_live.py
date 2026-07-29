"""Create controller-comparison figures from the live segment log."""

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
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.input.parent / "live_controller_comparison.png"
    frame = pd.read_csv(args.input)
    colors = {"conformal_nash": "#315A91", "risk_debt": "#C84C39"}

    figure, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for controller, group in frame.groupby("controller"):
        epoch = group.groupby("epoch")
        mean = epoch["operational_qoe"].mean()
        minimum = epoch["operational_qoe"].min()
        axes[0].plot(
            mean.index,
            mean.values,
            marker="o",
            color=colors.get(controller),
            label=f"{controller}: mean",
        )
        axes[0].plot(
            minimum.index,
            minimum.values,
            linestyle="--",
            marker=".",
            color=colors.get(controller),
            alpha=0.75,
            label=f"{controller}: epoch minimum",
        )
        allocated = epoch["allocated_mbps"].sum()
        axes[1].plot(
            allocated.index,
            allocated.values,
            marker="o",
            color=colors.get(controller),
            label=controller,
        )
    capacity = frame.groupby("epoch")["capacity_mbps"].first()
    axes[0].axhline(4.0, color="black", linestyle=":", label="service floor")
    axes[0].set_ylabel("Operational QoE")
    axes[0].set_ylim(1, 5.1)
    axes[0].grid(alpha=0.25)
    axes[0].legend(ncol=2, fontsize=8)
    axes[1].plot(
        capacity.index,
        capacity.values,
        color="black",
        linestyle=":",
        marker="x",
        label="shared capacity",
    )
    axes[1].set_ylabel("Aggregate allocation (Mb/s)")
    axes[1].set_xlabel("Segment epoch")
    axes[1].grid(alpha=0.25)
    axes[1].legend(ncol=3, fontsize=8)
    figure.suptitle("Live Mininet DASH experiment: measured shared bottleneck")
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    print(output)


if __name__ == "__main__":
    main()
