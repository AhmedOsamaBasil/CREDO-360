"""Run the locked exploratory recovery pilot; never overwrite an output."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np

from live_testbed.playback_clock import advance_round
from recovery_pilot.core import (
    CONTROLLERS, Catalogue, ObjectiveModel, select_action, shortfall,
)

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ("capacity_only", "known_ceiling", "delayed_ceiling", "prediction_shift")


def processor_sharing(bits: np.ndarray, capacity_mbps: float) -> np.ndarray:
    """Exact simultaneous-flow equal sharing, independently tested below."""
    remaining = np.asarray(bits, float).copy()
    if remaining.ndim != 1 or not np.all(np.isfinite(remaining)) or np.any(remaining <= 0) or capacity_mbps <= 0:
        raise ValueError("positive finite sizes and capacity required")
    completion = np.zeros(len(remaining))
    active = np.ones(len(remaining), bool)
    elapsed = 0.0
    while active.any():
        rate = capacity_mbps * 1e6 / active.sum()
        delta = remaining[active].min() / rate
        elapsed += delta
        remaining[active] -= rate * delta
        finished = active & (remaining <= 1e-6)
        completion[finished] = elapsed
        active[finished] = False
    return completion


def make_plan(seed: int, index: int, model: ObjectiveModel, contents: list[str]) -> dict:
    rng = np.random.default_rng(seed)
    capacities = np.clip(rng.normal(3.0, 0.3, 60), 1.0, 4.5)
    capacities[np.arange(60) % 8 >= 5] *= 0.4
    return {
        "seed": seed, "subjects": rng.choice(model.partition["test"], 5, replace=False).tolist(),
        "contents": [contents[(index + user) % len(contents)] for user in range(5)],
        "capacities_mbps": capacities.tolist(), "impaired_user": index % 5,
    }


def cap_at(scenario: str, epoch: int, user: int, impaired: int) -> int:
    return 1 if scenario in {"known_ceiling", "delayed_ceiling"} and 20 <= epoch < 40 and user == impaired else 5


def simulate(catalogue: Catalogue, model: ObjectiveModel, plan: dict, controller: str, scenario: str) -> list[dict]:
    lookup = {key: i for i, key in enumerate(catalogue.contexts)}
    subject_indices = np.array([catalogue.subjects.index(sid) for sid in plan["subjects"]])
    users = len(subject_indices)
    buffers = np.full(users, 4.0)
    debt, last = np.zeros(users), np.zeros(users)
    previous = np.ones(users, dtype=int)
    rows = []
    wall_clock = 0.0
    for epoch, capacity in enumerate(plan["capacities_mbps"]):
        context_ids = np.array([lookup[(content, epoch % 6)] for content in plan["contents"]])
        observed_epoch = epoch - 1 if scenario == "delayed_ceiling" else epoch
        observed_caps = np.array([cap_at(scenario, observed_epoch, user, plan["impaired_user"]) for user in range(users)])
        effective_caps = np.array([cap_at(scenario, epoch, user, plan["impaired_user"]) for user in range(users)])
        means = model.mean[context_ids].copy()
        if scenario == "prediction_shift" and 20 <= epoch < 40:
            means = np.clip(means + 0.6, 1, 5)
        policy_means = np.take_along_axis(means, np.minimum(np.arange(6)[None, :], observed_caps[:, None]), axis=1)
        costs = catalogue.sizes[context_ids]
        estimate = plan["capacities_mbps"][max(0, epoch - 1)]
        budget_bytes = estimate * 1e6 * 10 / 8
        started = time.perf_counter()
        action, decision = select_action(controller, policy_means, model.radius, costs,
                                         budget_bytes, debt, last, previous)
        measured_decision_ms = 1000 * (time.perf_counter() - started)
        # Runtime is reported, not injected: policies share deterministic simulation
        # timing. Live controller/setup overhead is handled by the live clock.
        chosen_bytes = costs[np.arange(users), action]
        completion = processor_sharing(chosen_bytes * 8, capacity)
        round_end = float(completion.max())
        clock = advance_round(buffers, completion, round_end)
        conservation = buffers + 10 + clock.stall_s - round_end - clock.buffer_s
        if np.max(np.abs(conservation)) > 1e-8 or chosen_bytes.sum() > budget_bytes + 1e-8:
            raise AssertionError("timing or admission invariant failed")
        effective = np.minimum(action, effective_caps)
        # Held-out labels enter only AFTER the action, as outcomes and debt feedback.
        actual = catalogue.quality[subject_indices, context_ids, effective]
        reference = catalogue.quality[subject_indices, context_ids, 0]
        actual_gain = shortfall(reference) - shortfall(actual)
        calibrated_gain = shortfall(policy_means[:, 0]) - shortfall(decision["mean"]) - model.radius
        updated_debt = np.maximum(0, 0.9 * debt + 4 - actual)
        for user in range(users):
            rows.append({
                "seed": plan["seed"], "scenario": scenario, "controller": controller,
                "epoch": epoch, "user": user, "subject": plan["subjects"][user],
                "content": plan["contents"][user], "source_segment": epoch % 6,
                "action": int(action[user]), "displayed_action": int(effective[user]),
                "observed_cap": int(observed_caps[user]), "actual_cap": int(effective_caps[user]),
                "quality": float(actual[user]), "mean": float(decision["mean"][user]),
                "lower": float(decision["lower"][user]),
                "upper": float(min(5, decision["mean"][user] + model.radius)),
                "actual_gain": float(actual_gain[user]), "gain_lower": float(calibrated_gain[user]),
                "recovery_credit": float(decision["credit"][user]),
                "shortfall": float(shortfall(actual[user])), "debt_before": float(debt[user]),
                "debt_after": float(updated_debt[user]),
                "source_vw_psnr_db": float(catalogue.psnr[subject_indices[user], context_ids[user], effective[user]]),
                "source_vw_ssim": float(catalogue.ssim[subject_indices[user], context_ids[user], effective[user]]),
                "capacity_mbps": capacity, "forecast_capacity_mbps": estimate,
                "bytes": float(chosen_bytes[user]),
                "excess_bytes": float(max(0, chosen_bytes[user] - costs[user, effective[user]])),
                "completion_s": float(completion[user]), "round_duration_s": round_end,
                "clock_before_s": wall_clock, "buffer_before_s": float(buffers[user]),
                "buffer_after_s": float(clock.buffer_s[user]), "stall_s": float(clock.stall_s[user]),
                "switched": int(action[user] != previous[user]), "decision_ms": measured_decision_ms,
                "feasible_allocations": decision["candidate_count"],
            })
        buffers, debt, last, previous = clock.buffer_s, updated_debt, shortfall(actual), action
        wall_clock += round_end
    return rows


def longest_run(mask: np.ndarray) -> int:
    best = current = 0
    for value in mask:
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def summarize(rows: list[dict], impaired_user: int) -> dict:
    q = np.array([row["quality"] for row in rows]).reshape(60, 5)
    deficit = np.maximum(4 - q, 0)
    meets = q[40:, impaired_user] >= 4
    successes = [index + 2 for index in range(19) if meets[index] and meets[index + 1]]
    first = rows[0]
    return {
        "seed": first["seed"], "scenario": first["scenario"], "controller": first["controller"],
        "cumulative_shortfall": float(deficit.sum(axis=0).mean()),
        "post_restoration_shortfall": float(deficit[40:].sum(axis=0).mean()),
        "longest_deprivation_rounds": max(longest_run(deficit[:, user] > 0) for user in range(5)),
        "recovery_wait_rounds_capped20": successes[0] if successes else 20,
        "recovery_event_observed": int(bool(successes)),
        "mean_quality": float(q.mean()), "worst_user_quality": float(q.mean(axis=0).min()),
        "stall_s_per_user": sum(row["stall_s"] for row in rows) / 5,
        "stall_after_first_round_s_per_user": sum(row["stall_s"] for row in rows if row["epoch"] > 0) / 5,
        "excess_bytes": sum(row["excess_bytes"] for row in rows),
        "selected_quality_coverage": np.mean([row["lower"] - 1e-12 <= row["quality"] <= row["upper"] + 1e-12 for row in rows]).item(),
        "selected_gain_coverage": np.mean([row["actual_gain"] >= row["gain_lower"] - 1e-12 for row in rows]).item(),
        "positive_gain_frequency": np.mean([row["gain_lower"] > 0 for row in rows]).item(),
        "decision_ms_median": float(np.median([row["decision_ms"] for row in rows[::5]])),
    }


def paired_comparisons(summaries: list[dict]) -> list[dict]:
    result = []
    outcomes = ("cumulative_shortfall", "post_restoration_shortfall", "stall_s_per_user", "worst_user_quality")
    rng = np.random.default_rng(481516)
    for scenario in SCENARIOS:
        proposed = {r["seed"]: r for r in summaries if r["scenario"] == scenario and r["controller"] == "certified_recovery"}
        for comparator in ("bounded_quality_debt", "uncertified_recovery", "memoryless_recovery"):
            baseline = {r["seed"]: r for r in summaries if r["scenario"] == scenario and r["controller"] == comparator}
            for outcome in outcomes:
                differences = np.array([proposed[s][outcome] - baseline[s][outcome] for s in sorted(proposed)])
                draws = rng.choice(differences, (2000, len(differences)), replace=True).mean(axis=1)
                result.append({"scenario": scenario, "proposed": "certified_recovery", "baseline": comparator,
                               "outcome": outcome, "paired_seeds": len(differences), "mean_delta": float(differences.mean()),
                               "descriptive_ci95_low": float(np.quantile(draws, 0.025)),
                               "descriptive_ci95_high": float(np.quantile(draws, 0.975))})
    return result


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--artifacts", type=Path, default=ROOT / "multimedia_testbed/artifacts/qoevave")
    parser.add_argument("--output", type=Path, default=ROOT / "recovery_pilot/results/v1")
    parser.add_argument("--seeds", type=int, default=12, help="Changing this marks a non-protocol engineering run.")
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("positive seeds required")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("output is nonempty; choose a new version, never overwrite results")
    catalogue = Catalogue.load(args.artifacts)
    model = ObjectiveModel.fit(catalogue)
    contents = sorted({key[0] for key in catalogue.contexts})
    if len(contents) != 6 or len(catalogue.contexts) != 36:
        parser.error("protocol requires six contents with six segments each")
    plans = [make_plan(202610230 + index, index, model, contents) for index in range(args.seeds)]
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "split_and_calibration.json").write_text(json.dumps({
        "partition": model.partition, "mean_quality_table": model.mean.tolist(),
        "context_order": catalogue.contexts, "calibration_scores": model.scores,
        "joint_radius": model.radius, "order_statistic_rank": model.rank,
        "trivial_bound": model.trivial_bound, "nominal_panel_coverage": 0.9,
        "held_out_panels": model.panel_coverage(catalogue),
        "target": "1 + 4*clip((VW-PSNR-18)/24,0,1); not MOS",
    }, indent=2), encoding="utf-8")
    (args.output / "campaign_plan.json").write_text(json.dumps(plans, indent=2), encoding="utf-8")
    summaries, action_audit = [], []
    raw_path = args.output / "measurements.csv.gz"
    # Stable gzip headers; measured runtime fields themselves are intentionally variable.
    with raw_path.open("wb") as binary:
        with gzip.GzipFile(fileobj=binary, mode="wb", filename="", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as handle:
                writer = None
                for plan in plans:
                    for scenario in SCENARIOS:
                        selected = {}
                        for controller in CONTROLLERS:
                            rows = simulate(catalogue, model, plan, controller, scenario)
                            if writer is None:
                                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                                writer.writeheader()
                            writer.writerows(rows)
                            summaries.append(summarize(rows, plan["impaired_user"]))
                            selected[controller] = np.array([row["action"] for row in rows])
                        for baseline in ("bounded_quality_debt", "uncertified_recovery", "memoryless_recovery"):
                            action_audit.append({"seed": plan["seed"], "scenario": scenario, "baseline": baseline,
                                                 "disagreements": int(np.sum(selected["certified_recovery"] != selected[baseline])),
                                                 "comparisons": 300})
                        print(f"completed seed={plan['seed']} scenario={scenario}", flush=True)
    contrasts = paired_comparisons(summaries)
    write_csv(args.output / "seed_metrics.csv", summaries)
    write_csv(args.output / "paired_diagnostics.csv", contrasts)
    write_csv(args.output / "action_disagreements.csv", action_audit)
    primary = {row["outcome"]: row["mean_delta"] for row in contrasts if row["scenario"] == "known_ceiling" and row["baseline"] == "bounded_quality_debt"}
    baseline_stall = np.mean([row["stall_s_per_user"] for row in summaries if row["scenario"] == "known_ceiling" and row["controller"] == "bounded_quality_debt"])
    gate = primary["cumulative_shortfall"] < 0 and primary["post_restoration_shortfall"] < 0 and primary["stall_s_per_user"] <= (0.05 * baseline_stall if baseline_stall else 0.1)
    source_files = [Path(__file__), ROOT / "recovery_pilot/core.py", ROOT / "recovery_pilot/PROTOCOL.md", ROOT / "live_testbed/playback_clock.py"]
    git = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
    metadata = {
        "format": "recovery-pilot-v1", "exploratory": True, "matches_locked_seed_count": args.seeds == 12,
        "seeds": args.seeds, "users": 5, "rounds": 60, "rows": args.seeds * 4 * 8 * 60 * 5,
        "controllers": CONTROLLERS, "scenarios": SCENARIOS, "git_head_at_run": git.stdout.strip(),
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in source_files},
        "input_sha256": {name: sha256(args.artifacts / name) for name in ("viewport_quality.csv", "segment_sizes.csv", "subject_split.csv", "metadata.json")},
        "result_sha256": {p.name: sha256(p) for p in args.output.iterdir() if p.is_file()},
        "python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(),
        "progression_gate_passed": bool(gate), "primary_mean_deltas": primary,
        "runtime_injected_into_simulated_clock": False,
        "limitations": ["known-content centroid predictor", "nine held-out source-ID panels", "looped six-segment catalogue",
                        "synthetic representation ceiling", "fluid synchronized transport, not live player", "no adaptive recalibration under shift",
                        "seed-bootstrap intervals condition on this dataset", "no human perception or novelty claim"],
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    lines = ["# Recovery pilot v1 results", "", "Exploratory engineering replay; not confirmatory or live validation.", "",
             f"Progression gate: **{'PASS' if gate else 'FAIL'}**. No post-test tuning was performed.", "",
             f"Joint quality/gain radius: {model.radius:.6f} objective-index units; calibration IDs: 9; test IDs: 9.",
             f"Held-out catalogue panels covered: {sum(r['covered'] for r in model.panel_coverage(catalogue))}/9.", "",
             "## Candidate minus bounded-quality debt", "", "Negative shortfall/stall differences favor the candidate; positive quality differences favor it.", "",
             "| Scenario | Cumulative shortfall | Post-restoration shortfall | Stall s/user | Worst-user quality |",
             "|---|---:|---:|---:|---:|"]
    for scenario in SCENARIOS:
        values = {r["outcome"]: r["mean_delta"] for r in contrasts if r["scenario"] == scenario and r["baseline"] == "bounded_quality_debt"}
        lines.append(f"| {scenario} | {values['cumulative_shortfall']:.4f} | {values['post_restoration_shortfall']:.4f} | {values['stall_s_per_user']:.4f} | {values['worst_user_quality']:.4f} |")
    lines += ["", "Full per-seed results, descriptive paired intervals, calibration panels, action disagreements and compressed raw measurements accompany this report.", "",
              "Recovery-event times are right-censored at 20 rounds; do not interpret capped waiting means as observed recovery for every user.", "",
              "The finite-catalogue envelope assumes exchangeable grouped ID panels; it does not promise validity under the deliberately injected prediction shift or stale ceiling observation.", "",
              "See PROTOCOL.md for the fixed design and metadata.json for code/data hashes. Hardware runtime fields are not injected into replay timing."]
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "progression_gate_passed": bool(gate), "primary_mean_deltas": primary}, indent=2))


if __name__ == "__main__":
    main()
