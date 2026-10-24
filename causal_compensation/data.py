"""Read only already published objective-quality tables; never download media."""
import csv
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {'v2': 'feasibility_recovery/data/v2', 'v3': 'horizon_recovery/data/v3'}


def quality_units(value):
    q = max(Decimal(1), min(Decimal(5), Decimal(1)+(Decimal(value)-18)/6))
    return int((q*1000).quantize(Decimal(1), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Offer:
    reference: tuple
    transfer: tuple
    gain: int
    harm: int
    baseline_bytes: int
    transfer_bytes: int
    rungs: tuple


@dataclass(frozen=True)
class Episode:
    cohort: str
    scene: str
    recipient: int
    donor: int
    loss: int
    history: tuple
    offers: tuple

    @property
    def key(self): return f'{self.cohort}:{self.scene}:{self.recipient}:{self.donor}'


def source_paths():
    return tuple(ROOT/folder/name for folder in SOURCES.values()
                 for name in ('calibration_quality.csv', 'heldout_quality.csv', 'segment_sizes.csv'))


def make_offer(recipient, donor, sizes):
    ref, budget = (recipient[2], donor[2]), 2*sizes[2]
    choices = []
    for r in (3,4,5):
        for d in (0,1):
            gain, harm = recipient[r]-ref[0], max(0, ref[1]-donor[d])
            cost = sizes[r]+sizes[d]
            if gain > 0 and harm <= 500 and cost <= budget:
                choices.append((-gain, harm, cost, r, d))
    if not choices: return Offer(ref, ref, 0, 0, budget, budget, (2,2))
    negative_gain, harm, cost, r, d = min(choices)
    return Offer(ref, (recipient[r], donor[d]), -negative_gain, harm, budget, cost, (r,d))


def load_episodes():
    episodes = []
    for cohort, folder in SOURCES.items():
        folder = ROOT/folder
        labels, sizes = {}, {}
        for name in ('calibration_quality.csv', 'heldout_quality.csv'):
            with (folder/name).open(newline='') as f:
                for row in csv.DictReader(f):
                    key = row['content'], int(row['subject']), int(row['segment']), int(row['ladder_index'])
                    if key in labels: raise ValueError('duplicate quality key')
                    labels[key] = quality_units(row['vw_psnr_db'])
        with (folder/'segment_sizes.csv').open(newline='') as f:
            for row in csv.DictReader(f):
                key = row['content'], int(row['segment']), int(row['ladder_index'])
                if key in sizes: raise ValueError('duplicate byte key')
                sizes[key] = int(row['bytes'])
        scenes = sorted({k[0] for k in labels})
        ids = sorted({k[1] for k in labels})
        if len(scenes) != 3 or ids != list(range(1,29)) or len(labels) != 3*28*6*6:
            raise ValueError('unexpected exposed catalogue shape')
        for scene in scenes:
            for a,b in zip(ids[::2], ids[1::2]):
                for recipient, donor in ((a,b),(b,a)):
                    offers, history, loss = [], [], 0
                    for t in range(6):
                        rq = tuple(labels[scene,recipient,t,r] for r in range(6))
                        dq = tuple(labels[scene,donor,t,r] for r in range(6))
                        cost = tuple(sizes[scene,t,r] for r in range(6))
                        offers.append(make_offer(rq,dq,cost))
                        if t < 2:
                            history.append((rq[0],dq[2])); loss += max(rq[2]-rq[0],0)
                    episodes.append(Episode(cohort,scene,recipient,donor,loss,tuple(history),tuple(offers)))
    return tuple(episodes)
