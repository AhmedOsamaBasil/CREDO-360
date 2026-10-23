"""Independently check saved pilot rows, source identity and summary arithmetic."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from recovery_pilot.core import Catalogue, ObjectiveModel, shortfall
from recovery_pilot.run import summarize

ROOT = Path(__file__).resolve().parents[1]
TEXT_COLUMNS = {"scenario", "controller", "content"}
INT_COLUMNS = {"seed", "epoch", "user", "subject", "source_segment", "action", "displayed_action", "observed_cap", "actual_cap", "switched", "feasible_allocations"}


def canonical_text_hash(data: bytes) -> str:
    """Only normalize Git's CRLF/LF transport difference; no other edits."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def verify_input_bytes(data: bytes, expected: str, text_record: dict | None) -> str:
    if hashlib.sha256(data).hexdigest() == expected:
        return "byte_exact"
    if (text_record and text_record["original_raw_sha256"] == expected
            and canonical_text_hash(data) == text_record["canonical_lf_sha256"]):
        return "git_line_endings_only"
    raise AssertionError("input differs beyond recorded Git line-ending normalization")


def audit(output: Path) -> dict:
    metadata = json.loads((output / "metadata.json").read_text())
    for relative, expected in metadata["source_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, f"source changed: {relative}"
    artifact = ROOT / "multimedia_testbed/artifacts/qoevave"
    text_path = output / "input_text_hashes.json"
    text_records = json.loads(text_path.read_text()) if text_path.exists() else {}
    verification_modes = {}
    for name, expected in metadata["input_sha256"].items():
        verification_modes[name] = verify_input_bytes((artifact / name).read_bytes(), expected, text_records.get(name))
    for name, expected in metadata["result_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected, f"result changed: {name}"
    catalogue = Catalogue.load(artifact)
    model = ObjectiveModel.fit(catalogue)
    calibration = json.loads((output / "split_and_calibration.json").read_text())
    assert model.partition == calibration["partition"]
    assert np.allclose(model.mean, calibration["mean_quality_table"], rtol=0, atol=1e-12)
    assert abs(model.radius - calibration["joint_radius"]) < 1e-12
    plans = {plan["seed"]: plan for plan in json.loads((output / "campaign_plan.json").read_text())}
    contexts = {key: i for i, key in enumerate(catalogue.contexts)}
    grouped = defaultdict(list)
    max_clock_error = 0.0
    selected_coverage = defaultdict(lambda: [0, 0, 0, 0])
    seen = set()
    with gzip.open(output / "measurements.csv.gz", "rt", newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row = {key: value if key in TEXT_COLUMNS else int(value) if key in INT_COLUMNS else float(value) for key, value in raw.items()}
            key = (row["seed"], row["scenario"], row["controller"], row["epoch"], row["user"])
            assert key not in seen, f"duplicate: {key}"
            seen.add(key)
            assert row["subject"] in model.partition["test"]
            assert row["subject"] == plans[row["seed"]]["subjects"][row["user"]]
            assert row["source_segment"] == row["epoch"] % 6
            assert row["displayed_action"] == min(row["action"], row["actual_cap"])
            subject = catalogue.subjects.index(row["subject"])
            context = contexts[(row["content"], row["source_segment"])]
            expected_q = catalogue.quality[subject, context, row["displayed_action"]]
            assert abs(expected_q - row["quality"]) < 1e-12
            expected_mean = model.mean[context, min(row["action"], row["observed_cap"])]
            expected_reference_mean = model.mean[context, 0]
            if row["scenario"] == "prediction_shift" and 20 <= row["epoch"] < 40:
                expected_mean = min(5, expected_mean + 0.6)
                expected_reference_mean = min(5, expected_reference_mean + 0.6)
            expected_gain_lower = shortfall(expected_reference_mean) - shortfall(expected_mean) - model.radius
            expected_gain = shortfall(catalogue.quality[subject, context, 0]) - shortfall(expected_q)
            assert abs(expected_mean - row["mean"]) < 1e-12
            assert abs(max(1, expected_mean - model.radius) - row["lower"]) < 1e-12
            assert abs(min(5, expected_mean + model.radius) - row["upper"]) < 1e-12
            assert abs(expected_gain_lower - row["gain_lower"]) < 1e-12
            assert abs(expected_gain - row["actual_gain"]) < 1e-12
            assert abs(shortfall(expected_q) - row["shortfall"]) < 1e-12
            assert abs(max(0, 0.9 * row["debt_before"] + 4 - expected_q) - row["debt_after"]) < 1e-12
            assert row["bytes"] == catalogue.sizes[context, row["action"]]
            assert row["forecast_capacity_mbps"] == plans[row["seed"]]["capacities_mbps"][max(0, row["epoch"] - 1)]
            # Independently derive arrival/waiting accounting, not by calling the clock helper.
            arrival, end, before = row["completion_s"], row["round_duration_s"], row["buffer_before_s"]
            after_arrival = max(0, before - arrival) + 10
            expected_stall = max(0, arrival - before) + max(0, end - arrival - after_arrival)
            expected_buffer = max(0, after_arrival - (end - arrival))
            error = max(abs(row["stall_s"] - expected_stall), abs(row["buffer_after_s"] - expected_buffer),
                        abs(before + 10 + row["stall_s"] - end - row["buffer_after_s"]))
            max_clock_error = max(max_clock_error, error)
            assert error < 1e-8
            coverage = selected_coverage[(row["scenario"], row["controller"])]
            coverage[0] += row["lower"] - 1e-12 <= expected_q <= row["upper"] + 1e-12
            coverage[1] += row["actual_gain"] >= row["gain_lower"] - 1e-12
            coverage[2] += row["gain_lower"] > 0
            coverage[3] += 1
            grouped[key[:3]].append(row)
    assert len(seen) == metadata["rows"]
    assert len(grouped) == metadata["seeds"] * 4 * 8
    for key, rows in grouped.items():
        assert len(rows) == 300
        for epoch in range(60):
            block = rows[epoch * 5:(epoch + 1) * 5]
            assert sum(row["bytes"] for row in block) <= block[0]["forecast_capacity_mbps"] * 1e6 * 10 / 8 + 1e-8
            expected_end = sum(row["bytes"] for row in block) * 8 / (block[0]["capacity_mbps"] * 1e6)
            assert abs(expected_end - block[0]["round_duration_s"]) < 1e-8
            if epoch:
                for user, row in enumerate(block):
                    previous = rows[(epoch - 1) * 5 + user]
                    assert row["buffer_before_s"] == previous["buffer_after_s"]
                    assert row["debt_before"] == previous["debt_after"]
                    assert abs(row["clock_before_s"] - previous["clock_before_s"] - previous["round_duration_s"]) < 1e-8
    with (output / "seed_metrics.csv").open(encoding="utf-8") as handle:
        for stored in csv.DictReader(handle):
            key = (int(stored["seed"]), stored["scenario"], stored["controller"])
            recomputed = summarize(grouped[key], plans[key[0]]["impaired_user"])
            for field, value in recomputed.items():
                if isinstance(value, (int, float)):
                    assert abs(float(stored[field]) - value) < 1e-8, f"summary mismatch {key} {field}"
    return {
        "passed": True, "rows_checked": len(seen), "controller_seed_scenario_runs": len(grouped),
        "max_clock_conservation_error_s": max_clock_error,
        "source_input_result_hashes_verified": True, "split_and_model_recomputed": True,
        "input_verification_modes": verification_modes,
        "selected_predictions_and_direct_gain_bounds_recomputed": True,
        "all_saved_summaries_recomputed": True,
        "selected_coverage": [{"scenario": key[0], "controller": key[1], "quality_coverage": value[0] / value[3],
                               "gain_coverage": value[1] / value[3], "positive_gain_frequency": value[2] / value[3],
                               "dependent_observations": value[3]} for key, value in sorted(selected_coverage.items())],
        "caution": "An integrity audit is not evidence of benefit or novelty. Scientific progression gate is separate.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "recovery_pilot/results/v1")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--audit-name", default="integrity_audit.json")
    parser.add_argument("--record-text-hashes", action="store_true",
                        help="Record canonical text hashes only after matching the original run's raw input hashes.")
    args = parser.parse_args()
    if Path(args.audit_name).name != args.audit_name or not args.audit_name.endswith(".json"):
        parser.error("audit name must be a JSON basename")
    if args.record_text_hashes:
        metadata = json.loads((args.results / "metadata.json").read_text())
        records = {}
        for name, expected in metadata["input_sha256"].items():
            data = (ROOT / "multimedia_testbed/artifacts/qoevave" / name).read_bytes()
            assert hashlib.sha256(data).hexdigest() == expected, "raw inputs must match before recording transport hashes"
            records[name] = {"original_raw_sha256": expected, "canonical_lf_sha256": canonical_text_hash(data)}
        with (args.results / "input_text_hashes.json").open("x", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
    report = audit(args.results)
    if args.save:
        output = args.results / args.audit_name
        with output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
    print(json.dumps({key: value for key, value in report.items() if key != "selected_coverage"}, indent=2))


if __name__ == "__main__":
    main()
