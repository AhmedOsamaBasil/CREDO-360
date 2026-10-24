"""Render stored measurements and exposed-development results only."""
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from service_opportunity.model import ROOT
from reserve_recovery.run import sha


def main():
    base=ROOT/'service_opportunity/results/development_v1'; out=base/'figures'
    if out.exists(): raise FileExistsError('preserve existing figure directory')
    out.mkdir()
    with gzip.open(base/'results.json.gz','rt') as f: data=json.load(f)
    with gzip.open(base/'posthoc_ablation.json.gz','rt') as f: ablation=json.load(f)
    service=json.loads((ROOT/'service_opportunity/results/service_v1.json').read_text())
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(8.8,4.9))
    groups=[(20,False,False),(20,True,False),(80,False,False),(80,True,False),(80,True,True)]
    for j,key in enumerate(groups):
        rows=[r for r in service['probes'] if (r['rtt_ms'],r['background'],r['negative_control'])==key]
        x=j+np.linspace(-.12,.12,len(rows))
        ax.scatter(x,[r['joint_completion_seconds'] for r in rows],s=42,color='#a44b22' if key[-1] else '#167b83',
                   label='Receiver-confirmed joint transfer' if j==0 else None,zorder=3)
        ax.scatter(x,[r['subprocess_wall_seconds'] for r in rows],s=42,marker='x',color='#454b56',
                   label='Including client-process startup' if j==0 else None,zorder=3)
    ax.axhline(9.5,color='#167b83',ls='--',lw=1,label='9.5 s transfer deadline')
    ax.axhline(10,color='#555',ls=':',lw=1,label='10 s whole-slot deadline')
    ax.set_xticks(range(5),['20 ms\nidle','20 ms\ncompeting','80 ms\nidle','80 ms\ncompeting','80 ms competing\n1 Mbit/s negative'])
    ax.set_ylabel('Completion time (s)'); ax.set_ylim(7.6,13.6); ax.grid(axis='y',alpha=.18)
    ax.set_title('Controlled reservation: two concurrent 750 kB TCP payloads',pad=13)
    ax.legend(loc='upper left',fontsize=8,frameon=False)
    fig.text(.5,.025,'First four groups: 1.5 Mbit/s reserved class. Three repetitions per group; not field capacity.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.065,1,1))
    for suffix in ('png','svg'): fig.savefig(out/f'service_completion.{suffix}',dpi=180)
    plt.close(fig)
    policies=('rolling_nash','rolling_maxmin','greedy_recovery','cost_greedy','persistence_mpc','unconditional_mpc','knn_mpc','offline')
    labels=('Rolling Nash','Rolling max-min','Greedy recovery','Cost-matched greedy*','Persistence + lookahead','Unconditional mean*','Prefix KNN + lookahead','Future-known oracle')
    cells={r['policy']:r for r in data['summary']['all']+ablation['summary']['all'] if F(r['reserve_fraction'])==1}
    colors=['#788a9b']*6+['#167b83','#a8adb3']
    fig,axes=plt.subplots(1,2,figsize=(11,5.3),sharey=True,gridspec_kw={'width_ratios':[1.1,1]})
    y=np.arange(len(policies))
    for ax,field in zip(axes,('mean_unpaid_fraction','half_repaid')):
        values=[float(F(cells[p][field])) for p in policies]
        ax.barh(y,values,color=colors,height=.62)
        for i,v in enumerate(values): ax.text(v+(.004 if field.startswith('mean') else 1),i,f'{v:.3f}' if field.startswith('mean') else str(int(v)),va='center',fontsize=9)
        ax.grid(axis='x',alpha=.18); ax.set_axisbelow(True)
    axes[0].set_yticks(y,labels); axes[0].invert_yaxis()
    axes[0].set_xlim(0,.53); axes[1].set_xlim(0,115)
    axes[0].set_xlabel('Mean unpaid loss fraction (lower is better)')
    axes[1].set_xlabel('Half-repayment episodes out of 168')
    fig.suptitle('Exposed development: fixed 1.5 MB/slot service, reserve = baseline episode bytes',fontsize=12)
    fig.text(.5,.025,'* Post-hoc controls; unchanged candidate. Exact current qualities; six exposed scenes; no independent-test claim.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.07,1,.94))
    for suffix in ('png','svg'): fig.savefig(out/f'primary_comparison.{suffix}',dpi=180)
    plt.close(fig)
    m={'script_sha256':sha(Path(__file__)),'primary_result_sha256':sha(base/'results.json.gz'),
       'posthoc_result_sha256':sha(base/'posthoc_ablation.json.gz'),
       'service_sha256':sha(ROOT/'service_opportunity/results/service_v1.json'),
       'figure_sha256':{f.name:sha(f) for f in out.iterdir()}}
    (out/'metadata.json').write_text(json.dumps(m,indent=2)+'\n')


if __name__=='__main__': main()
