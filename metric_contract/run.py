"""Run or fully verify the fixed exposed metric/contract grid; never overwrite."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean
from metric_contract.data import ROOT, INPUTS, METRICS, SCALES, load
from metric_contract.core import HORIZONS, debt, path_arrays, metric_paths, bound, rescore, validate_saved_clock
from metric_contract.check import scalar_frontier, compare

OUT = ROOT / "metric_contract/results/sensitivity_v1"
SOURCES = ("__init__.py", "core.py", "data.py", "run.py", "check.py", "test_core.py", "PLAN.md")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(path):
    raw = path.read_bytes()
    if path.suffix in (".py", ".md", ".csv", ".json"):
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def provenance():
    return {"source_sha256": {"metric_contract/"+p: sha(ROOT/"metric_contract"/p) for p in SOURCES},
            "input_sha256": {p: sha(ROOT/p) for p in INPUTS},
            "hash_convention": "Raw bytes except text LF normalization; gzip bytes unchanged"}


def summarize(fixed, oracle):
    cells = defaultdict(list)
    for r in fixed+oracle:
        for group in ("all", r["cohort"], r["scene"]):
            key = (group, r["metric"], r["impairment"], r["horizon"], r["clock"], r.get("policy", "offline"))
            cells[key].append(r)
    result = []
    for (group, metric, impairment, horizon, clock, policy), rows in sorted(cells.items()):
        active = [r for r in rows if r["applicable"]]
        result.append({"group": group, "metric": metric, "impairment": impairment,
            "horizon": horizon, "clock": clock, "policy": policy, "episodes": len(rows),
            "positive_loss_episodes": len(active), "zero_loss_episodes": len(rows)-len(active),
            "mean_unpaid": round(mean(r["unpaid"] for r in active), 12) if active else None,
            "targets_met": [sum(r["targets_met"][k] for r in active) for k in range(4)],
            "donor_floor_violations": sum(r.get("donor_floor_violations", 0) for r in rows),
            "recipient_floor_violations": sum(r.get("recipient_floor_violations", 0) for r in rows),
            "mean_minimum_extra_bytes_if_feasible": [
                round(mean(r["minimum_cost_witnesses"][k]["extra_bytes"] for r in active
                           if r["minimum_cost_witnesses"][k] is not None), 6)
                if policy == "offline" and any(r["minimum_cost_witnesses"][k] for r in active) else None
                for k in range(4)]})
    return result


def analysis(progress=False):
    records, historical = load()
    fixed = []; oracle = []
    audits = {"original_policy_scores": 0, "original_strict_oracles": 0, "saved_clock_decisions": 0,
              "independent_queries": 0, "minimum_cost_target_checks": 0,
              "affine_path_checks": 0, "strict_saved_path_bound_checks": 0,
              "monotonicity_checks": 0}
    for i, record in enumerate(records, 1):
        base = {k: record[k] for k in ("key", "cohort", "scene")}
        for saved in record["policies"].values():
            audits["saved_clock_decisions"] += validate_saved_clock(record, saved)
        prior = {}
        for h in HORIZONS:
            arrays = path_arrays(record["costs"], h, record["reserve"])
            for m, metric in enumerate(METRICS):
                quality = record["quality"][m]
                safe, gains = metric_paths(quality, arrays, h)
                transformed_safe, transformed = metric_paths(3*quality+7, arrays, h)
                if not (safe == transformed_safe).all() or any(not (3*gains[c] == transformed[c]).all() for c in gains):
                    raise ValueError("Positive affine invariance failed")
                audits["affine_path_checks"] += len(safe)
                if not (gains["deadline"] <= gains["media"]).all():
                    raise ValueError("Deadline gains exceed eventual gains")
                independent = scalar_frontier(quality, record["costs"], h, record["reserve"])
                for clock in ("media", "deadline"):
                    audits["independent_queries"] += 1
                    current_max = int(gains[clock][safe].max())
                    if current_max < prior.get((metric, clock), 0):
                        raise ValueError("Opportunity decreased with a longer horizon")
                    prior[metric, clock] = current_max
                    audits["monotonicity_checks"] += 1
                    for impairment in (0, 1):
                        loss = debt(quality, impairment)
                        if debt(3*quality+7, impairment) != 3*loss:
                            raise ValueError("Affine debt invariance failed")
                        context = {**base, "metric": metric, "scale": SCALES[m], "impairment": impairment,
                                   "horizon": h, "clock": clock}
                        result = bound(loss, safe, gains[clock], arrays)
                        compare(independent, result, clock)
                        audits["minimum_cost_target_checks"] += 4
                        if loss and result["targets_met"] != sorted(result["targets_met"], reverse=True):
                            raise ValueError("Feasibility increases with target")
                        oracle.append({**context, "resource_paths": arrays["resource_paths"], **result})
                        historical_cell = metric == "index" and impairment == 0 and h == 4 and clock == "media"
                        if historical_cell:
                            old = historical[record["key"]]["bounds"]["strict"]
                            if abs(result["unpaid"]-old["unpaid_fraction"]) > 1e-11 or result["targets_met"][1] != old["half_repaid"]:
                                raise ValueError("Historical strict bound not reproduced")
                            audits["original_strict_oracles"] += 1
                        for policy, saved in sorted(record["policies"].items()):
                            score = rescore(quality, saved, h, impairment, clock)
                            if historical_cell:
                                if abs(score["unpaid"]-saved["unpaid_fraction"]) > 1e-11 or any(
                                    score[k] != saved[k] for k in ("donor_floor_violations", "recipient_floor_violations")):
                                    raise ValueError("Historical fixed-path result not reproduced")
                                audits["original_policy_scores"] += 1
                            if score["donor_floor_violations"] == score["recipient_floor_violations"] == 0:
                                if score["gain"] > current_max:
                                    raise ValueError("A strict saved path exceeds the offline bound")
                                audits["strict_saved_path_bound_checks"] += 1
                            fixed.append({**context, "policy": policy, **score})
        if progress and i % 28 == 0:
            print(f"Metric/contract audit {i}/168 exposed episodes", flush=True)
    return {"exposed_only": True, "fresh_holdout": False, "new_controller_tuned": False,
            "nominal_segment_seconds": 10, "quality_units": dict(zip(METRICS, SCALES)),
            "target_quarters": [1, 2, 3, 4], "fixed_path_rows": fixed, "oracle_rows": oracle,
            "summary": summarize(fixed, oracle), "audits": audits}


def report(result):
    lines = ["# Exposed metric and service-contract sensitivity", "",
             "Fixed paths are rescored, not retuned. Offline bounds know future quality.",
             "No new holdout, player experiment, human-QoE validation or controller success claim.", "",
             "## Original-event, four-segment eventual playback", "",
             "| Metric | Policy | Positive loss / episodes | Mean unpaid | Targets 25/50/75/100% met | Donor/recipient floor violations |",
             "|---|---|---:|---:|---|---:|"]
    for r in result["summary"]:
        if r["group"] == "all" and r["impairment"] == 0 and r["horizon"] == 4 and r["clock"] == "media":
            lines.append(f"| {r['metric']} | {r['policy']} | {r['positive_loss_episodes']}/{r['episodes']} | {r['mean_unpaid']} | "
                         f"{' / '.join(map(str,r['targets_met']))} | {r['donor_floor_violations']}/{r['recipient_floor_violations']} |")
    lines += ["", "## Offline feasibility across contracts", "",
              "Same total four-slot byte reserve for all horizons. Only completed recipient segments count before a deadline.", "",
              "| Metric | Initial rung | H | Contract | Positive loss | Targets 25/50/75/100% feasible | Mean unpaid |",
              "|---|---:|---:|---|---:|---|---:|"]
    for r in result["summary"]:
        if r["group"] == "all" and r["policy"] == "offline":
            lines.append(f"| {r['metric']} | {r['impairment']} | {r['horizon']} | {r['clock']} | {r['positive_loss_episodes']} | "
                         f"{' / '.join(map(str,r['targets_met']))} | {r['mean_unpaid']} |")
    lines += ["", "## Verification", ""]+[f"- {k}: {v}" for k, v in result["audits"].items()]
    lines += ["", "All cohort/scene cells and minimum-cost path witnesses are in results.json.gz.",
              "Targets are accounting choices, not perceptual thresholds. Initial-rung1 fixed paths are counterfactual rescoring only.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if not args.verify and OUT.exists():
        parser.error("Preserve existing results; output already exists")
    before = provenance()
    if args.verify:
        meta = json.loads((OUT/"metadata.json").read_text())
        for key in before:
            if meta[key] != before[key]:
                raise ValueError("Source/input hash mismatch: "+key)
    result = analysis(True)
    digest = hashlib.sha256(canonical(result)).hexdigest()
    text = report(result)
    if args.verify:
        if digest != meta["scientific_sha256"]:
            raise ValueError("Full scientific replay mismatch")
        with gzip.open(OUT/"results.json.gz", "rt") as f:
            if json.load(f) != result:
                raise ValueError("Published result mismatch")
        if (OUT/"REPORT.md").read_text() != text:
            raise ValueError("Report mismatch")
    else:
        OUT.mkdir(parents=True)
        (OUT/"results.json.gz").write_bytes(gzip.compress(canonical(result), mtime=0))
        (OUT/"REPORT.md").write_text(text, encoding="utf-8")
        (OUT/"metadata.json").write_text(json.dumps({**before, "scientific_sha256": digest,
            "result_sha256": sha(OUT/"results.json.gz")}, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"verified": args.verify, "scientific_sha256": digest, "audits": result["audits"],
                      "fixed_rows": len(result["fixed_path_rows"]), "oracle_rows": len(result["oracle_rows"])}))


if __name__ == "__main__":
    main()
