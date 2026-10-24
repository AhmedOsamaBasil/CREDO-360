"""Display the frozen exact frontier results without altering scientific outputs."""
import argparse
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from feasibility_frontier.run import ROOT,sha


def curve(rows,m,e,b,limit):
    values=[]
    for row in rows:
        point=next((p for p in row['frontiers'][f'{m}:{e}'] if p['donor_total_units']<=b),None)
        if point is not None: values.append(F(point['peak_multiplier']))
    x=sorted({F(1),F(str(limit)),*(v for v in values if v<=F(str(limit)))})
    return [float(v) for v in x],[sum(r<=v for r in values) for v in x],len(values)


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--results',type=Path,default=ROOT/'feasibility_frontier/results/audit_v1')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(); output=args.output or args.results/'figures'
    if output.exists(): parser.error('output exists; preserve previous figures')
    with gzip.open(args.results/'results.json.gz','rt') as f: payload=json.load(f)
    plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.spines.top':False,
                         'axes.spines.right':False,'svg.hashsalt':'feasibility-frontier-v1'})
    fig,axes=plt.subplots(1,2,figsize=(12.5,5.4),sharey=True)
    colors=('#bf6c19','#168580','#244f83','#80549e')
    for m,c in zip((1,2,4),colors):
        x,y,n=curve(payload['rows'],m,0,0,12)
        axes[0].step(x,y,where='post',lw=2.1,color=c,label=f'M={m}; ceiling {n}/168')
    axes[0].set_title('(a) Recovery-action limit; zero donor loss')
    axes[0].set_xlim(1,12); axes[0].set_xticks((1,2,3,4,6,8,10,12))
    for e,b,label,c,style in ((0,0,'No donor loss',colors[2],'-'),
            (500,1000,'Step 0.5; total 1',colors[1],'--'),
            (1000,4000,'Step 1; total 4',colors[0],'-.'),
            (4000,16000,'Donor caps fully relaxed',colors[3],':')):
        x,y,n=curve(payload['rows'],4,e,b,3.5)
        axes[1].step(x,y,where='post',lw=2.1,color=c,ls=style,label=label)
    axes[1].set_title('(b) Donor-loss allowances; M=4')
    axes[1].set_xlim(1,3.5); axes[1].set_xticks((1,1.5,2,2.5,3,3.5))
    for ax in axes:
        ax.set_ylim(0,175); ax.set_yticks((0,42,84,126,168))
        ax.set_xlabel('Peak per-segment byte allowance / original pair baseline')
        ax.grid(axis='y',alpha=.18); ax.set_axisbelow(True)
        ax.axhline(157,color='#77818b',ls=':',lw=1,zorder=0)
        ax.legend(loc='lower right',fontsize=9,framealpha=.96)
    axes[0].set_ylabel('Episodes with feasible half-repayment (of 168)')
    fig.suptitle('Recovery requires substantial resource headroom in the exposed catalogue',
                 fontsize=14,x=.06,ha='left',y=.98)
    fig.text(.06,.91,'Exact future-known schedules; unchanged losses and recipient service floors. Not online success rates.',
             fontsize=10,color='#45515c')
    fig.text(.06,.035,'M counts positive-gain recovery actions in four segments. Donor loss uses the objective index, not MOS.\n'
             'Dotted horizontal reference: 157/168 catalogue ceiling; eleven episodes remain impossible at any allowance.',
             fontsize=9,color='#45515c')
    fig.subplots_adjust(left=.075,right=.98,bottom=.21,top=.81,wspace=.15)
    output.mkdir(parents=True)
    fig.savefig(output/'feasibility_frontier.png',dpi=180)
    fig.savefig(output/'feasibility_frontier.svg',metadata={'Date':None})
    plt.close(fig)
    meta={'renderer_sha256':sha(Path(__file__)),
          'scientific_results_sha256':sha(args.results/'results.json.gz'),
          'matplotlib':matplotlib.__version__,
          'figure_sha256':{p.name:sha(p) for p in sorted(output.iterdir())}}
    (output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')


if __name__=='__main__': main()
