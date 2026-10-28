"""Bind a descriptive claim register to existing results, without rerunning policies."""
import argparse
import gzip
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "measurement_assessment/results/assessment_v1"
INPUTS = {
    "early": "early_commitment/results/development_v1/results.json.gz",
    "frontier": "feasibility_frontier/results/audit_v1/results.json.gz",
    "reserve": "reserve_recovery/results/analysis_v1/results.json.gz",
    "opportunity": "feedback_opportunity/results/audit_v1/results.json.gz",
    "feedback": "feedback_opportunity/results/diagnostics_v1/results.json",
    "live": "causal_playback/results/diagnostics_v1/diagnostics.json",
    "service": "service_opportunity/results/service_v1.json",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def load_inputs(root=ROOT):
    result = {}
    for name, relative in INPUTS.items():
        path = root / relative
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                result[name] = json.load(stream)
        else:
            result[name] = json.loads(path.read_text(encoding="utf-8"))
    return result


def policy_summary(rows):
    """Episode-weighted descriptive means, not independent-person estimates."""
    if not rows or len({r["key"] for r in rows}) != len(rows):
        raise ValueError("Empty or duplicate episode keys within a policy cell")
    return {
        "episodes": len(rows),
        "half_repaid": sum(r["half_repaid"] for r in rows),
        **{k: mean(r[k] for r in rows) for k in (
            "unpaid_fraction", "worst_quality", "mean_stall_seconds", "current_mae")},
        **{k: sum(r[k] for r in rows) for k in (
            "donor_floor_violations", "recipient_floor_violations")},
    }


def check_summary(actual, saved):
    for key, value in actual.items():
        if not math.isclose(value, saved[key], rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"Frozen summary disagrees with rows: {key}")


def synthesize(inputs):
    early = inputs["early"]
    if early["fresh_holdout_used"] or not early["exposed_only"]:
        raise ValueError("This register is restricted to the exposed study")
    rows = early["rows"]
    if len(rows) != 1512:
        raise ValueError("Incomplete fixed early-commitment batch")
    cells = {}
    expected = {(r["policy"], r["delay"]) for r in early["summary"]["all"]}
    if len(expected) != 9 or {(r["policy"], r["delay"]) for r in rows} != expected:
        raise ValueError("Policy/delay cells differ from frozen protocol")
    for group in ("all", "v2", "v3"):
        cells[group] = {}
        for policy, delay in sorted(expected):
            selected = [r for r in rows if r["policy"] == policy and r["delay"] == delay
                        and group in ("all", r["cohort"])]
            summary = policy_summary(selected)
            if summary["episodes"] != (168 if group == "all" else 84):
                raise ValueError("Incomplete cohort/policy cell")
            saved = next(r for r in early["summary"][group]
                         if r["policy"] == policy and r["delay"] == delay)
            check_summary(summary, saved)
            cells[group][f"{policy}@{delay:g}s"] = summary
    episode_keys = {r["key"] for r in rows}
    scenes = sorted({r["scene"] for r in rows})
    identities = {identity for key in episode_keys for identity in key.split(":")[-2:]}
    contrasts = {}
    for group, cell in cells.items():
        primary = cell["prefix_mpc@0.08s"]
        completed = cell["completed_mpc@0.08s"]
        greedy = cell["prefix_cost_greedy@0.08s"]
        contrasts[group] = {
            "unpaid_reduction_vs_completed": completed["unpaid_fraction"] - primary["unpaid_fraction"],
            "unpaid_increase_vs_cost_greedy": primary["unpaid_fraction"] - greedy["unpaid_fraction"],
            "wait_added_stall_vs_completed_seconds":
                cell["wait_mpc@0.08s"]["mean_stall_seconds"] - completed["mean_stall_seconds"],
            "worst_quality_delta_vs_nash": primary["worst_quality"] - cell["prefix_nash@0.08s"]["worst_quality"],
        }
    frontier = inputs["frontier"]["summary"]["all"]
    no_loss = next(p["requirements"] for p in frontier["profiles"]
                   if p["name"] == "no_donor_loss")
    reserve = inputs["reserve"]["catalogue"]["summary"]["all"]
    reserve_cells = [{**{k: r[k] for k in ("peak", "policy", "reserve_fraction", "half_repaid")},
                      "mean_worst_quality": float(Fraction(r["mean_worst_quality"]))}
                     for r in reserve["cells"]
                     if r["peak"] in ("3", "4") and r["reserve_fraction"] == "1"]
    live = inputs["live"]["live_summary"]
    measured = {}
    for label, rate in (("nominal", 1500), ("stress", 750)):
        subset = [r for r in live if r["rate_kbit"] == rate]
        measured[label] = {
            "episodes": sum(r["episodes"] for r in subset),
            "decisions": sum(r["rounds"] for r in subset),
            "deadline_misses": sum(r["deadline_misses"] for r in subset),
            "maximum_receipt_latency_seconds": max(r["max_latency"] for r in subset),
        }
    return {
        "assessment_date": "2026-10-28",
        "analysis_type": "posthoc descriptive synthesis of frozen artifacts; no new experiment",
        "source_json_sha256": {INPUTS[k]: hashlib.sha256(canonical(v)).hexdigest()
                               for k, v in inputs.items()},
        "source_hash_definition": "SHA256 of decoded canonical JSON, not compressed file bytes",
        "sampling": {"reused_episode_keys": len(episode_keys), "scenes": scenes,
                     "reused_participant_identifiers": len(identities),
                     "early_policy_runs": len(rows),
                     "independence_warning": "Directed pairs share people and content; runs are not independent participants."},
        "relative_payload_frontier_no_cumulative_reserve": {
            "no_donor_loss": no_loss,
            "largest_half_count_at_2x_across_all_donor_slices":
                max(r["counts_by_multiplier"]["2"] for r in frontier["requirements"]),
            "scope": "Future-known four-segment encoded-payload contract; not measured path capacity."},
        "finite_payload_reserve": {"rho1_peak3_and4": reserve_cells,
            "field_available_capacity_identified": inputs["reserve"]["evidence"]["capacity_availability_identified"]},
        "fixed_file_cap_offline_opportunity": inputs["opportunity"]["opportunity_summary"]["all"],
        "completed_feedback_loopback": inputs["feedback"]["wire_feedback"],
        "feedback_action_disagreements": inputs["feedback"]["corrected_action_disagreements"],
        "controlled_service": inputs["service"]["validation"],
        "selected_transfer_receipts": measured,
        "simulated_prefix_playback": {"cells": cells, "contrasts": contrasts,
            "frozen_screen_passed": early["screen"]["passed"],
            "scope": early["timing"]},
        "interpretation": {"superior_recovery_controller_established": False,
                           "human_qoe_validated": False,
                           "field_deployment_validated": False,
                           "resubmission_ready_by_reframing_alone": False},
    }


def report(result):
    rows = result["simulated_prefix_playback"]["cells"]["all"]
    lines = ["# Frozen-evidence synthesis", "",
             "Post-hoc descriptive aggregation; no new simulation or statistical test.", "",
             "## Matched prefix-playback comparison (simulation)", "",
             "| Policy | Half / episodes | Mean unpaid | Worst quality | Stall s |",
             "|---|---:|---:|---:|---:|"]
    for key in ("prefix_cost_greedy@0.08s", "completed_mpc@0.08s", "prefix_mpc@0.08s", "wait_mpc@0.08s"):
        r = rows[key]
        lines.append(f"| {key} | {r['half_repaid']}/{r['episodes']} | {r['unpaid_fraction']:.6f} | "
                     f"{r['worst_quality']:.6f} | {r['mean_stall_seconds']:.6f} |")
    lines += ["", "The frozen progression screen remains FAILED. Lower unpaid is better.",
              "Half-repayment is the declared accounting target, not a perceptual threshold.", "",
              "## Evidence boundaries", "",
              "- 168 reused directed episodes, six scenes, 28 participant identifiers; 1,512 policy runs are not independent subjects.",
              "- Relative encoded-payload frontiers and fixed actual-file-cap bounds are different contracts.",
              "- TCP receipts and completed-feedback loopback are measurements; incremental feedback/playback is simulated.",
              "- Frozen inputs are bound by canonical decoded-JSON hashes in summary.json.",
              "- This verifier checks extraction and aggregation, not every original optimizer; each source retains its own replay/audit.",
              "- See ../../README.md, ../../RELATED_WORK.md and ../../VALIDATION_PLAN.md for the assessment.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--build", action="store_true", help="Create a new result directory; never overwrite")
    args = parser.parse_args()
    result = synthesize(load_inputs())
    rendered = report(result)
    if args.build:
        OUT.mkdir(parents=True, exist_ok=False)
        (OUT / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (OUT / "REPORT.md").write_text(rendered, encoding="utf-8")
    else:
        if json.loads((OUT / "summary.json").read_text(encoding="utf-8")) != result:
            raise ValueError("Published synthesis differs from frozen inputs")
        if (OUT / "REPORT.md").read_text(encoding="utf-8") != rendered:
            raise ValueError("Published report differs from regenerated text")
    print(json.dumps({"verified": not args.build, "built": args.build,
                      "synthesis_sha256": hashlib.sha256(canonical(result)).hexdigest(),
                      "new_experiments": 0, "controller_screen_passed": result["simulated_prefix_playback"]["frozen_screen_passed"]}))


if __name__ == "__main__":
    main()
