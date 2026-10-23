"""Verify immutable hashes, all saved scientific rows, and physical invariants."""
from __future__ import annotations
import argparse
import csv
import gzip
import itertools
import json
import platform
from pathlib import Path
import numpy as np
from feasibility_recovery.run import (
    ROOT, DATA, fit, label_array, make_plan, simulate, summarize, read_csv,
    contrasts, progression, POLICIES, SCENARIOS, sha256,
)


def verify_hashes(base, recorded):
    for name, expected in recorded.items():
        if sha256(base / name) != expected:
            raise AssertionError(f"hash mismatch: {base / name}")


def assert_row_equal(actual, expected, ignored=()):
    if set(actual) != set(expected):
        raise AssertionError("row schema mismatch")
    for key in expected:
        if key in ignored:
            continue
        if isinstance(expected[key], (int, float, np.number)):
            if not np.isclose(float(actual[key]), expected[key], rtol=1e-10, atol=1e-9):
                raise AssertionError(f"numeric mismatch {key}: {actual[key]} != {expected[key]}")
        elif str(actual[key]) != str(expected[key]):
            raise AssertionError(f"value mismatch {key}")


def audit(data, output):
    metadata = json.loads((output / "metadata.json").read_text())
    verify_hashes(ROOT, metadata["source_sha256"])
    verify_hashes(data, metadata["input_sha256"])
    verify_hashes(output, metadata["result_sha256"])
    data_meta = json.loads((data / "metadata.json").read_text())
    verify_hashes(data, data_meta["result_sha256"])
    model = fit(data)
    saved = json.loads((output / "calibration.json").read_text())
    np.testing.assert_allclose(saved["prediction"], model["predicted"], rtol=0, atol=0)
    np.testing.assert_allclose(saved["scores"], model["scores"], rtol=0, atol=0)
    if saved["radius"] != model["radius"] or saved["split"] != model["split"]:
        raise AssertionError("calibration mismatch")
    psnr, ssim = label_array(data / "heldout_quality.csv", model["split"]["test"], model["contexts"])
    expected_plans = [make_plan(i, model["split"]["test"]) for i in range(metadata["seeds"])]
    if json.loads((output / "campaign_plan.json").read_text()) != expected_plans:
        raise AssertionError("plan differs from locked RNG/assignment")
    plans = {p["seed"]: p for p in expected_plans}
    expected_groups = {(s, scenario, policy) for s in plans for scenario in SCENARIOS for policy in POLICIES}
    seen, total, residual = set(), 0, 0.
    summaries = []
    action_sets = {}
    with gzip.open(output / "measurements.csv.gz", "rt", newline="", encoding="utf-8") as handle:
        for key, group in itertools.groupby(csv.DictReader(handle), lambda r: (int(r["seed"]), r["scenario"], r["policy"])):
            if key in seen or key not in expected_groups:
                raise AssertionError("duplicate/unexpected run")
            seen.add(key)
            rows = list(group)
            if len(rows) != 450:
                raise AssertionError("incomplete run")
            expected = simulate(model, psnr, ssim, plans[key[0]], key[2], key[1])
            for actual, replay in zip(rows, expected):
                assert_row_equal(actual, replay, ignored=("decision_ms",))
                if not np.isfinite(float(actual["decision_ms"])) or float(actual["decision_ms"]) < 0:
                    raise AssertionError("invalid runtime")
                clock_error = abs(float(actual["buffer_before_s"]) + 10 + float(actual["stall_s"])
                                  - float(actual["round_duration_s"]) - float(actual["buffer_after_s"]))
                residual = max(residual, clock_error)
                total += 1
            for t in range(90):
                block = rows[5*t:5*t+5]
                if sum(float(r["bytes"]) for r in block) > float(block[0]["budget_bytes"]) + 1e-8:
                    raise AssertionError("admission violated")
                # Feasible witness is checked independently of selected policy actions.
                witness_bytes = 0.
                for row in block:
                    context = model["contexts"].index((row["content"], int(row["segment"])))
                    a, cap = int(row["witness_action"]), int(row["observed_cap"])
                    witness_bytes += model["sizes"][context, a]
                    q = model["predicted"][context, min(a, cap)]
                    if key[1] == "prediction_shift" and 30 <= t < 60:
                        q = min(q + .6, 5)
                    if max(1, q - model["radius"]) < float(row["feasible_floor"]) - 1e-10:
                        raise AssertionError("reference has no qualifying witness")
                if witness_bytes > float(block[0]["budget_bytes"]) + 1e-8:
                    raise AssertionError("reference not jointly feasible")
            # Runtime is observational, so preserve stored values for runtime summaries.
            for replay, row in zip(expected, rows):
                replay["decision_ms"] = float(row["decision_ms"])
            summaries.append(summarize(expected, plans[key[0]]["impaired_user"]))
            action_sets[key] = np.array([r["action"] for r in expected])
    if seen != expected_groups or total != metadata["rows"] or residual > 1e-8:
        raise AssertionError("incomplete campaign or clock violation")
    saved_summaries = read_csv(output / "seed_metrics.csv")
    for a, b in zip(saved_summaries, summaries):
        assert_row_equal(a, b)
    if len(saved_summaries) != len(summaries):
        raise AssertionError("summary cardinality mismatch")
    comparisons = contrasts(summaries)
    saved_comparisons = read_csv(output / "paired_diagnostics.csv")
    if len(saved_comparisons) != len(comparisons):
        raise AssertionError("contrast cardinality mismatch")
    for a, b in zip(saved_comparisons, comparisons):
        assert_row_equal(a, b)
    passed, delta = progression(summaries, comparisons)
    if passed != metadata["progression_gate_passed"]:
        raise AssertionError("progression mismatch")
    assert_row_equal(metadata["primary_mean_deltas"], delta)
    disagreements = read_csv(output / "action_disagreements.csv")
    if len(disagreements) != len(plans) * len(SCENARIOS) * 5:
        raise AssertionError("action diagnostic cardinality mismatch")
    for r in disagreements:
        key = (int(r["seed"]), r["scenario"])
        count = np.sum(action_sets[key + ("feasible_recovery",)] != action_sets[key + (r["baseline"],)])
        if int(r["disagreements"]) != count or int(r["comparisons"]) != 450:
            raise AssertionError("action diagnostic mismatch")
    errors = np.max(np.abs(1 + 4 * np.clip((psnr - 18) / 24, 0, 1) - model["predicted"][None]), axis=(1, 2))
    panels = json.loads((output / "heldout_panel_coverage.json").read_text())
    if len(panels) != 19:
        raise AssertionError("incomplete held-out panel coverage report")
    for row, sid, error in zip(panels, model["split"]["test"], errors):
        if row != {"subject": sid, "max_error": float(error), "covered": bool(error <= model["radius"] + 1e-12)}:
            raise AssertionError("held-out coverage mismatch")
    diagnostics_verified = False
    if (output / "diagnostics/manifest.json").exists():
        figures = json.loads((output / "diagnostics/manifest.json").read_text())
        verify_hashes(output, figures["inputs"])
        verify_hashes(output / "diagnostics", figures["outputs"])
        if sha256(ROOT / "feasibility_recovery/analyze.py") != figures["analysis_source_sha256"]:
            raise AssertionError("diagnostic source mismatch")
        diagnostics_verified = True
    return {"passed": True, "scientific_rows_replayed": total, "episodes": len(seen),
            "maximum_clock_residual_s": residual, "joint_feasibility_witnesses_checked": total // 5,
            "progression_gate_passed": passed, "calibration_panels": 9, "heldout_panels": 19,
            "source_data_result_hashes_verified": True, "runtime_replayed": False,
            "diagnostics_hashes_verified": diagnostics_verified, "platform": platform.platform(),
            "python": platform.python_version(), "numpy": np.__version__,
            "audit_source_sha256": sha256(Path(__file__))}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, default=ROOT / "feasibility_recovery/results/v2")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--report-name", default="integrity_audit.json")
    args = parser.parse_args()
    if Path(args.report_name).name != args.report_name or not args.report_name.endswith(".json"):
        parser.error("report name must be a local JSON filename")
    report = audit(args.data, args.output)
    if args.save:
        with (args.output / args.report_name).open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
