"""Static figures from complete saved evidence; no scientific recomputation.

All axes and cell selections are fixed independently of timing outcomes.
The figure data are stored separately from PDF/PNG rendering for exact replay.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path

from wu_feasibility.spec import canonical, digest, file_hash, text_hash
from .assemble import POLICIES


def figure_data(evidence):
    if evidence['schema'] != 'recovery-contract-evidence-v1':
        raise ValueError('Unexpected evidence schema')
    clips=sorted((r for r in evidence['feasibility']['clips'] if r['disposition']=='evaluated'),
                 key=lambda r:r['clip'])
    if len(clips)!=10:raise ValueError('All ten eligible clips required')
    cells=[r for r in evidence['timing']['cells'] if r['control']=='none']
    lookup={(r['clip'],r['policy'],r['unit_seconds'],r['buffered']):r for r in cells}
    columns=[(p,u,b) for p in POLICIES for u in (10,2) for b in (False,True)]
    if len(lookup)!=120:raise ValueError('All 120 main timing cells required')
    timing=[]
    for clip in clips:
        row=[]
        for policy,unit,buffered in columns:
            c=lookup[(clip['clip'],policy,unit,buffered)]
            complete=c['valid']==3 and c['parent_fraction_minus_ideal']['n']==3
            value=c['parent_fraction_minus_ideal']['mean'] if complete else None
            if value is not None and not -1<=Fraction(value)<=1:
                raise ValueError('Capped credited-fraction difference outside [-1,1]')
            row.append({'case_id':c['case_id'],'delta':value,
                'valid':c['valid'],'scheduled':c['scheduled'],
                'cap_failures_among_valid':c['resource_cap_failures'],
                'recipient_finish_seconds':c['recipient_finish_seconds']})
        timing.append(row)
    return {'schema':'recovery-contract-figure-data-v1','evidence_sha256':digest(evidence),
        'clips':clips,'columns':[{'policy':p,'unit_seconds':u,'buffered':b} for p,u,b in columns],
        'timing_cells':timing,'repetitions':3,'heatmap_range':[-1,1],
        'deadline_seconds':40,'missing_cell_policy':'show missing; never impute or drop',
        'controls':evidence['timing']['controls']}


def render(data, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':9,'axes.titlesize':9,'axes.labelsize':9,
        'xtick.labelsize':9,'ytick.labelsize':9,
        'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':600})
    saved=[]
    def save(fig,name):
        for ext in ('pdf','png'):
            path=output/f'{name}.{ext}'
            options={'metadata':{'CreationDate':None,'ModDate':None}} if ext=='pdf' else {}
            fig.savefig(path,bbox_inches='tight',**options);saved.append(path)
        plt.close(fig)
    clips=data['clips']; y=np.arange(len(clips)); labels=[r['clip'] for r in clips]
    fig,axes=plt.subplots(1,3,figsize=(7.16,3.7),sharey=True,
        gridspec_kw={'width_ratios':[2.1,1,1]})
    convex=np.array([r['convex_impossible'] for r in clips]);extra=np.array([r['additional_rejections'] for r in clips])
    impossible=convex+extra;abstain=np.array([r['abstain'] for r in clips])
    axes[0].barh(y,convex,color='#586b7f',label='Convex rejection')
    axes[0].barh(y,extra,left=convex,color='#d18b28',hatch='///',
                 edgecolor='#555555',linewidth=.3,label='Additional geometric rejection')
    axes[0].barh(y,abstain,left=impossible,color='#dce1e6',label='Abstain')
    admitted=np.array([r['admit'] for r in clips])
    if admitted.any():axes[0].barh(y,admitted,left=impossible+abstain,color='#357a55',label='Admit')
    axes[0].set_yticks(y,labels);axes[0].invert_yaxis()
    axes[0].set_title('(a) Contract decision');axes[0].set_xlabel('Directed episodes')
    axes[1].barh(y,extra,color='#d18b28',hatch='///',edgecolor='#555555',linewidth=.3)
    axes[1].set_title('(b) Extra rejections')
    axes[1].set_xlabel('Directed episodes')
    gaps=[r['opportunity_promise_gaps'] for r in clips]
    axes[2].barh(y,gaps,color='#7b538e');axes[2].set_title('(c) Opportunity gap')
    axes[2].set_xlabel('Directed episodes')
    for ax in axes:
        ax.set_xlim(0,50);ax.axhline(4.5,color='black',lw=.6,ls=':')
        ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True);ax.grid(axis='x',alpha=.2)
    handles,names=axes[0].get_legend_handles_labels()
    fig.legend(handles,names,loc='lower center',bbox_to_anchor=(.5,-.08),ncol=2,frameon=False,fontsize=9)
    fig.tight_layout(w_pad=1.2);save(fig,'wu_feasibility')

    values=np.array([[float(Fraction(c['delta'])) if c['delta'] is not None else np.nan for c in row]
                     for row in data['timing_cells']])
    fig,ax=plt.subplots(figsize=(7.16,3.8));cmap=plt.get_cmap('RdBu').copy();cmap.set_bad('#999999')
    im=ax.imshow(np.ma.masked_invalid(values),vmin=-1,vmax=1,cmap=cmap,aspect='auto')
    xticks=[f'{c["unit_seconds"]} s\n'+('B' if c['buffered'] else 'C') for c in data['columns']]
    ax.set_xticks(np.arange(12),xticks);ax.set_yticks(y,labels)
    for i,name in enumerate(('Cost-greedy','Rolling Nash','Max-min')):
        ax.text((i*4+1.5)/12+.5/12,1.02,name,transform=ax.transAxes,ha='center',fontsize=9)
    for j in (3.5,7.5):ax.axvline(j,color='black',lw=.7)
    ax.axhline(4.5,color='black',lw=.7)
    for i,row in enumerate(data['timing_cells']):
        for j,cell in enumerate(row):
            if cell['delta'] is None:
                ax.text(j,i,'NA',ha='center',va='center',fontsize=9)
            elif cell['cap_failures_among_valid']:
                ax.plot(j,i,marker='x',color='black',ms=4,mew=.8)
    cb=fig.colorbar(im,ax=ax,fraction=.035,pad=.025);cb.set_label('Measured minus ideal credited fraction')
    ax.set_xlabel('C: cold; B: buffered; ×: parent-cap failure; grey: incomplete cell',labelpad=6)
    fig.tight_layout();save(fig,'wu_timing_delta')

    # The entire paired completion distribution is shown, not a best/worst trace.
    fig,axes=plt.subplots(1,2,figsize=(7.16,3.7),sharey=True)
    for condition,ax in zip(('free_exploration','content_focused_memory_test'),axes):
        for j,c in enumerate(data['columns']):
            selected=[data['timing_cells'][i][j] for i,r in enumerate(clips) if r['condition']==condition]
            for k,cell in enumerate(selected):
                if cell['valid']!=3:continue
                stats=cell['recipient_finish_seconds'];mean=float(Fraction(stats['mean']))
                low=float(Fraction(stats['min']));high=float(Fraction(stats['max']))
                x=j+(k-2)*.11
                ax.errorbar(x,mean,yerr=[[mean-low],[high-mean]],fmt=('o','s','^')[j//4],ms=2.5,
                    lw=.6,color=('#2e668b' if j//4==0 else '#d18b28' if j//4==1 else '#7b538e'),alpha=.85)
        ax.axhline(40,color='black',ls='--',lw=.8)
        ax.set_xticks(range(12),[f'{c["unit_seconds"]}'+('B' if c['buffered'] else 'C') for c in data['columns']],rotation=45)
        ax.set_title('Free exploration' if condition=='free_exploration' else 'Content-focused memory test')
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2)
        ax.set_ylim(bottom=0)
        ax.set_xlabel('G: first four; N: next four; M: last four')
    axes[0].set_ylabel('Complete recipient recovery playback (s)')
    fig.tight_layout();save(fig,'wu_completion')
    return saved


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--verify',action='store_true')
    a=p.parse_args();evidence=json.loads((a.evidence/'evidence.json').read_text());data=figure_data(evidence)
    if a.verify:
        meta=json.loads((a.output/'metadata.json').read_text())
        if meta['source_sha256']!=text_hash(Path(__file__)) or meta['data_sha256']!=digest(data):
            raise ValueError('Figure source/data changed')
        if json.loads((a.output/'data.json').read_text())!=data:raise ValueError('Figure data changed')
        for name,sha in meta['figures'].items():
            if file_hash(a.output/name)!=sha:raise ValueError('Figure bytes changed')
    else:
        a.output.mkdir(parents=True,exist_ok=False)
        (a.output/'data.json').write_bytes(canonical(data));files=render(data,a.output)
        meta={'source_sha256':text_hash(Path(__file__)),'data_sha256':digest(data),
              'figures':{f.name:file_hash(f) for f in files},'automatically_selected_extreme_case':False}
        (a.output/'metadata.json').write_bytes(canonical(meta))
    print(json.dumps(meta))


if __name__=='__main__':main()
