"""Independent frame-event/contract audit of published real-time timing records."""
import argparse
import gzip
import hashlib
import json
from math import ceil
from statistics import mean
from metric_contract.data import ROOT,load
from metric_contract.run import canonical,sha
from duration_contract.core import TICKS,account,playback
from duration_contract.run import inputs,media_rows,durations_for,schedule

RAW=ROOT/"duration_contract/results/paced_v1"
OUT=ROOT/"duration_contract/results/measured_audit_v1"


def audit_session(row,record,media):
    if row["status"]!="passed" or row["error"] is not None:raise ValueError("Invalid measured session retained")
    choices,arrivals=schedule(record,row["policy"])
    if row["negative_control"]:arrivals=[[x+(40*TICKS if u==0 else 0) for u,x in enumerate(a)] for a in arrivals]
    if row["choices"]!=choices or row["scripted_arrivals_ticks"]!=arrivals:raise ValueError("Session changed fixed schedule")
    ns=lambda tick:(int(tick)*1000000000+TICKS//2)//TICKS
    finishes=[];playerstats=[];count=0;alllate=[];ends=[[0,0] for _ in range(4)]
    for u in (0,1):
        cursor=0;position=0;media_total=wait_total=late_total=0;startup=None
        if len(row["segments"][u])!=4:raise ValueError("Missing segment")
        for j,t in enumerate(range(2,6)):
            meta=media[record["cohort"],record["scene"],t,choices[j][u]]
            segment=row["segments"][u][j];decoder=row["decoders"][f"{j}:{u}"]
            if decoder["release_ns"]!=ns(arrivals[j][u]) or decoder["launched_ns"]<decoder["release_ns"]:
                raise ValueError("Premature decoder launch")
            if decoder["returncode"]!=0 or decoder["stderr"] or decoder["frames"]!=meta["packets"] or decoder["file_sha256"]!=meta["sha256"]:
                raise ValueError("Decoder identity/count/error mismatch")
            if segment["first_frame_index"]!=position or segment["frames"]!=meta["packets"] or segment["duration_ticks"]!=meta["total_ticks"]:
                raise ValueError("Segment timeline mismatch")
            for i in range(meta["packets"]):
                event=row["frames"][u][position];position+=1;count+=1
                p,d=meta["pts_ticks"][i],meta["duration_ticks"][i]
                if (event["segment"],event["frame"],event["pts_ticks"],event["duration_ticks"])!=(t,i,p,d):raise ValueError("Dropped/reordered frame")
                duration=ns(p+d)-ns(p)
                if event["duration_ns"]!=duration or event["decoded_bytes"]!=meta["width"]*meta["height"]*3//2:raise ValueError("Wrong raw frame duration/size")
                if len(event["md5"])!=32 or any(c not in "0123456789abcdef" for c in event["md5"]):raise ValueError("Invalid frame digest")
                if not decoder["launched_ns"]<=event["ready_ns"]<=decoder["finished_ns"]:raise ValueError("Frame availability outside decoder lifetime")
                target=max(cursor,event["ready_ns"])
                if event["prior_end_ns"]!=cursor or event["target_ns"]!=target or event["present_ns"]<target:raise ValueError("Early/overlapping presentation")
                gap=target-cursor;late=event["present_ns"]-target
                if gap!=event["decoder_wait_ns"] or late!=event["pacing_late_ns"]:raise ValueError("Delay accounting mismatch")
                if startup is None:startup=event["present_ns"]
                media_total+=duration;wait_total+=gap;late_total+=late;alllate.append(late)
                cursor=event["present_ns"]+duration
            if segment["end_ns"]<cursor or segment["boundary_late_ns"]!=segment["end_ns"]-cursor:raise ValueError("Premature segment completion")
            late_total+=segment["boundary_late_ns"];cursor=segment["end_ns"]
            ends[j][u]=(cursor*TICKS+999999999)//1000000000
        if position!=len(row["frames"][u]) or cursor!=media_total+wait_total+late_total:raise ValueError("Playback conservation failure")
        finishes.append(cursor/1e9)
        playerstats.append({"finish_ns":cursor,"media_ns":media_total,"decoder_wait_ns":wait_total,
                            "pacing_late_ns":late_total,"startup_ns":startup,"later_delay_ns":cursor-media_total-startup})
    ds=durations_for(record,media);scores=account(record["quality"][3],ds,choices,ends)
    ideal=playback(arrivals,ds[2:]);expected=account(record["quality"][3],ds,choices,[s["end_ticks"] for s in ideal["segments"]])
    if row["negative_control"] and scores["deadline_credit"]!=0:raise ValueError("Late-release control credited before playback")
    return {"index":row["index"],"key":row["key"],"scene":row["scene"],"policy":row["policy"],
            "negative_control":row["negative_control"],"frames_checked":count,"player_stats":playerstats,**scores,
            "ideal_account":expected,"mean_finish_seconds":mean(finishes),
            "mean_added_finish_vs_ideal_seconds":mean(finishes)-mean(ideal["finish_ticks"])/TICKS,
            "mean_startup_seconds":mean(s["startup_ns"] for s in playerstats)/1e9,
            "mean_later_delay_seconds":mean(s["later_delay_ns"] for s in playerstats)/1e9,
            "max_frame_pacing_late_ms":max(alllate)/1e6,
            "p95_frame_pacing_late_ms":sorted(alllate)[ceil(.95*len(alllate))-1]/1e6,
            "recipient_completed_segments_by_deadline":sum(e[0]<=40*TICKS for e in ends)}


def analysis():
    meta=json.loads((RAW/"metadata.json").read_text())
    if any(meta[k]!=v for k,v in inputs().items()):raise ValueError("Frozen source/input mismatch")
    records,_=load();bykey={r["key"]:r for r in records};media=media_rows();rows=[];hashes={}
    completion=json.loads((RAW/"completion.json").read_text())
    if len(completion)!=19 or any(r["status"]!="passed" for r in completion):raise ValueError("Incomplete or failed fixed batch")
    for item in meta["schedule"]:
        path=RAW/f"session_{item['index']:02}.json.gz"
        with gzip.open(path,"rt") as stream:row=json.load(stream)
        if (row["key"],row["policy"],row["negative_control"],row["index"])!=(item["key"],item["policy"],item["negative"],item["index"]):raise ValueError("Schedule mismatch")
        rows.append(audit_session(row,bykey[row["key"]],media));hashes[path.name]=sha(path)
    groups=[]
    for policy in ("prefix_mpc","prefix_cost_greedy","baseline"):
        selected=[r for r in rows if r["policy"]==policy and not r["negative_control"]]
        groups.append({"policy":policy,"sessions":len(selected),"half":sum(r["half_by_deadline"] for r in selected),
            "protected_half":sum(r["protected_half_by_deadline"] for r in selected),
            **{k:mean(r[k] for r in selected) for k in ("deadline_unpaid","mean_finish_seconds","mean_added_finish_vs_ideal_seconds","mean_startup_seconds","mean_later_delay_seconds")}})
    return {"scope":"measured decode/hash and software pacing; scripted arrivals; not rendering/HMD/network",
            "rows":rows,"summary":groups,"sessions":19,"frames_checked":sum(r["frames_checked"] for r in rows),
            "raw_sha256":hashes,"source_sha256":meta["source_sha256"],"negative_control_pass":True}


def report(result):
    lines=["# Measured decode-and-PTS-paced timing","",result["scope"],"",
           "18 nominal sessions (six fixed directed pairs), plus one late-release negative control. Not the full168 population.","",
           "| Policy | Sessions | Half by40s | Protected half | Mean unpaid | Added finish vs ideal s | Startup s | Later delay s |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in result["summary"]:lines.append(f"| {r['policy']} | {r['sessions']} | {r['half']} | {r['protected_half']} | {r['deadline_unpaid']:.6f} | {r['mean_added_finish_vs_ideal_seconds']:.6f} | {r['mean_startup_seconds']:.6f} | {r['mean_later_delay_seconds']:.6f} |")
    lines += ["",f"All {result['frames_checked']} frame events and all152 segment records pass the independent timing/identity audit.",
              "The late-release control earns zero recipient credit before40s. Full scalar records are retained.",""]
    return "\n".join(lines)


if __name__=="__main__":
    p=argparse.ArgumentParser(__doc__);p.add_argument("--verify",action="store_true");a=p.parse_args()
    result=analysis();digest=hashlib.sha256(canonical(result)).hexdigest();text=report(result)
    if a.verify:
        if json.loads((OUT/"results.json").read_text())!=result or (OUT/"REPORT.md").read_text()!=text:raise ValueError("Measured audit mismatch")
        meta=json.loads((OUT/"metadata.json").read_text())
        if meta["scientific_sha256"]!=digest:raise ValueError("Audit hash mismatch")
    else:
        OUT.mkdir(parents=True,exist_ok=False);(OUT/"results.json").write_text(json.dumps(result,indent=2)+"\n")
        (OUT/"REPORT.md").write_text(text);(OUT/"metadata.json").write_text(json.dumps({"scientific_sha256":digest},indent=2)+"\n")
    print(json.dumps({"verified":a.verify,"scientific_sha256":digest,"frames":result['frames_checked'],"summary":result["summary"]}))
