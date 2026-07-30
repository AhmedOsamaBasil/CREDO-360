"""Create the TMM controller-scalability figure from frozen raw outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frame = pd.read_csv(args.summary)
    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axis = plt.subplots(figsize=(6.4, 3.8))
    axis.plot(
        frame["users"],
        frame["latency_median_ms"],
        marker="o",
        linewidth=2,
        label="Median",
    )
    axis.plot(
        frame["users"],
        frame["latency_p95_ms"],
        marker="s",
        linewidth=2,
        label="95th percentile",
    )
    axis.plot(
        frame["users"],
        frame["latency_p99_ms"],
        marker="^",
        linewidth=2,
        label="99th percentile",
    )
    axis.axhline(1000, color="black", linestyle="--", linewidth=1, label="1 s")
    axis.set(
        xlabel="Concurrent users",
        ylabel="Controller decision latency (ms)",
        xticks=frame["users"],
        ylim=(0, 1050),
    )
    axis.legend(frameon=True, ncol=2)
    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=220)


if __name__ == "__main__":
    main()
