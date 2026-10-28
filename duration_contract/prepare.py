"""Read-only packet-duration audit of the already cached exposed media."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
from metric_contract.data import ROOT
from metric_contract.run import canonical, sha
from duration_contract.core import packet_timeline, TICKS

OUT = ROOT/"duration_contract/data/media_v1"
CACHE = ROOT/".external/causal_playback_v1"


def prepare(cache=CACHE):
    manifest = json.loads((ROOT/"causal_playback/data/media_manifest.json").read_text())
    rows = []
    for i,item in enumerate(manifest["files"],1):
        path = cache/item["relative_path"]
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise ValueError("Cached media differs from frozen exposed file")
        raw = subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0",
            "-show_packets","-show_entries","packet=pts,duration:stream=time_base,start_pts,duration_ts,nb_frames,width,height,r_frame_rate",
            "-show_streams","-of","json",str(path)], text=True)
        probe = json.loads(raw); stream = probe["streams"][0]
        timeline = packet_timeline(probe["packets"],stream["time_base"])
        if len(timeline["pts_ticks"]) != item["packets"] or int(stream["nb_frames"]) != item["packets"]:
            raise ValueError("Frame/packet count mismatch")
        if timeline["total_ticks"] != int(item["packets"])*TICKS//30 or stream["r_frame_rate"] != "30/1":
            raise ValueError("Unexpected exposed media timeline")
        rows.append({**item, **timeline, "width": stream["width"],"height": stream["height"]})
        if i%36 == 0: print(f"Packet-duration audit {i}/216 files",flush=True)
    groups = {}
    for r in rows: groups.setdefault((r["cohort"],r["scene"],r["segment"]),set()).add(r["total_ticks"])
    if len(groups)!=36 or any(len(v)!=1 for v in groups.values()): raise ValueError("Representation duration mismatch")
    return {"existing_exposed_only": True, "reencoded": False, "rows": rows,
            "ffprobe": subprocess.check_output(["ffprobe","-version"],text=True).splitlines()[0],
            "manifest_sha256": sha(ROOT/"causal_playback/data/media_manifest.json"),
            "script_sha256": sha(Path(__file__))}


if __name__ == "__main__":
    p=argparse.ArgumentParser(__doc__); a=p.parse_args()
    if OUT.exists(): p.error("Preserve previous media audit")
    result=prepare(); OUT.mkdir(parents=True)
    (OUT/"timelines.json.gz").write_bytes(gzip.compress(canonical(result),mtime=0))
    print(json.dumps({"files":len(result["rows"]),"short_segments":sum(r["total_ticks"]!=10*TICKS for r in result["rows"])}))
