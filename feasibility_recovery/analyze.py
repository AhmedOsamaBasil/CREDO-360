"""Scientific figures and descriptive mechanism diagnostics; no retuning."""
from __future__ import annotations
import argparse
import csv
import gzip
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from feasibility_recovery.run import ROOT, read_csv, sha256, write_csv, POLICIES, SCENARIOS


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "feasibility_recovery/results/v2")
    args = parser.parse_args()
    folder = args.output / "diagnostics"
    if folder.exists():
        parser.error("diagnostics already exist; do not overwrite")
    folder.mkdir()
    comparisons = read_csv(args.output / "paired_diagnostics.csv")
    actions = read_csv(args.output / "action_disagreements.csv")
    aggregation, curves, content = {}, {}, {}
    with gzip.open(args.output / "measurements.csv.gz", "rt", newline="", encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            key = (r["scenario"], r["policy"])
            agg = aggregation.setdefault(key, np.zeros(7))
            agg += [1, float(r["debt_before"]) <= 1e-12, float(r["target"]), float(r["feasible_floor"]),
                    4 - float(r["individual_ceiling"]), float(r["individual_ceiling"]) - float(r["feasible_floor"]),
                    float(r["quality"]) >= float(r["feasible_floor"])]
            if r["scenario"] == "known_ceiling":
                k = (r["policy"], int(r["epoch"]))
                curves.setdefault(k, []).append([float(r["debt_after"]), float(r["fixed_shortfall"])])
                k = (int(r["seed"]), r["policy"], r["content"])
                content.setdefault(k, []).append(float(r["quality"]))
    rows = []
    for (scenario, policy), values in aggregation.items():
        n = values[0]
        rows.append({"scenario": scenario, "policy": policy, "rows": int(n), "zero_queue_fraction": values[1]/n,
                     "decision_state": ("persistent_queue" if policy in {"fixed_debt", "ceiling_debt", "feasible_recovery"}
                                        else "last_deficit" if policy == "memoryless_feasible" else "none"),
                     "mean_queue_target": values[2]/n, "mean_feasible_floor": values[3]/n,
                     "predicted_ceiling_relaxation": values[4]/n, "contention_relaxation": values[5]/n,
                     "realized_quality_meets_reference_fraction": values[6]/n})
    write_csv(folder / "queue_diagnostics.csv", rows)
    content_rows = []
    for scene in ("ParkFountains01", "River01", "Train01"):
        seeds = sorted({key[0] for key in content})
        for baseline in ("fixed_debt", "bounded_nash", "ceiling_debt"):
            diffs = [np.mean(content[s, "feasible_recovery", scene]) - np.mean(content[s, baseline, scene]) for s in seeds]
            content_rows.append({"content": scene, "baseline": baseline, "paired_seeds": len(seeds),
                                 "mean_quality_delta": float(np.mean(diffs)), "min_seed_delta": float(np.min(diffs)),
                                 "max_seed_delta": float(np.max(diffs))})
    write_csv(folder / "content_diagnostics.csv", content_rows)
    agreement_rows = []
    for scenario in SCENARIOS:
        for baseline in POLICIES:
            if baseline == "feasible_recovery":
                continue
            subset = [r for r in actions if r["scenario"] == scenario and r["baseline"] == baseline]
            agreement_rows.append({"scenario": scenario, "baseline": baseline,
                                   "action_disagreement_fraction": sum(int(r["disagreements"]) for r in subset)/sum(int(r["comparisons"]) for r in subset)})
    write_csv(folder / "agreement_summary.csv", agreement_rows)
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.3), constrained_layout=True)
    colors = {"fixed_debt": "#bd4b2c", "feasible_recovery": "#007f87", "bounded_nash": "#686868", "ceiling_debt": "#8056a3"}
    for policy, color in colors.items():
        vals = np.array([np.mean(curves[policy, t], axis=0) for t in range(90)])
        for i, ax in enumerate(axes):
            if i == 0 and policy == "bounded_nash":
                continue  # A shadow diagnostic queue is not Nash's decision state.
            ax.plot(np.arange(90), vals[:, i], label=policy.replace("_", " "), color=color, lw=1.25)
    for ax in axes:
        ax.axvspan(30, 59, color="#dedede", alpha=.5)
        ax.axvline(60, ls="--", color="black", lw=.7)
        ax.set_xlabel("Decision round")
    axes[0].set_ylabel("Mean recovery queue (index units)")
    axes[1].set_ylabel("Mean fixed-target shortfall (index units)")
    axes[0].legend(fontsize=7)
    axes[1].legend(fontsize=7)
    fig.suptitle("Known ceiling: paired-seed averages; shaded = impairment")
    for suffix in ("pdf", "png"):
        fig.savefig(folder / f"recovery_dynamics.{suffix}", dpi=180)
    plt.close(fig)
    outcomes = [("cumulative_shortfall", "Cumulative shortfall\n(index-rounds/user)"),
                ("post_restoration_shortfall", "Restoration shortfall\n(index-rounds/user)"),
                ("stall_s_per_user", "Stall\n(seconds/user)"), ("worst_user_quality", "Worst-user mean\nquality index")]
    fig, axes = plt.subplots(1, 4, figsize=(11, 3.1), constrained_layout=True)
    labels = ["Fixed debt", "Ceiling debt", "Bounded Nash"]
    for ax, (outcome, title) in zip(axes, outcomes):
        for j, baseline in enumerate(("fixed_debt", "ceiling_debt", "bounded_nash")):
            r = next(r for r in comparisons if r["scenario"] == "known_ceiling" and r["baseline"] == baseline and r["outcome"] == outcome)
            mean, lo, hi = (float(r[k]) for k in ("mean_delta", "descriptive_ci95_low", "descriptive_ci95_high"))
            ax.plot([lo, hi], [j, j], color=colors[baseline], lw=2)
            ax.scatter([mean], [j], color=colors[baseline], s=25)
        ax.axvline(0, color="black", ls="--", lw=.7)
        ax.set_yticks(range(3), labels)
        ax.set_title(title)
        ax.set_xlabel("Candidate minus baseline")
    fig.suptitle("Known ceiling: paired mean differences, descriptive 95% seed intervals")
    for suffix in ("pdf", "png"):
        fig.savefig(folder / f"paired_effects.{suffix}", dpi=180)
    plt.close(fig)
    manifest = {"inputs": {p: sha256(args.output / p) for p in ("measurements.csv.gz", "paired_diagnostics.csv", "seed_metrics.csv", "action_disagreements.csv")},
                "analysis_source_sha256": sha256(Path(__file__)),
                "outputs": {p.name: sha256(p) for p in folder.iterdir() if p.is_file()},
                "scope": "descriptive mechanism/content diagnostics, not additional confirmatory endpoints"}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"diagnostics": str(folder), "files": len(manifest["outputs"])}, indent=2))


if __name__ == "__main__":
    main()
