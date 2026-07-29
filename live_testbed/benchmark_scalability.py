"""Benchmark the deterministic CREDO-360 action cover at journal-scale N."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import time
from pathlib import Path

import numpy as np

from portable_qoe import PortableEnsemble, select_action

try:
    import resource
except ImportError:  # Windows benchmark host
    resource = None


LADDER = np.array([0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491])


def percentile(values: list[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=float), q))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--decisions-per-seed", type=int, default=8)
    parser.add_argument("--users", nargs="+", type=int, default=[5, 10, 20, 30])
    args = parser.parse_args()

    model = PortableEnsemble(args.model)
    export_error = model.verify_export()
    template = np.asarray(
        model.payload["self_check"]["features"][0],
        dtype=float,
    )
    rows: list[dict] = []
    for users in args.users:
        for seed_offset in range(args.seeds):
            rng = np.random.default_rng(20260729 + seed_offset)
            buffer_s = rng.uniform(1.0, 12.0, users)
            previous = rng.choice(LADDER[:5], size=users)
            debt = rng.gamma(shape=2.0, scale=0.8, size=users)
            for decision in range(args.decisions_per_seed):
                throughput = rng.lognormal(mean=-0.05, sigma=0.65, size=users)
                latency = 0.04 + 0.18 / np.maximum(throughput, 0.15)
                capacity = max(
                    LADDER[0] * users,
                    float(0.75 * users + rng.uniform(-0.08, 0.08) * users),
                )
                started = time.perf_counter_ns()
                action, audit = select_action(
                    "risk_debt",
                    model,
                    template,
                    LADDER,
                    capacity,
                    throughput,
                    buffer_s,
                    previous,
                    latency,
                    debt,
                    radius=0.35,
                )
                elapsed_ms = (time.perf_counter_ns() - started) / 1e6
                rows.append(
                    {
                        "users": users,
                        "seed": 20260729 + seed_offset,
                        "decision": decision,
                        "latency_ms": elapsed_ms,
                        "candidate_count": audit["candidate_count"],
                        "capacity_mbps": capacity,
                        "allocated_mbps": float(action.sum()),
                        "feasible": int(action.sum() <= capacity + 1e-9),
                    }
                )
                previous = action
                buffer_s = np.clip(
                    buffer_s + 2.0 * throughput / np.maximum(action, 0.05) - 2.0,
                    0,
                    15,
                )

    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "scalability_decisions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = []
    for users in args.users:
        group = [row for row in rows if row["users"] == users]
        timings = [row["latency_ms"] for row in group]
        summary.append(
            {
                "users": users,
                "decisions": len(group),
                "candidate_count_median": percentile(
                    [row["candidate_count"] for row in group], 50
                ),
                "latency_median_ms": percentile(timings, 50),
                "latency_p95_ms": percentile(timings, 95),
                "latency_p99_ms": percentile(timings, 99),
                "feasibility_violations": sum(not row["feasible"] for row in group),
            }
        )
    with (args.output / "scalability_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    metadata = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "portable_export_max_abs_error": export_error,
        "max_rss_native_units": (
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if resource is not None
            else None
        ),
        "scope": (
            "Controller-side NumPy inference and deterministic candidate-cover "
            "benchmark; this is not a network or subjective-QoE result."
        ),
    }
    (args.output / "scalability_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"summary": summary, "metadata": metadata}, indent=2))


if __name__ == "__main__":
    main()
