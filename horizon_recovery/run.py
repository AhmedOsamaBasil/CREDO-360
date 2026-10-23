"""Development and frozen evaluation of finite-window entitlement recovery."""
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
from horizon_recovery.core import POLICIES, WindowLedger, contract, select_action
from feasibility_recovery.core import partition as old_partition, quality_radius
from feasibility_recovery.run import label_array, read_csv
from recovery_pilot.core import quality_index
from recovery_pilot.run import processor_sharing, longest_run, sha256, write_csv
from live_testbed.playback_clock import advance_round

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ("capacity_only", "known_ceiling", "delayed_ceiling", "prediction_shift")
OUTCOMES = ("worst_user_quality", "post_restoration_shortfall", "cumulative_shortfall",
            "stall_s_per_user", "mean_quality", "impaired_restoration_shortfall", "switch_frequency")


def partition(subjects):
    import hashlib
    if len(set(subjects)) != 28:
        raise ValueError("28 source IDs required")
    ids = sorted(set(subjects), key=lambda s: hashlib.sha256(f"horizon-v3-{s}".encode()).digest())
    return {"calibration": ids[:9], "test": ids[9:]}


def fit(data, development=False):
    split = json.loads((data / "split.json").read_text())
    expected = (old_partition if development else partition)(split["calibration"] + split["test"])
    if split != expected:
        raise ValueError("source-ID split differs from protocol")
    rows = read_csv(data / "sender_quality.csv")
    contexts = sorted({(r["content"], int(r["segment"])) for r in rows})
    if len(contexts) != 18 or {s for _, s in contexts} != set(range(6)):
        raise ValueError("three six-segment contents required")
    if development:
        names = ["ParkFountains01", "River01", "Train01"]
    else:
        names = sorted(json.loads((ROOT / "horizon_recovery/manifest.json").read_text())["contents"])
    if sorted({c for c, _ in contexts}) != names:
        raise ValueError("unexpected content set")
    predicted, sizes = np.full((18, 6), np.nan), np.full((18, 6), np.nan)
    for row in rows:
        key = contexts.index((row["content"], int(row["segment"]))), int(row["ladder_index"])
        if np.isfinite(predicted[key]):
            raise ValueError("duplicate sender key")
        predicted[key] = quality_index(float(row["full_sphere_psnr_db"]))
    for row in read_csv(data / "segment_sizes.csv"):
        key = contexts.index((row["content"], int(row["segment"]))), int(row["ladder_index"])
        if np.isfinite(sizes[key]):
            raise ValueError("duplicate size key")
        sizes[key] = int(row["bytes"])
    if not np.isfinite(predicted).all() or not np.isfinite(sizes).all() or np.any(sizes <= 0):
        raise ValueError("incomplete sender table")
    # This path never opens held-out outcomes.
    calibration, _ = label_array(data / "calibration_quality.csv", split["calibration"], contexts)
    radius, scores = quality_radius(predicted, quality_index(calibration))
    return {"split": split, "contexts": contexts, "predicted": predicted, "sizes": sizes,
            "radius": radius, "scores": scores.tolist()}


def make_plan(index, model, development=False):
    seed = (202610300 if development else 202610400) + index
    rng = np.random.default_rng(seed)
    capacities = np.clip(rng.normal(3, .3, 120), 1, 4.5)
    capacities[np.arange(120) % 8 >= 5] *= .4
    names = sorted({c for c, _ in model["contexts"]})
    return {"seed": seed, "subjects": rng.choice(model["split"]["test"], 5, replace=False).tolist(),
            "contents": [names[(index + u) % 3] for u in range(5)],
            "capacities_mbps": capacities.tolist(), "impaired_user": index % 5}


def caps(scenario, epoch, impaired, observed=True):
    t = epoch - 1 if observed and scenario == "delayed_ceiling" else epoch
    result = np.full(5, 5)
    if scenario in {"known_ceiling", "delayed_ceiling"} and 40 <= t < 80:
        result[impaired] = 1
    return result


def tables(model, plan, epoch, scenario, periods=1):
    observed = caps(scenario, epoch, plan["impaired_user"])
    shift = scenario == "prediction_shift" and 40 <= epoch < 80
    means, costs = [], []
    for offset in range(periods):
        ids = [model["contexts"].index((c, (epoch + offset) % 6)) for c in plan["contents"]]
        q = model["predicted"][ids].copy()
        if shift:
            q = np.clip(q + .6, 1, 5)
        means.append(np.take_along_axis(q, np.minimum(np.arange(6), observed[:, None]), axis=1))
        costs.append(model["sizes"][ids])
    return np.array(means), np.array(costs)


def contracts(model, plan, scenario):
    result, previous_signature = {}, None
    for t in range(120):
        signature = (tuple(caps(scenario, t, plan["impaired_user"])), scenario == "prediction_shift" and 40 <= t < 80)
        if t % 6 == 0 or signature != previous_signature:
            prediction, costs = tables(model, plan, t, scenario, periods=6)
            forecast = float(np.mean(plan["capacities_mbps"][max(0, t-12):t])) if t else 3.
            start = time.perf_counter()
            result[str(t)] = contract(prediction, model["radius"], costs, forecast * 1e6 * 10 / 8)
            result[str(t)].update({"forecast_capacity_mbps": forecast,
                                   "contract_ms": 1000 * (time.perf_counter() - start)})
        previous_signature = signature
    return result


def simulate(model, psnr, ssim, plan, scenario, policy, horizon, strength, service_contracts):
    ledger = WindowLedger(horizon, 5)
    buffer, previous, wallclock, rows = np.full(5, 4.), np.ones(5, int), 0., []
    sid_indices = np.array([model["split"]["test"].index(s) for s in plan["subjects"]])
    contract_epoch = 0
    for t, capacity in enumerate(plan["capacities_mbps"]):
        if str(t) in service_contracts:
            contract_epoch = t
        service = service_contracts[str(contract_epoch)]
        target = np.array(service["target"]) if policy != "fixed_window" else np.full(5, 4.)
        predicted, costs = tables(model, plan, t, scenario)
        predicted, costs = predicted[0], costs[0]
        estimate = plan["capacities_mbps"][t-1] if t else 3.
        budget = estimate * 1e6 * 10 / 8
        state = ledger.state(policy)
        start = time.perf_counter()
        action, decision = select_action(policy, predicted, model["radius"], costs, budget, state, target, horizon, strength)
        runtime = 1000 * (time.perf_counter() - start)
        bytecount = costs[np.arange(5), action]
        completion = processor_sharing(bytecount * 8, capacity)
        duration = float(completion.max())
        clock = advance_round(buffer, completion, duration)
        observed_cap = caps(scenario, t, plan["impaired_user"])
        actual_cap = caps(scenario, t, plan["impaired_user"], observed=False)
        effective = np.minimum(action, actual_cap)
        context_ids = np.array([model["contexts"].index((c, t % 6)) for c in plan["contents"]])
        # Only selected post-action outcome is provided to recovery feedback.
        actual_psnr = psnr[sid_indices, context_ids, effective]
        actual_ssim = ssim[sid_indices, context_ids, effective]
        quality = quality_index(actual_psnr)
        expired = ledger.update(target, quality)
        after = ledger.state(policy)
        for u in range(5):
            mean = float(predicted[u, action[u]])
            rows.append({"seed": plan["seed"], "scenario": scenario, "policy": policy, "horizon": horizon, "strength": strength,
                         "epoch": t, "user": u, "subject": plan["subjects"][u], "content": plan["contents"][u], "segment": t % 6,
                         "action": int(action[u]), "displayed_action": int(effective[u]), "nash_action": int(decision["nash_action"][u]),
                         "quality": float(quality[u]), "vw_psnr_db": float(actual_psnr[u]), "vw_ssim": float(actual_ssim[u]),
                         "predicted": mean, "lower": max(1, mean-model["radius"]), "upper": min(5, mean+model["radius"]),
                         "target": float(target[u]), "state_before": float(state[u]), "state_after": float(after[u]),
                         "expired_signed_residual": float(expired[u]), "signed_residual": float(target[u]-quality[u]),
                         "fixed_shortfall": float(max(4-quality[u], 0)), "contract_epoch": contract_epoch,
                         "observed_cap": int(observed_cap[u]), "actual_cap": int(actual_cap[u]),
                         "capacity_mbps": capacity, "forecast_capacity_mbps": estimate, "budget_bytes": budget,
                         "nash_bytes": decision["nash_bytes"], "bytes": int(bytecount[u]),
                         "excess_bytes": float(max(0, bytecount[u] - costs[u, effective[u]])),
                         "completion_s": float(completion[u]), "round_duration_s": duration, "clock_before_s": wallclock,
                         "buffer_before_s": float(buffer[u]), "buffer_after_s": float(clock.buffer_s[u]), "stall_s": float(clock.stall_s[u]),
                         "switched": int(action[u] != previous[u]), "decision_ms": runtime,
                         "candidate_count": decision["candidate_count"]})
        buffer, previous, wallclock = clock.buffer_s, action, wallclock + duration
    return rows


def summarize(rows, impaired):
    q = np.array([r["quality"] for r in rows]).reshape(120, 5)
    d = np.maximum(4-q, 0)
    meets = q[80:, impaired] >= 4
    events = [i+2 for i in range(39) if meets[i] and meets[i+1]]
    return {**{k: rows[0][k] for k in ("seed", "scenario", "policy", "horizon", "strength")},
            "worst_user_quality": float(q.mean(axis=0).min()), "mean_quality": float(q.mean()),
            "cumulative_shortfall": float(d.sum(axis=0).mean()), "post_restoration_shortfall": float(d[80:].sum(axis=0).mean()),
            "impaired_restoration_shortfall": float(d[80:, impaired].sum()),
            "stall_s_per_user": sum(r["stall_s"] for r in rows)/5,
            "longest_deprivation_rounds": max(longest_run(d[:, u] > 0) for u in range(5)),
            "recovery_wait_capped40": events[0] if events else 40, "recovery_event_observed": int(bool(events)),
            "switch_frequency": float(np.mean([r["switched"] for r in rows])),
            "active_state_fraction": float(np.mean([r["state_before"] > 1e-9 for r in rows])),
            "mean_state": float(np.mean([r["state_before"] for r in rows])),
            "excess_bytes": sum(r["excess_bytes"] for r in rows), "total_bytes": sum(r["bytes"] for r in rows),
            "selected_quality_coverage": float(np.mean([r["lower"]-1e-12 <= r["quality"] <= r["upper"]+1e-12 for r in rows])),
            "decision_ms_median": float(np.median([r["decision_ms"] for r in rows[::5]]))}


def comparisons(summaries):
    result, rng = [], np.random.default_rng(481518)
    for scenario in SCENARIOS:
        a = {r["seed"]: r for r in summaries if r["scenario"] == scenario and r["policy"] == "window_recovery"}
        for baseline in POLICIES:
            if baseline == "window_recovery":
                continue
            b = {r["seed"]: r for r in summaries if r["scenario"] == scenario and r["policy"] == baseline}
            for metric in OUTCOMES:
                diff = np.array([a[s][metric]-b[s][metric] for s in sorted(a)])
                draws = rng.choice(diff, (2000, len(diff)), replace=True).mean(axis=1)
                result.append({"scenario": scenario, "baseline": baseline, "metric": metric, "paired_seeds": len(diff),
                               "mean_delta": float(diff.mean()), "ci95_low": float(np.quantile(draws,.025)), "ci95_high": float(np.quantile(draws,.975))})
    return result


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "horizon_recovery/data/v3")
    parser.add_argument("--output", type=Path, default=ROOT / "horizon_recovery/results/v3")
    parser.add_argument("--seeds", type=int, default=20)
    args = parser.parse_args()
    config = json.loads((ROOT / "horizon_recovery/frozen_config.json").read_text())
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("output already contains results")
    if not 1 <= args.seeds <= 20:
        parser.error("1--20 seeds; only20matchesprotocol")
    model = fit(args.data)
    args.output.mkdir(parents=True, exist_ok=True)
    calibration = {k: (v.tolist() if isinstance(v,np.ndarray) else v) for k,v in model.items() if k != "sizes"}
    (args.output / "calibration.json").write_text(json.dumps(calibration,indent=2)+"\n")
    psnr, ssim = label_array(args.data / "heldout_quality.csv", model["split"]["test"], model["contexts"])
    errors = np.max(np.abs(quality_index(psnr)-model["predicted"]),axis=(1,2))
    panels = [{"subject": s, "max_error": float(e), "covered": bool(e <= model["radius"]+1e-12)} for s,e in zip(model["split"]["test"],errors)]
    (args.output / "panel_coverage.json").write_text(json.dumps(panels,indent=2)+"\n")
    plans = [make_plan(i,model) for i in range(args.seeds)]
    (args.output / "plans.json").write_text(json.dumps(plans,indent=2)+"\n")
    all_contracts, summaries, agreement = {}, [], []
    with (args.output / "measurements.csv.gz").open("wb") as binary:
        with gzip.GzipFile(fileobj=binary, mode="wb", filename="", mtime=0) as compressed:
            with io.TextIOWrapper(compressed,encoding="utf-8",newline="") as handle:
                writer = None
                for plan in plans:
                    for scenario in SCENARIOS:
                        service = contracts(model, plan, scenario)
                        all_contracts[f"{plan['seed']}:{scenario}"] = service
                        actions = {}
                        for policy in POLICIES:
                            rows = simulate(model, psnr, ssim, plan, scenario, policy, config["horizon"], config["strength"], service)
                            if writer is None:
                                writer = csv.DictWriter(handle,fieldnames=list(rows[0])); writer.writeheader()
                            writer.writerows(rows)
                            summaries.append(summarize(rows,plan["impaired_user"]))
                            actions[policy] = np.array([r["action"] for r in rows])
                        for baseline in POLICIES:
                            if baseline != "window_recovery":
                                agreement.append({"seed":plan["seed"],"scenario":scenario,"baseline":baseline,
                                                  "disagreements":int(np.sum(actions[baseline]!=actions["window_recovery"])),"comparisons":600})
                        print(f"completed seed={plan['seed']} scenario={scenario}",flush=True)
    (args.output / "contracts.json").write_text(json.dumps(all_contracts,indent=2)+"\n")
    paired = comparisons(summaries)
    write_csv(args.output / "seed_metrics.csv",summaries)
    write_csv(args.output / "paired_diagnostics.csv",paired)
    write_csv(args.output / "action_disagreements.csv",agreement)
    from horizon_recovery.evaluate import screen
    passed, detail = screen(summaries,paired,agreement)
    source_names = ["horizon_recovery/"+n for n in ("core.py","run.py","evaluate.py","PROTOCOL.md","frozen_config.json")]
    source_names += ["recovery_pilot/core.py","recovery_pilot/run.py","feasibility_recovery/core.py","feasibility_recovery/run.py","live_testbed/playback_clock.py"]
    metadata = {"format":"horizon-v3", "exploratory":True,"seeds":args.seeds,"rows":args.seeds*4*5*120*5,
                "config":config,"progression_gate_passed":passed,"screen_details":detail,
                "git_head_at_run":subprocess.check_output(["git","-c",f"safe.directory={ROOT.as_posix()}","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                "python":platform.python_version(),"numpy":np.__version__,"platform":platform.platform(),
                "source_sha256":{n:sha256(ROOT/n) for n in source_names},
                "input_sha256":{p.name:sha256(p) for p in args.data.iterdir() if p.is_file()},
                "result_sha256":{p.name:sha256(p) for p in args.output.iterdir() if p.is_file()},
                "runtime_injected":False,"new_participants":False}
    (args.output / "metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print(json.dumps({"progression_gate_passed":passed,"details":detail},indent=2))


if __name__ == "__main__":
    main()
