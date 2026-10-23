"""Fixed six-configuration search on already-exposed v2 outcomes only."""
import json
from pathlib import Path
import numpy as np
from horizon_recovery.run import ROOT, fit, label_array, make_plan, contracts, simulate, summarize, SCENARIOS, POLICIES, write_csv, sha256


def main():
    output = ROOT / "horizon_recovery/results/development_v1"
    if output.exists():
        raise ValueError("development output exists; preserve every run")
    output.mkdir(parents=True)
    data = ROOT / "feasibility_recovery/data/v2"
    model = fit(data,development=True)
    psnr,ssim = label_array(data/"heldout_quality.csv",model["split"]["test"],model["contexts"])
    plans = [make_plan(i,model,True) for i in range(6)]
    cache = {}
    for plan in plans:
        for scenario in SCENARIOS:
            cache[f"{plan['seed']}:{scenario}"] = contracts(model,plan,scenario)
    (output/"contracts.json").write_text(json.dumps(cache,indent=2)+"\n")
    (output/"plans.json").write_text(json.dumps(plans,indent=2)+"\n")
    all_summaries, selection = [], []
    for horizon in (12,24):
        for strength in (.5,2.,8.):
            summaries = []
            for plan in plans:
                for scenario in SCENARIOS:
                    for policy in POLICIES:
                        rows = simulate(model,psnr,ssim,plan,scenario,policy,horizon,strength,cache[f"{plan['seed']}:{scenario}"])
                        summaries.append(summarize(rows,plan["impaired_user"]))
            all_summaries.extend(summaries)
            means = {p:{metric:np.mean([r[metric] for r in summaries if r["scenario"]=="known_ceiling" and r["policy"]==p])
                        for metric in ("worst_user_quality","mean_quality","cumulative_shortfall","stall_s_per_user")} for p in POLICIES}
            a = means["window_recovery"]
            passed = True
            diagnostics = {"horizon":horizon,"strength":strength}
            for p in ("nash","memoryless_scaled"):
                b = means[p]
                for k in a:
                    diagnostics[f"delta_{p}_{k}"] = float(a[k]-b[k])
                passed &= a["worst_user_quality"] > b["worst_user_quality"] and a["mean_quality"] >= b["mean_quality"]-.03
                passed &= a["cumulative_shortfall"] <= 1.05*b["cumulative_shortfall"]
                passed &= a["stall_s_per_user"]-b["stall_s_per_user"] <= (.05*b["stall_s_per_user"] if b["stall_s_per_user"] else .1)
            diagnostics["development_screen_passed"] = bool(passed)
            selection.append(diagnostics)
            print(json.dumps(diagnostics),flush=True)
            write_csv(output/f"metrics_h{horizon}_s{strength:g}.csv",summaries)
    eligible = [r for r in selection if r["development_screen_passed"]] or selection
    best = sorted(eligible,key=lambda r:(-r["delta_nash_worst_user_quality"],r["horizon"],r["strength"]))[0]
    write_csv(output/"selection.csv",selection)
    config = {"horizon":best["horizon"],"strength":best["strength"],"development_screen_passed":best["development_screen_passed"],
              "development_data":"feasibility_recovery/data/v2", "selection_rule":"DEVELOPMENT.md; no fresh labels accessed"}
    (output/"selected.json").write_text(json.dumps(config,indent=2)+"\n")
    (output/"metadata.json").write_text(json.dumps({"exposed_data_only":True,"configurations":6,"seeds":6,
        "source_sha256":{n:sha256(ROOT/"horizon_recovery"/n) for n in ("core.py","run.py","develop.py","DEVELOPMENT.md")},
        "input_sha256":{p.name:sha256(p) for p in data.iterdir() if p.is_file()},
        "result_sha256":{p.name:sha256(p) for p in output.iterdir() if p.is_file()}},indent=2)+"\n")
    print(json.dumps(config,indent=2),flush=True)


if __name__ == "__main__":
    main()
