"""Separately labeled post-hoc diagnosis and figure of the frozen sensitivity grid."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
from statistics import mean
import numpy as np
from metric_contract.data import ROOT, METRICS, load
from metric_contract.core import path_arrays, metric_paths, debt, bound
from metric_contract.run import canonical, sha, OUT

DEST = ROOT/"metric_contract/results/diagnostics_v1"


def diagnostics():
    with gzip.open(OUT/"results.json.gz", "rt") as stream:
        result = json.load(stream)
    def cell(metric, policy, group="all", impairment=0, h=4, clock="media"):
        return next(r for r in result["summary"] if (r["group"], r["metric"], r["policy"], r["impairment"], r["horizon"], r["clock"])
                    == (group, metric, policy, impairment, h, clock))
    comparisons = []
    for group in ("all", "v2", "v3"):
        for metric in METRICS:
            a, b = cell(metric, "prefix_mpc", group), cell(metric, "prefix_cost_greedy", group)
            comparisons.append({"group": group, "metric": metric,
                "primary_minus_cost_greedy_unpaid": round(a["mean_unpaid"]-b["mean_unpaid"], 12),
                "primary_half": a["targets_met"][1], "cost_greedy_half": b["targets_met"][1]})
    records, _ = load()
    common = []; harms = []; clipping = {"values": 0, "at_or_above_42db": 0, "below_or_at_18db": 0}
    # These count directed-episode appearances, not distinct observations.
    for record in records:
        psnr = record["quality"][2]
        clipping["values"] += int(psnr.size)
        clipping["at_or_above_42db"] += int((psnr >= 42000000).sum())
        clipping["below_or_at_18db"] += int((psnr <= 18000000).sum())
        arrays = path_arrays(record["costs"], 4, record["reserve"])
        menus = [metric_paths(q, arrays, 4) for q in record["quality"]]
        common_safe = np.logical_and.reduce([s for s, g in menus])
        for m, (safe, gains) in enumerate(menus):
            b = bound(debt(record["quality"][m], 0), common_safe, gains["media"], arrays)
            common.append({"key": record["key"], "metric": METRICS[m], "native_safe_paths": int(safe.sum()),
                           "common_safe_paths": int(common_safe.sum()), "half": b["targets_met"][1], "unpaid": b["unpaid"]})
        saved = record["policies"]["prefix_mpc"]
        for row in saved["rounds"]:
            t = row["segment"]
            for u, rung in enumerate(row["decision"]["rungs"]):
                delta = int(psnr[t, u, rung]-psnr[t, u, 2])
                if delta < 0:
                    harms.append({"key": record["key"], "segment": t, "user": u, "rung": rung,
                                  "psnr_loss_db": -delta/1000000,
                                  "legacy_index_loss": max(0, int(record["quality"][0,t,u,2]-record["quality"][0,t,u,rung]))/1000})
    common_summary = [{"metric": m, "half": sum(r["half"] for r in common if r["metric"] == m),
                       "mean_unpaid": round(mean(r["unpaid"] for r in common if r["metric"] == m), 12),
                       "episodes_native_set_larger": sum(r["native_safe_paths"] > r["common_safe_paths"] for r in common if r["metric"] == m)}
                      for m in METRICS]
    legacy = {tuple(r[k] for k in ("key", "policy", "impairment", "horizon", "clock")): r for r in result["fixed_path_rows"] if r["metric"] == "index"}
    differences = [abs(r["unpaid"]-legacy[tuple(r[k] for k in ("key", "policy", "impairment", "horizon", "clock"))]["unpaid"])
                   for r in result["fixed_path_rows"] if r["metric"] == "fine_index" and r["applicable"]]
    return {"posthoc": True, "original_methods_unchanged": True,
            "primary_cost_greedy_contrasts": comparisons, "common_floor_oracle": common_summary,
            "common_floor_rows": common, "primary_psnr_floor_losses": harms,
            "primary_floor_loss_summary": {"count": len(harms), "max_db": max(r["psnr_loss_db"] for r in harms),
                "median_db": float(np.median([r["psnr_loss_db"] for r in harms])),
                "hidden_by_legacy_rounding_or_clipping": sum(r["legacy_index_loss"] == 0 for r in harms)},
            "clipping_directed_appearances": clipping,
            "max_fixed_path_unpaid_change_coarse_to_fine": max(differences),
            "offline_grid": [r for r in result["summary"] if r["policy"] == "offline"],
            "new_scientific_success_claim": False}


def figures(result):
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT/".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "metric-contract-v1"})
    labels = ["Rounded\nindex", "Fine\nindex", "Unclipped\nPSNR", "Distortion\nreduction"]
    x = np.arange(4)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), layout="constrained")
    def oracle(m, h, clock, impairment=0):
        return next(r for r in result["offline_grid"] if r["group"] == "all" and r["metric"] == m
                    and r["impairment"] == impairment and r["horizon"] == h and r["clock"] == clock)
    vals = [oracle(m, 4, "media")["targets_met"][1] for m in METRICS]
    bars = axes[0].bar(x, vals, color=["#32658b", "#6a94ad", "#50846b", "#b66d3e"])
    axes[0].bar_label(bars, padding=3)
    axes[0].set(xticks=x, xticklabels=labels, ylim=(0, 190), ylabel="Episodes reaching 50% repayment /168",
                title="A. Same resources, different units\nOffline, after four segments")
    delta = [next(r["primary_minus_cost_greedy_unpaid"] for r in result["primary_cost_greedy_contrasts"]
                  if r["group"] == "all" and r["metric"] == m) for m in METRICS]
    axes[1].bar(x, delta, color=["#b66d3e" if d > 0 else "#50846b" for d in delta])
    axes[1].axhline(0, color="black", lw=.8)
    axes[1].set(xticks=x, xticklabels=labels, ylabel="Primary minus cost-greedy mean unpaid",
                title="B. Ranking reverses with the metric\nFixed paths; above zero = primary worse")
    for metric, color, name in (("index", "#32658b", "Index"), ("negative_mse", "#b66d3e", "Distortion")):
        for clock, style in (("media", "-"), ("deadline", "--")):
            axes[2].plot([1,2,4], [oracle(metric,h,clock)["targets_met"][1] for h in (1,2,4)],
                         style, marker="o", color=color, label=name+" / "+("played" if clock=="media" else "deadline"))
    axes[2].set(xticks=[1,2,4], xlabel="Recovery segments H (deadline = 10H s)", ylabel="Offline half-repayment episodes /168",
                ylim=(-5, 110), title="C. Played media is not elapsed time\nFixed reserve; cold nominal 10 s playback")
    axes[2].legend(fontsize=8)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    for ext in ("png", "svg"):
        fig.savefig(DEST/f"metric_contract.{ext}", dpi=180, metadata={"Date": None} if ext=="svg" else {})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--repair-metadata", action="store_true", help="Create a portable successor; retain original metadata")
    args = parser.parse_args()
    result = diagnostics(); digest = hashlib.sha256(canonical(result)).hexdigest()
    inputs = {p.relative_to(ROOT).as_posix(): sha(p) for p in (OUT/"results.json.gz", OUT/"metadata.json")}
    successor = DEST/"metadata_portable.json"
    if args.repair_metadata:
        old = json.loads((DEST/"metadata.json").read_text())
        if old["scientific_sha256"] != digest or json.loads((DEST/"results.json").read_text()) != result:
            raise ValueError("Cannot repair metadata for changed scientific results")
        if {k.replace("\\", "/"): v for k, v in old["input_sha256"].items()} != inputs:
            raise ValueError("Metadata repair must not change input hashes")
        if any(sha(DEST/n) != h for n, h in old["figure_sha256"].items()):
            raise ValueError("Metadata repair must not change figures")
        with successor.open("x", encoding="utf-8") as stream:
            json.dump({**old, "input_sha256": inputs, "script_sha256": sha(Path(__file__)),
                "predecessor_metadata_sha256": sha(DEST/"metadata.json"),
                "repair": "Portable POSIX input keys; scientific values and original metadata retained"}, stream, indent=2)
        print("Created portable metadata successor; original metadata, outcomes and figures unchanged")
        return
    if args.verify:
        meta = json.loads((successor if successor.exists() else DEST/"metadata.json").read_text())
        if successor.exists() and meta["predecessor_metadata_sha256"] != sha(DEST/"metadata.json"):
            raise ValueError("Original diagnostic metadata changed")
        if meta["input_sha256"] != inputs or meta["script_sha256"] != sha(Path(__file__)) or meta["scientific_sha256"] != digest:
            raise ValueError("Diagnostic source/result mismatch")
        if json.loads((DEST/"results.json").read_text()) != result:
            raise ValueError("Diagnostic rows changed")
        for name, expected in meta["figure_sha256"].items():
            if sha(DEST/name) != expected:
                raise ValueError("Figure changed")
    else:
        if DEST.exists():
            if (DEST/"metadata.json").exists():
                raise FileExistsError("Preserve complete diagnostic artifact")
            if json.loads((DEST/"results.json").read_text()) != result:
                raise ValueError("Incomplete diagnostic has different results")
            if not all((DEST/f"metric_contract.{ext}").is_file() for ext in ("png", "svg")):
                raise ValueError("Incomplete figures; do not silently overwrite")
            print("Finalizing metadata for matching existing diagnostics; no outcome or figure overwritten", flush=True)
        else:
            DEST.mkdir(parents=True)
            (DEST/"results.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
            figures(result)
        (DEST/"metadata.json").write_text(json.dumps({"input_sha256": inputs, "script_sha256": sha(Path(__file__)),
            "scientific_sha256": digest, "figure_sha256": {p.name: sha(p) for p in DEST.glob("metric_contract.*")}}, indent=2)+"\n")
    print(json.dumps({"verified": args.verify, "scientific_sha256": digest,
                      "common_floor": result["common_floor_oracle"], "floor_losses": result["primary_floor_loss_summary"],
                      "coarse_to_fine_max": result["max_fixed_path_unpaid_change_coarse_to_fine"],
                      "contrasts": result["primary_cost_greedy_contrasts"]}))


if __name__ == "__main__":
    main()
