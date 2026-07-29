"""Summarize paired live Mininet controller measurements."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def mean(values):
    return sum(values) / len(values) if values else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.input.parent / "live_summary.json"
    with args.input.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    metadata_path = args.input.parent / "run_metadata.json"
    metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.exists()
        else {}
    )
    target = float(metadata.get("target_operational_qoe", 4.0))
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["controller"]].append(row)
    summary = {}
    for controller, data in grouped.items():
        users = defaultdict(list)
        for row in data:
            users[int(row["user"])].append(float(row["operational_qoe"]))
        user_means = [mean(values) for values in users.values()]
        jain = sum(user_means) ** 2 / (
            len(user_means) * sum(value * value for value in user_means)
        )
        total_stall = sum(float(row["stall_s"]) for row in data)
        epoch_allocations = defaultdict(list)
        for row in data:
            epoch_allocations[int(row["epoch"])].append(row)
        maximum_capacity_excess = max(
            sum(float(row["allocated_mbps"]) for row in epoch_rows)
            - float(epoch_rows[0]["capacity_mbps"])
            for epoch_rows in epoch_allocations.values()
        )
        qoe_values = [float(row["operational_qoe"]) for row in data]
        summary[controller] = {
            "measurements": len(data),
            "mean_operational_qoe": mean(qoe_values),
            "worst_user_mean_operational_qoe": min(user_means),
            "jain_user_mean_operational_qoe": jain,
            "service_floor": target,
            "service_violation_rate": mean([value < target for value in qoe_values]),
            "mean_service_shortfall": mean(
                [max(target - value, 0) for value in qoe_values]
            ),
            "mean_throughput_mbps": mean(
                [float(row["throughput_mbps"]) for row in data]
            ),
            "total_stall_s": total_stall,
            "switch_rate": mean([float(row["switched"]) for row in data]),
            "mean_debt_after": mean([float(row["debt_after"]) for row in data]),
            "mean_epoch_wall_s": mean(
                [float(row["epoch_wall_s"]) for row in data]
            ),
            "maximum_allocation_capacity_excess_mbps": maximum_capacity_excess,
        }
    if "conformal_nash" in summary and "risk_debt" in summary:
        baseline = summary["conformal_nash"]
        proposed = summary["risk_debt"]
        summary["paired_delta_risk_debt_minus_conformal_nash"] = {
            metric: proposed[metric] - baseline[metric]
            for metric in [
                "mean_operational_qoe",
                "worst_user_mean_operational_qoe",
                "jain_user_mean_operational_qoe",
                "service_violation_rate",
                "mean_service_shortfall",
                "total_stall_s",
                "switch_rate",
                "mean_debt_after",
            ]
        }
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
