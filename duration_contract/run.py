"""Exact-duration replay of frozen actions and independently checked offline bounds."""
import argparse
from collections import defaultdict
import gzip
import hashlib
from itertools import product
import json
from statistics import mean
import numpy as np
from metric_contract.data import ROOT, INPUTS, load
from metric_contract.core import path_arrays, offsets, SLOT, TICKS, CAP
from metric_contract.run import canonical, sha
from duration_contract.core import playback, account, baseline_arrivals, oracle

OUT=ROOT/"duration_contract/results/replay_v1"
MEDIA=ROOT/"duration_contract/data/media_v1/timelines.json.gz"
OWN=("__init__.py","core.py","prepare.py","run.py","paced.py","audit.py","test_core.py","PLAN.md")


def inputs():
    return {"source_sha256":{"duration_contract/"+p:sha(ROOT/"duration_contract"/p) for p in OWN},
            "input_sha256":{p:sha(ROOT/p) for p in INPUTS},
            "dependency_sha256":{p:sha(ROOT/p) for p in ("metric_contract/core.py","metric_contract/data.py","metric_contract/run.py")},
            "media_audit_sha256":sha(MEDIA)}


def media_rows():
    with gzip.open(MEDIA,"rt") as f: audit=json.load(f)
    return {(r["cohort"],r["scene"],r["segment"],r["rung"]):r for r in audit["rows"]}


def durations_for(record,media,mode="actual"):
    return [media[record["cohort"],record["scene"],t,2]["total_ticks"] if mode=="actual" else SLOT for t in range(6)]


def schedule(record,policy):
    if policy=="baseline":
        return [[2,2] for _ in range(4)],baseline_arrivals(record["costs"])
    saved=record["policies"][policy]
    return [r["decision"]["rungs"] for r in saved["rounds"]],[[round(x*TICKS) for x in r["arrivals"]] for r in saved["rounds"]]


def secondary_psnr(quality,durations,choices):
    if quality.shape != (4,6,2,6):raise ValueError("Metric/segment/user/rung axes required")
    return [sum(int(quality[2,t,u,pair[u]])*durations[t] for t,pair in zip(range(2,6),choices))
            /sum(durations[2:])/1e6 for u in (0,1)]


def scalar_bound(q,costs,durations,reserve):
    """Independent recursion; no vector path arrays or vector clock."""
    best={"deadline":0,"eventual":0}; costs_at_half={"deadline":None,"eventual":None}; count=0
    loss=sum(max(0,int(q[t,0,2]-q[t,0,0]))*durations[t] for t in (0,1))
    def walk(t,spent,clock,ends,credited,total):
        nonlocal count
        if t==6:
            count+=1
            for name,gain in (("deadline",credited),("eventual",total)):
                best[name]=max(best[name],gain)
                if 2*gain>=loss and (costs_at_half[name] is None or spent<costs_at_half[name]): costs_at_half[name]=spent
            return
        for a,b in product(range(2,6),repeat=2):
            sa,sb=int(costs[t,a]),int(costs[t,b]); extra=max(0,sa+sb-2*int(costs[t,2]))
            if sa+sb>CAP or spent+extra>reserve or q[t,0,a]<q[t,0,2] or q[t,1,b]<q[t,1,2]: continue
            ar=[clock+19500+(2*n if n==min(sa,sb) else sa+sb) for n in (sa,sb)]
            end=[max(ends[u],ar[u])+durations[t] for u in (0,1)]
            g=max(0,int(q[t,0,a]-q[t,0,2]))*durations[t]
            walk(t+1,spent+extra,max(clock+SLOT,*ar),end,credited+(g if end[0]<=40*TICKS else 0),total+g)
    walk(2,0,0,[0,0],0,0)
    return best,costs_at_half,count


def summary(rows):
    groups=defaultdict(list)
    for r in rows:
        for g in ("all",r["cohort"],r["scene"]):groups[g,r["mode"],r["policy"]].append(r)
    return [{"group":g,"mode":m,"policy":p,"episodes":len(rs),
             "half_by_deadline":sum(r["half_by_deadline"] for r in rs),
             "protected_half":sum(r["protected_half_by_deadline"] for r in rs),
             **{k:round(mean(r[k] for r in rs),12) for k in ("deadline_unpaid","eventual_unpaid","mean_finish_seconds","mean_wait_seconds","worst_eventual_psnr_db")},
             "donor_floor_violations":sum(r["donor_floor_violations"] for r in rs),
             "recipient_floor_violations":sum(r["recipient_floor_violations"] for r in rs)}
            for (g,m,p),rs in sorted(groups.items())]


def analysis():
    records,_=load(); media=media_rows(); rows=[]; bounds=[]; parity=0
    with gzip.open(ROOT/"metric_contract/results/sensitivity_v1/results.json.gz","rt") as f: old=json.load(f)
    oldpaths={(r["key"],r["policy"],r["clock"]):r for r in old["fixed_path_rows"]
              if r["metric"]=="negative_mse" and r["impairment"]==0 and r["horizon"]==4}
    for i,r in enumerate(records,1):
        arrays=path_arrays(r["costs"],4,r["reserve"])
        for mode in ("nominal","actual"):
            ds=durations_for(r,media,mode); base={k:r[k] for k in ("key","cohort","scene")}
            for policy in sorted(r["policies"])+["baseline"]:
                choices,arrivals=schedule(r,policy); timing=playback(arrivals,ds[2:])
                ends=[x["end_ticks"] for x in timing["segments"]]
                result=account(r["quality"][3],ds,choices,ends)
                if mode=="nominal" and policy!="baseline":
                    for clock,name in (("deadline","deadline_unpaid"),("media","eventual_unpaid")):
                        if result[name]!=oldpaths[r["key"],policy,clock]["unpaid"]:raise ValueError("Historical MSE score mismatch")
                        parity+=1
                means=secondary_psnr(r["quality"],ds,choices)
                rows.append({**base,"mode":mode,"policy":policy,"choices":choices,"arrivals":arrivals,
                    "durations":ds,"timing":timing,**result,
                    "mean_finish_seconds":sum(timing["finish_ticks"])/2/TICKS,
                    "mean_wait_seconds":sum(timing["wait_ticks"])/2/TICKS,"worst_eventual_psnr_db":min(means)})
            b=oracle(r["quality"][3],r["costs"],ds,arrays["choices"],arrays["cost"])
            independently,costs,count=scalar_bound(r["quality"][3],r["costs"],ds,r["reserve"])
            if b["strict_paths"]!=count or any(b[n]["gain"]!=independently[n] or b[n]["half_min_extra_bytes"]!=costs[n] for n in independently):
                raise ValueError("Independent duration-bound mismatch")
            bounds.append({**base,"mode":mode,**b})
        if i%28==0:print(f"Actual-duration replay {i}/168",flush=True)
    return {"exposed_only":True,"retuned":False,"deadline_seconds":40,"rows":rows,"bounds":bounds,
            "summary":summary(rows),"checks":{"nominal_score_parity":parity,"scalar_bound_queries":len(bounds)},
            "quality_contract":"completed-segment sampled distortion-seconds; not human QoE"}


def report(result):
    lines=["# Engineering contract: actual-duration replay","","Frozen actions; sampled distortion-seconds credited only on completed playback by40s.","",
           "| Duration | Policy | Half /168 | Protected half | Deadline unpaid | Eventual unpaid | Mean finish s | Donor/recipient floor losses |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in result["summary"]:
        if r["group"]=="all":lines.append(f"| {r['mode']} | {r['policy']} | {r['half_by_deadline']} | {r['protected_half']} | {r['deadline_unpaid']:.6f} | {r['eventual_unpaid']:.6f} | {r['mean_finish_seconds']:.6f} | {r['donor_floor_violations']}/{r['recipient_floor_violations']} |")
    for mode in ("nominal","actual"):
        rs=[r for r in result["bounds"] if r["mode"]==mode]
        lines += ["",f"{mode} strict future-known bound: deadline half {sum(r['deadline']['half'] for r in rs)}/168; eventual half {sum(r['eventual']['half'] for r in rs)}/168; mean deadline unpaid {mean(r['deadline']['unpaid'] for r in rs):.9f}."]
    return "\n".join(lines)+"\n"


if __name__=="__main__":
    p=argparse.ArgumentParser(__doc__);p.add_argument("--verify",action="store_true");a=p.parse_args()
    prov={**inputs(),"metric_sensitivity_sha256":sha(ROOT/"metric_contract/results/sensitivity_v1/results.json.gz")}
    if a.verify:
        meta=json.loads((OUT/"metadata.json").read_text())
        if any(meta[k]!=v for k,v in prov.items()):raise ValueError("Provenance mismatch")
    elif OUT.exists():p.error("Preserve prior results")
    result=analysis(); digest=hashlib.sha256(canonical(result)).hexdigest(); text=report(result)
    if a.verify:
        with gzip.open(OUT/"results.json.gz","rt") as f: saved=json.load(f)
        if result!=saved or digest!=meta["scientific_sha256"] or (OUT/"REPORT.md").read_text()!=text:raise ValueError("Replay mismatch")
    else:
        OUT.mkdir(parents=True);(OUT/"results.json.gz").write_bytes(gzip.compress(canonical(result),mtime=0))
        (OUT/"REPORT.md").write_text(text,encoding="utf-8")
        (OUT/"metadata.json").write_text(json.dumps({**prov,"scientific_sha256":digest},indent=2)+"\n")
    print(json.dumps({"verified":a.verify,"scientific_sha256":digest,"rows":len(result['rows']),"checks":result["checks"]}))
