"""Visualize the frozen reserve grid; no result selection or method alteration."""
import argparse
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reserve_recovery.run import ROOT,sha
from reserve_recovery.catalogue import FRACTIONS,BASELINES


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'reserve_recovery/results/analysis_v1/figures')
    args=parser.parse_args()
    if args.output.exists(): parser.error('preserve previous figures; choose new output')
    source=ROOT/'reserve_recovery/results/analysis_v1/results.json.gz'
    with gzip.open(source,'rt') as f: p=json.load(f)
    cells=p['catalogue']['summary']['all']['cells']; names=BASELINES+('offline',)
    labels=('Rolling Nash','Rolling max-min','Greedy recovery','Future-known oracle')
    plt.rcParams.update({'font.size':11,'svg.hashsalt':'recovery-reserve-v1'})
    fig,axes=plt.subplots(1,2,figsize=(11.8,4.9),sharey=True)
    for ax,peak in zip(axes,(3,4)):
        values=np.array([[next(c['half_repaid'] for c in cells if F(c['peak'])==peak
            and F(c['reserve_fraction'])==rho and c['policy']==name) for rho in FRACTIONS] for name in names])
        im=ax.imshow(values,vmin=0,vmax=168,cmap='Blues',aspect='auto')
        for y in range(4):
            for x in range(5): ax.text(x,y,str(values[y,x]),ha='center',va='center',
                color='white' if values[y,x]>90 else '#182533',fontsize=12)
        ax.set_xticks(range(5),('0','0.25','0.5','1','2'))
        ax.set_yticks(range(4),labels); ax.tick_params(length=0,pad=8)
        ax.set_xlabel('Cumulative extra reserve / total baseline bytes',labelpad=10)
        ax.set_title(f'Per-slot byte cap: {peak}x baseline',pad=13)
        for spine in ax.spines.values(): spine.set_visible(False)
    fig.suptitle('Recovery under simultaneous peak and cumulative byte limits',fontsize=15,x=.02,ha='left',y=.98)
    fig.text(.02,.88,'Cells: episodes repaying at least half the original loss, out of 168 exposed episodes. Donor quality is protected.',fontsize=10)
    fig.text(.02,.04,'Peak factors 1x and 2x yield zero target attainment at every tested reserve. Oracle uses future qualities; other rows do not.\n'
             'These are exact catalogue calculations, not network trials or measured human QoE. No fitted causal planner is evaluated here.',fontsize=9,color='#45515c')
    fig.subplots_adjust(left=.175,right=.91,top=.75,bottom=.27,wspace=.14)
    cax=fig.add_axes((.93,.27,.017,.48)); fig.colorbar(im,cax=cax,ticks=(0,42,84,126,168))
    args.output.mkdir(parents=True)
    fig.savefig(args.output/'reserve_grid.png',dpi=180)
    fig.savefig(args.output/'reserve_grid.svg',metadata={'Date':None})
    plt.close(fig)
    meta={'renderer_sha256':sha(Path(__file__)),'scientific_results_sha256':sha(source),
          'matplotlib':matplotlib.__version__,'figure_sha256':{f.name:sha(f) for f in args.output.iterdir()}}
    (args.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')


if __name__=='__main__': main()
