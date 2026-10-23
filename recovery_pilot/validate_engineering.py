"""Verify cross-platform scientific replication and the live timing smoke test."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def raw_rows(path: Path, seed: int) -> list[dict]:
    with gzip.open(path / "measurements.csv.gz", "rt", newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if int(row["seed"]) == seed]


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "recovery_pilot/results/v1")
    parser.add_argument("--replica", type=Path, default=ROOT / "work/recovery_repro_linux_seed1")
    parser.add_argument("--live", type=Path, default=ROOT / "recovery_pilot/results/live_clock_smoke_v1")
    args = parser.parse_args()
    first, second = raw_rows(args.results, 202610230), raw_rows(args.replica, 202610230)
    assert len(first) == len(second) == 4 * 8 * 60 * 5
    largest = 0.0
    for left, right in zip(first, second):
        assert left.keys() == right.keys()
        for key in left:
            if key == "decision_ms":
                continue
            if key in {"scenario", "controller", "content"}:
                assert left[key] == right[key]
            else:
                difference = abs(float(left[key]) - float(right[key]))
                largest = max(largest, difference)
                assert difference < 1e-10, (key, left[key], right[key])
    with (args.live / "live_measurements.csv").open(encoding="utf-8") as handle:
        live = list(csv.DictReader(handle))
    assert len(live) == 6
    max_error, max_wait = 0.0, 0.0
    buffers = {}
    for row in live:
        assert row["playback_clock_version"] == "2"
        before, after = float(row["buffer_before_s"]), float(row["buffer_after_s"])
        elapsed, arrival = float(row["epoch_wall_s"]), float(row["completion_since_boundary_s"])
        stall, censored = float(row["stall_s"]), int(row["transfer_censored"])
        assert 0 <= arrival <= elapsed
        at_arrival = max(0, before - arrival) + 10 * (1 - censored)
        expected_after = max(0, at_arrival - (elapsed - arrival))
        expected_stall = max(0, arrival - before) + max(0, elapsed - arrival - at_arrival)
        error = max(abs(expected_after - after), abs(expected_stall - stall),
                    abs(before + 10 * (1 - censored) + stall - elapsed - after))
        max_error, max_wait = max(max_error, error), max(max_wait, elapsed - arrival)
        assert error < 1e-9
        if row["user"] in buffers:
            assert abs(before - buffers[row["user"]]) < 1e-9
        buffers[row["user"]] = after
    report = {
        "cross_platform_passed": True, "replicated_seed": 202610230,
        "replicated_rows": len(first), "max_scientific_field_difference": largest,
        "runtime_excluded_from_comparison": True,
        "replica_metadata": json.loads((args.replica / "metadata.json").read_text()),
        "live_clock_smoke_passed": True, "live_rows": len(live),
        "live_max_clock_error_s": max_error, "live_max_post_completion_wait_s": max_wait,
        "live_measurements_sha256": hashlib.sha256((args.live / "live_measurements.csv").read_bytes()).hexdigest(),
        "limitations": "One-seed replication checks determinism, not efficacy. Two-client/three-round Big Buck Bunny Mininet smoke checks timing, not immersive recovery performance.",
    }
    with (args.results / "engineering_validation.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({key: value for key, value in report.items() if key != "replica_metadata"}, indent=2))


if __name__ == "__main__":
    main()
