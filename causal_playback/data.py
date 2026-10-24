"""Exposed tables and sender metadata; no media download or current-label access."""
import csv
from dataclasses import dataclass
import json
from causal_compensation.data import ROOT,SOURCES,quality_units,load_episodes,source_paths


@dataclass(frozen=True)
class Record:
    key:str
    cohort:str
    scene:str
    recipient:int
    donor:int
    loss:int
    quality:tuple
    sender:tuple
    costs:tuple


def load(manifest):
    quality={}; sender={}
    for cohort,folder in SOURCES.items():
        for filename in ('calibration_quality.csv','heldout_quality.csv'):
            with (ROOT/folder/filename).open(newline='') as f:
                for r in csv.DictReader(f):
                    quality[cohort,r['content'],int(r['subject']),int(r['segment']),int(r['ladder_index'])]=quality_units(r['vw_psnr_db'])
        with (ROOT/folder/'sender_quality.csv').open(newline='') as f:
            for r in csv.DictReader(f):
                sender[cohort,r['content'],int(r['segment']),int(r['ladder_index'])]=quality_units(r['full_sphere_psnr_db'])
    files={(r['cohort'],r['scene'],r['segment'],r['rung']):r for r in manifest['files']}
    rows=[]
    for e in load_episodes():
        q=tuple(tuple(tuple(quality[e.cohort,e.scene,u,t,r] for r in range(6))
                      for u in (e.recipient,e.donor)) for t in range(6))
        g=tuple(tuple(sender[e.cohort,e.scene,t,r] for r in range(6)) for t in range(6))
        costs=tuple(tuple(files[e.cohort,e.scene,t,r]['bytes'] for r in range(6)) for t in range(6))
        rows.append(Record(e.key,e.cohort,e.scene,e.recipient,e.donor,e.loss,q,g,costs))
    return tuple(rows)


def pool(records,target):
    ids={target.recipient,target.donor}
    result=tuple(r for r in records if r.scene!=target.scene and not ids.intersection((r.recipient,r.donor)))
    if len(result)!=130: raise ValueError('expected scene/identity-disjoint training pool')
    return result


def inputs():
    return (*source_paths(),*(ROOT/folder/'sender_quality.csv' for folder in SOURCES.values()),
            ROOT/'causal_playback/data/media_manifest.json')
