"""Reuse the unchanged episode definitions and read their full encoded ladders."""
import csv
from causal_compensation.data import ROOT,SOURCES,source_paths,quality_units,load_episodes
from feasibility_frontier.core import actions


def load():
    quality,costs={},{}
    for cohort,folder in SOURCES.items():
        for filename in ('calibration_quality.csv','heldout_quality.csv'):
            with (ROOT/folder/filename).open(newline='') as f:
                for row in csv.DictReader(f):
                    key=cohort,row['content'],int(row['subject']),int(row['segment']),int(row['ladder_index'])
                    if key in quality: raise ValueError('duplicate quality key')
                    quality[key]=quality_units(row['vw_psnr_db'])
        with (ROOT/folder/'segment_sizes.csv').open(newline='') as f:
            for row in csv.DictReader(f):
                key=cohort,row['content'],int(row['segment']),int(row['ladder_index'])
                if key in costs: raise ValueError('duplicate byte key')
                costs[key]=int(row['bytes'])
    result=[]
    for e in load_episodes():
        def q(subject,t): return tuple(quality[e.cohort,e.scene,subject,t,r] for r in range(6))
        assert e.loss==sum(max(q(e.recipient,t)[2]-q(e.recipient,t)[0],0) for t in range(2))
        periods=[]
        for t in range(2,6):
            sizes=tuple(costs[e.cohort,e.scene,t,r] for r in range(6))
            p=actions(q(e.recipient,t),q(e.donor,t),sizes)
            assert any(a.rungs==(2,2) and a.gain==a.harm==0 and a.multiplier==1 for a in p)
            periods.append(p)
        result.append((e,tuple(periods)))
    assert len(result)==168
    return tuple(result)
