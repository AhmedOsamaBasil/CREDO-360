"""Locked v2 campaign. Calibration is fitted before loading held-out outcomes."""
from __future__ import annotations
import argparse
import csv
import gzip
import io
import json
import platform
import subprocess
import time
from pathlib import Path
import numpy as np
from feasibility_recovery.core import POLICIES, partition, quality_radius, select_action, update_debt
from recovery_pilot.core import quality_index
from recovery_pilot.run import processor_sharing, longest_run, sha256, write_csv
from live_testbed.playback_clock import advance_round

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "feasibility_recovery/data/v2"
SCENARIOS = ("capacity_only", "known_ceiling", "delayed_ceiling", "prediction_shift")
OUTCOMES = ("cumulative_shortfall", "post_restoration_shortfall", "stall_s_per_user",
            "worst_user_quality", "impaired_restoration_shortfall", "mean_quality")
SOURCES = ("feasibility_recovery/core.py", "feasibility_recovery/run.py", "feasibility_recovery/PROTOCOL.md",
           "recovery_pilot/core.py", "recovery_pilot/run.py", "live_testbed/playback_clock.py")


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def label_array(path, subjects, contexts):
    psnr = np.full((len(subjects), len(contexts), 6), np.nan)
    ssim = psnr.copy()
    for row in read_csv(path):
        key = (subjects.index(int(row["subject"])), contexts.index((row["content"], int(row["segment"]))), int(row["ladder_index"]))
        if np.isfinite(psnr[key]):
            raise ValueError("duplicate label key")
        psnr[key], ssim[key] = float(row["vw_psnr_db"]), float(row["vw_ssim"])
    if not np.isfinite(psnr).all() or not np.isfinite(ssim).all():
        raise ValueError("incomplete or invalid label panels")
    return psnr, ssim


def fit(data):
    """This function never opens heldout_quality.csv."""
    split = json.loads((data / "split.json").read_text())
    if split != partition(split["calibration"] + split["test"]):
        raise ValueError("split differs from frozen protocol")
    rows = read_csv(data / "sender_quality.csv")
    contexts = sorted({(r["content"], int(r["segment"])) for r in rows})
    if len(contexts) != 18 or sorted(set(k[0] for k in contexts)) != ["ParkFountains01", "River01", "Train01"]:
        raise ValueError("unexpected fresh content catalogue")
    predicted, sizes = np.full((18, 6), np.nan), np.full((18, 6), np.nan)
    for row in rows:
        key = (contexts.index((row["content"], int(row["segment"]))), int(row["ladder_index"]))
        if np.isfinite(predicted[key]):
            raise ValueError("duplicate sender key")
        predicted[key] = quality_index(float(row["full_sphere_psnr_db"]))
    for row in read_csv(data / "segment_sizes.csv"):
        key = (contexts.index((row["content"], int(row["segment"]))), int(row["ladder_index"]))
        if np.isfinite(sizes[key]):
            raise ValueError("duplicate size key")
        sizes[key] = int(row["bytes"])
    if not np.isfinite(predicted).all() or not np.isfinite(sizes).all() or np.any(sizes <= 0):
        raise ValueError("incomplete sender table")
    psnr, _ = label_array(data / "calibration_quality.csv", split["calibration"], contexts)
    radius, scores = quality_radius(predicted, quality_index(psnr))
    return {"split": split, "contexts": contexts, "predicted": predicted, "sizes": sizes,
            "radius": radius, "scores": scores}


def make_plan(index, subjects):
    seed = 202610240 + index
    rng = np.random.default_rng(seed)
    capacities = np.clip(rng.normal(3, .3, 90), 1, 4.5)
    capacities[np.arange(90) % 8 >= 5] *= .4
    contents = ["ParkFountains01", "River01", "Train01"]
    return {"seed": seed, "subjects": rng.choice(subjects, 5, replace=False).tolist(),
            "contents": [contents[(index + user) % 3] for user in range(5)],
            "capacities_mbps": capacities.tolist(), "impaired_user": index % 5}


def cap_at(scenario, epoch, user, impaired):
    return 1 if scenario in {"known_ceiling", "delayed_ceiling"} and 30 <= epoch < 60 and user == impaired else 5


def simulate(model, psnr, ssim, plan, policy, scenario):
    subjects = model["split"]["test"]
    subject_indices = np.array([subjects.index(sid) for sid in plan["subjects"]])
    debt, last, buffer = np.zeros(5), np.zeros(5), np.full(5, 4.)
    previous, rows, wallclock = np.ones(5, int), [], 0.
    for epoch, capacity in enumerate(plan["capacities_mbps"]):
        context_ids = np.array([model["contexts"].index((name, epoch % 6)) for name in plan["contents"]])
        estimate = plan["capacities_mbps"][epoch - 1] if epoch else 3.
        budget = estimate * 1e6 * 10 / 8
        observed_epoch = epoch - 1 if scenario == "delayed_ceiling" else epoch
        cap = np.array([cap_at(scenario, observed_epoch, u, plan["impaired_user"]) for u in range(5)])
        actual_cap = np.array([cap_at(scenario, epoch, u, plan["impaired_user"]) for u in range(5)])
        predicted = model["predicted"][context_ids].copy()
        if scenario == "prediction_shift" and 30 <= epoch < 60:
            predicted = np.clip(predicted + .6, 1, 5)
        predicted = np.take_along_axis(predicted, np.minimum(np.arange(6), cap[:, None]), axis=1)
        costs = model["sizes"][context_ids]
        start = time.perf_counter()
        action, decision = select_action(policy, predicted, model["radius"], costs, budget, debt, last, previous)
        decision_ms = 1000 * (time.perf_counter() - start)
        bytecount = costs[np.arange(5), action]
        completion = processor_sharing(bytecount * 8, capacity)
        duration = float(completion.max())
        clock = advance_round(buffer, completion, duration)
        effective = np.minimum(action, actual_cap)
        # Only now access held-out viewport outcomes; feedback does not reveal unchosen actions.
        actual_psnr = psnr[subject_indices, context_ids, effective]
        actual_ssim = ssim[subject_indices, context_ids, effective]
        quality = quality_index(actual_psnr)
        updated = update_debt(debt, decision["target"], quality)
        if np.max(np.abs(buffer + 10 + clock.stall_s - duration - clock.buffer_s)) > 1e-8:
            raise AssertionError("clock conservation failed")
        for user in range(5):
            rows.append({"seed": plan["seed"], "scenario": scenario, "policy": policy, "epoch": epoch,
                         "user": user, "subject": plan["subjects"][user], "content": plan["contents"][user],
                         "segment": epoch % 6, "action": int(action[user]), "displayed_action": int(effective[user]),
                         "observed_cap": int(cap[user]), "actual_cap": int(actual_cap[user]),
                         "quality": float(quality[user]), "vw_psnr_db": float(actual_psnr[user]), "vw_ssim": float(actual_ssim[user]),
                         "predicted": float(decision["mean"][user]), "lower": float(decision["lower"][user]),
                         "upper": float(min(5, decision["mean"][user] + model["radius"])),
                         "fixed_shortfall": float(max(4 - quality[user], 0)),
                         "feasible_floor": float(decision["floor"][user]), "individual_ceiling": float(decision["ceiling"][user]),
                         "target": float(decision["target"][user]), "witness_action": int(decision["witness"][user]),
                         "debt_before": float(debt[user]), "debt_after": float(updated[user]),
                         "capacity_mbps": capacity, "forecast_capacity_mbps": estimate, "budget_bytes": budget,
                         "bytes": int(bytecount[user]), "excess_bytes": float(max(0, bytecount[user] - costs[user, effective[user]])),
                         "completion_s": float(completion[user]), "round_duration_s": duration, "clock_before_s": wallclock,
                         "buffer_before_s": float(buffer[user]), "buffer_after_s": float(clock.buffer_s[user]), "stall_s": float(clock.stall_s[user]),
                         "switched": int(action[user] != previous[user]), "decision_ms": decision_ms,
                         "candidate_count": decision["candidate_count"]})
        debt, last, buffer, previous = updated, np.maximum(decision["target"] - quality, 0), clock.buffer_s, action
        wallclock += duration
    return rows


def summarize(rows, impaired):
    q = np.array([r["quality"] for r in rows]).reshape(90, 5)
    deficit = np.maximum(4 - q, 0)
    meets = q[60:, impaired] >= 4
    events = [i + 2 for i in range(29) if meets[i] and meets[i + 1]]
    debt = np.array([r["debt_after"] for r in rows]).reshape(90, 5)
    return {"seed": rows[0]["seed"], "scenario": rows[0]["scenario"], "policy": rows[0]["policy"],
            "cumulative_shortfall": float(deficit.sum(axis=0).mean()),
            "post_restoration_shortfall": float(deficit[60:].sum(axis=0).mean()),
            "impaired_restoration_shortfall": float(deficit[60:, impaired].sum()),
            "stall_s_per_user": sum(r["stall_s"] for r in rows) / 5,
            "stall_after_first_round_s_per_user": sum(r["stall_s"] for r in rows if r["epoch"] > 0) / 5,
            "worst_user_quality": float(q.mean(axis=0).min()), "mean_quality": float(q.mean()),
            "longest_deprivation_rounds": max(longest_run(deficit[:, u] > 0) for u in range(5)),
            "recovery_wait_capped30": events[0] if events else 30, "recovery_event_observed": int(bool(events)),
            "max_debt_ceiling": float(debt[30:60].max()), "max_debt_restored": float(debt[60:].max()),
            "excess_bytes": sum(r["excess_bytes"] for r in rows), "total_bytes": sum(r["bytes"] for r in rows),
            "switch_frequency": float(np.mean([r["switched"] for r in rows])),
            "selected_quality_coverage": float(np.mean([r["lower"] - 1e-12 <= r["quality"] <= r["upper"] + 1e-12 for r in rows])),
            "clipped_high_fraction": float(np.mean(q >= 5)), "clipped_low_fraction": float(np.mean(q <= 1)),
            "decision_ms_median": float(np.median([r["decision_ms"] for r in rows[::5]]))}


def contrasts(summaries):
    rng, result = np.random.default_rng(481517), []
    for scenario in SCENARIOS:
        proposed = {r["seed"]: r for r in summaries if r["scenario"] == scenario and r["policy"] == "feasible_recovery"}
        for baseline in POLICIES:
            if baseline == "feasible_recovery":
                continue
            comparator = {r["seed"]: r for r in summaries if r["scenario"] == scenario and r["policy"] == baseline}
            for outcome in OUTCOMES:
                diff = np.array([proposed[s][outcome] - comparator[s][outcome] for s in sorted(proposed)])
                draws = rng.choice(diff, (2000, len(diff)), replace=True).mean(axis=1)
                result.append({"scenario": scenario, "baseline": baseline, "outcome": outcome, "paired_seeds": len(diff),
                               "mean_delta": float(diff.mean()), "descriptive_ci95_low": float(np.quantile(draws, .025)),
                               "descriptive_ci95_high": float(np.quantile(draws, .975))})
    return result


def progression(summaries, comparisons):
    delta = {r["outcome"]: r["mean_delta"] for r in comparisons if r["scenario"] == "known_ceiling" and r["baseline"] == "fixed_debt"}
    stall = float(np.mean([r["stall_s_per_user"] for r in summaries if r["scenario"] == "known_ceiling" and r["policy"] == "fixed_debt"]))
    passed = delta["cumulative_shortfall"] < 0 and delta["post_restoration_shortfall"] < 0 and delta["stall_s_per_user"] <= (.05 * stall if stall else .1) and delta["worst_user_quality"] >= -.02
    return bool(passed), delta


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, default=ROOT / "feasibility_recovery/results/v2")
    parser.add_argument("--seeds", type=int, default=20)
    args = parser.parse_args()
    if args.seeds < 1 or args.seeds > 20:
        parser.error("1--20 seeds; fewer than 20 is an engineering subset only")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("output nonempty; choose a new version")
    model = fit(args.data)
    args.output.mkdir(parents=True, exist_ok=True)
    calibration = {"split": model["split"], "contexts": model["contexts"], "prediction": model["predicted"].tolist(),
                   "radius": model["radius"], "scores": model["scores"].tolist(), "rank": 9, "nominal_panel_coverage": .9,
                   "test_labels_used_for_fit": False}
    (args.output / "calibration.json").write_text(json.dumps(calibration, indent=2) + "\n")
    # Fit is complete and saved before test labels are loaded for outcome simulation.
    psnr, ssim = label_array(args.data / "heldout_quality.csv", model["split"]["test"], model["contexts"])
    errors = np.max(np.abs(quality_index(psnr) - model["predicted"][None]), axis=(1, 2))
    panels = [{"subject": sid, "max_error": float(error), "covered": bool(error <= model["radius"] + 1e-12)}
              for sid, error in zip(model["split"]["test"], errors)]
    (args.output / "heldout_panel_coverage.json").write_text(json.dumps(panels, indent=2) + "\n")
    plans = [make_plan(i, model["split"]["test"]) for i in range(args.seeds)]
    (args.output / "campaign_plan.json").write_text(json.dumps(plans, indent=2) + "\n")
    summaries, disagreements = [], []
    with (args.output / "measurements.csv.gz").open("wb") as binary:
        with gzip.GzipFile(fileobj=binary, mode="wb", filename="", mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as handle:
                writer = None
                for plan in plans:
                    for scenario in SCENARIOS:
                        actions = {}
                        for policy in POLICIES:
                            rows = simulate(model, psnr, ssim, plan, policy, scenario)
                            if writer is None:
                                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                                writer.writeheader()
                            writer.writerows(rows)
                            summaries.append(summarize(rows, plan["impaired_user"]))
                            actions[policy] = np.array([r["action"] for r in rows])
                        for baseline in POLICIES:
                            if baseline != "feasible_recovery":
                                disagreements.append({"seed": plan["seed"], "scenario": scenario, "baseline": baseline,
                                                      "disagreements": int(np.sum(actions[baseline] != actions["feasible_recovery"])), "comparisons": 450})
                        print(f"completed seed={plan['seed']} scenario={scenario}", flush=True)
    comparisons = contrasts(summaries)
    passed, primary = progression(summaries, comparisons)
    write_csv(args.output / "seed_metrics.csv", summaries)
    write_csv(args.output / "paired_diagnostics.csv", comparisons)
    write_csv(args.output / "action_disagreements.csv", disagreements)
    lines = ["# Feasibility-aware recovery v2", "", "Fresh-content exploratory replay; not live or human-perception validation.", "",
             f"Predeclared descriptive progression screen: **{'PASS' if passed else 'FAIL'}**.",
             f"Seeds: {args.seeds}/20. Panel radius: {model['radius']:.6f}. Held-out panels covered: {sum(p['covered'] for p in panels)}/19.", "",
             "## Candidate minus fixed-target debt", "", "|Scenario|Cumulative shortfall|Restoration shortfall|Stall s/user|Worst-user quality|",
             "|---|---:|---:|---:|---:|"]
    for scenario in SCENARIOS:
        d = {r["outcome"]: r["mean_delta"] for r in comparisons if r["scenario"] == scenario and r["baseline"] == "fixed_debt"}
        lines.append(f"|{scenario}|{d['cumulative_shortfall']:.6f}|{d['post_restoration_shortfall']:.6f}|{d['stall_s_per_user']:.6f}|{d['worst_user_quality']:.6f}|")
    lines += ["", "Negative shortfall/stall deltas favor the candidate; positive quality deltas favor it.",
              "All policy contrasts and descriptive paired intervals are supplied. Seed intervals condition on three scenes and reused source participants; they are not evidence across an independent content population.",
              "Recovery waits are right-censored at 30 rounds. Reduced internal debt alone is not a benefit. Calibration quality bounds do not imply a gain bound or shift validity.",
              "See PROTOCOL.md and INTERPRETATION.md. No parameter retuning on this holdout is authorized by a favorable or adverse outcome."]
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n")
    git = subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    metadata = {"format": "feasibility-pilot-v2", "exploratory": True, "seeds": args.seeds, "matches_locked_seed_count": args.seeds == 20,
                "rows": args.seeds * 4 * 6 * 90 * 5, "git_head_at_run": git, "python": platform.python_version(), "numpy": np.__version__,
                "platform": platform.platform(), "progression_gate_passed": passed, "primary_mean_deltas": primary,
                "source_sha256": {p: sha256(ROOT / p) for p in SOURCES},
                "input_sha256": {p.name: sha256(p) for p in args.data.iterdir() if p.is_file()},
                "result_sha256": {p.name: sha256(p) for p in args.output.iterdir() if p.is_file()},
                "runtime_injected_into_simulated_clock": False, "new_participants": False,
                "limitations": ["three new scenes, same dataset/participant pool", "looped six segments", "synthetic ceiling and capacity traces",
                                "fluid transport, no player deployment", "no head movement predictor", "sender full-sphere prediction",
                                "exact score/byte ties break by enumeration order", "no conditional/shift guarantee", "no theoretical novelty claim"]}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "progression_gate_passed": passed, "primary_mean_deltas": primary}, indent=2))


if __name__ == "__main__":
    main()
