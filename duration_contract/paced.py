"""Real decode availability and monotonic PTS pacing; no pixel rendering or network."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from fractions import Fraction
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import queue
import subprocess
import threading
import time
from metric_contract.data import ROOT,load
from metric_contract.run import canonical,sha
from duration_contract.core import frame_record,pacing_step,ticks,TICKS
from duration_contract.prepare import CACHE
from duration_contract.run import media_rows,schedule,inputs

OUT=ROOT/"duration_contract/results/paced_v1"
NS=1000000000


def ns(tick):return (int(tick)*NS+TICKS//2)//TICKS


def sleep_until(target,stop):
    while True:
        if stop.is_set():raise RuntimeError("Timing session stopped")
        delay=(target-time.perf_counter_ns())/NS
        if delay<=0:return
        time.sleep(min(delay,.1))


def run_session(record,policy,media,negative=False):
    choices,arrivals=schedule(record,policy)
    if negative:arrivals=[[x+(40*TICKS if u==0 else 0) for u,x in enumerate(pair)] for pair in arrivals]
    selected=[[media[record["cohort"],record["scene"],t,r] for r in pair] for t,pair in zip(range(2,6),choices)]
    for pair in selected:
        for m in pair:
            path=CACHE/m["relative_path"]
            if sha(path)!=m["sha256"] or path.stat().st_size!=m["bytes"]:raise ValueError("Preflight file identity mismatch")
    stop=threading.Event(); lock=threading.Lock(); processes=[]; queues=[[queue.Queue() for u in (0,1)] for j in range(4)]
    frames=[[],[]]; segments=[[],[]]; decoders={}; epoch=time.perf_counter_ns()+300000000

    def decode(j,u):
        m=selected[j][u]; q=queues[j][u]; proc=None; emitted=0; tb=None; first=None
        release=ns(arrivals[j][u]); stderr=""
        try:
            sleep_until(epoch+release,stop); launched=time.perf_counter_ns()-epoch
            command=["ffmpeg","-nostdin","-v","error","-threads","1","-i",str(CACHE/m["relative_path"]),
                     "-map","0:v:0","-threads:v","1","-f","framehash","-hash","md5","-flush_packets","1","pipe:1"]
            proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
            with lock:processes.append(proc)
            for line in proc.stdout:
                if stop.is_set():raise RuntimeError("Decoder canceled")
                if line.startswith("#tb 0:"):tb=Fraction(line.split(":",1)[1].strip());continue
                if line.startswith("#") or not line.strip():continue
                if tb is None:raise ValueError("Missing decoder timebase")
                value=frame_record(line);ready=time.perf_counter_ns()-epoch
                if first is None:first=value["pts"]
                p,d=ticks((value["pts"]-first)*tb),ticks(value["duration"]*tb)
                if emitted>=len(m["pts_ticks"]) or (p,d)!=(m["pts_ticks"][emitted],m["duration_ticks"][emitted]):
                    raise ValueError("Decoded PTS differ from packet presentation timeline")
                q.put({"frame":emitted,"pts_ticks":p,"duration_ticks":d,"ready_ns":ready,"md5":value["md5"],"decoded_bytes":value["size"]})
                emitted+=1
            stderr=proc.stderr.read(); code=proc.wait(timeout=10)
            if code or stderr.strip() or emitted!=m["packets"]:raise ValueError("Decoder error/count mismatch: "+stderr[:300])
            decoders[f"{j}:{u}"]={"release_ns":release,"launched_ns":launched,"finished_ns":time.perf_counter_ns()-epoch,
                                   "frames":emitted,"returncode":code,"stderr":stderr,"file":m["relative_path"],"file_sha256":m["sha256"]}
        except BaseException as exc:
            q.put({"error":str(exc)});raise
        finally:
            q.put(None)
            if proc is not None and proc.poll() is None:proc.kill();proc.wait()

    def consume(u):
        cursor=0
        for j in range(4):
            m=selected[j][u]; q=queues[j][u]; first_index=len(frames[u])
            for i in range(m["packets"]):
                while True:
                    if stop.is_set():raise RuntimeError("Consumer canceled")
                    try: value=q.get(timeout=.5);break
                    except queue.Empty:continue
                if value is None or "error" in value:raise ValueError("Incomplete decoder stream: "+str(value))
                duration_ns=ns(value["pts_ticks"]+value["duration_ticks"])-ns(value["pts_ticks"])
                target=max(cursor,value["ready_ns"]);sleep_until(epoch+target,stop)
                pacing=pacing_step(cursor,value["ready_ns"],time.perf_counter_ns()-epoch)
                frames[u].append({"segment":j+2,**value,"duration_ns":duration_ns,"prior_end_ns":cursor,**pacing})
                cursor=pacing["present_ns"]+duration_ns
            expected=cursor;sleep_until(epoch+expected,stop);cursor=time.perf_counter_ns()-epoch
            segments[u].append({"segment":j+2,"rung":choices[j][u],"first_frame_index":first_index,
                                "frames":m["packets"],"end_ns":cursor,"boundary_late_ns":cursor-expected,
                                "duration_ticks":m["total_ticks"]})
        return cursor

    pool=ThreadPoolExecutor(max_workers=10); status="passed";error=None
    jobs=[pool.submit(decode,j,u) for j in range(4) for u in (0,1)]+[pool.submit(consume,u) for u in (0,1)]
    try:
        done,pending=wait(jobs,timeout=150)
        if pending:raise TimeoutError("150-second session watchdog")
        for job in jobs:job.result()
    except BaseException as exc:status="failed";error=repr(exc)
    finally:
        stop.set()
        with lock:
            for proc in processes:
                if proc.poll() is None:proc.kill()
        pool.shutdown(wait=True)
    return {"key":record["key"],"scene":record["scene"],"policy":policy,"negative_control":negative,
            "status":status,"error":error,"choices":choices,"scripted_arrivals_ticks":arrivals,
            "frames":frames,"segments":segments,"decoders":decoders,
            "scope":"software decode/hash and no-drop PTS pacing; scripted arrival, no pixel render or network"}


def planned(records):
    selected=sorted((r for r in records if r["key"].endswith(":1:2")),key=lambda r:r["scene"])
    policies=("prefix_mpc","prefix_cost_greedy","baseline");out=[]
    for i,r in enumerate(selected):
        for j in range(3):out.append((r,policies[(i+j)%3],False))
    out.append((next(r for r in selected if r["scene"]=="ParkFountains01"),"prefix_mpc",True))
    if len(out)!=19:raise ValueError("Fixed 19-session plan mismatch")
    return out


if __name__=="__main__":
    p=argparse.ArgumentParser(__doc__);a=p.parse_args()
    if OUT.exists():p.error("Preserve all measured attempts; no automatic overwrite/resume")
    records,_=load();media=media_rows();schedule_rows=planned(records);OUT.mkdir(parents=True)
    metadata={**inputs(),"platform":platform.platform(),"python":platform.python_version(),
        "ffmpeg":subprocess.check_output(["ffmpeg","-version"],text=True).splitlines()[0],"max_concurrent_sessions":2,
        "logical_cpu_count":os.cpu_count(),"decoder_threads_per_file":1,"raw_encoder_threads_per_file":1,
        "schedule":[{"index":i,"key":r["key"],"policy":p,"negative":n} for i,(r,p,n) in enumerate(schedule_rows)]}
    (OUT/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    results=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(run_session,r,p,media,n):i for i,(r,p,n) in enumerate(schedule_rows)}
        for job in as_completed(jobs):
            i=jobs[job]
            try:row=job.result()
            except BaseException as exc:
                r,p,n=schedule_rows[i]
                row={"key":r["key"],"scene":r["scene"],"policy":p,"negative_control":n,
                     "status":"failed","error":repr(exc),"frames":[[],[]],"segments":[[],[]],"decoders":{}}
            row["index"]=i
            (OUT/f"session_{i:02}.json.gz").write_bytes(gzip.compress(canonical(row),mtime=0))
            results.append({"index":i,"status":row["status"],"error":row["error"]})
            print(f"Paced session {i+1}/19 {row['scene']} {row['policy']}: {row['status']}",flush=True)
    (OUT/"completion.json").write_text(json.dumps(sorted(results,key=lambda r:r["index"]),indent=2)+"\n")
    if any(r["status"]!="passed" for r in results):raise RuntimeError("Measured session failures retained; not valid timing evidence")
