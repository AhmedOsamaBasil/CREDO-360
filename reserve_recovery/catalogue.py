"""Exact exposed-table calculation; not measured spare capacity or a new trial."""
from fractions import Fraction as F
from itertools import product
from recovery_objective.core import Action,Step,Contract
from feasibility_frontier.data import load
from feasibility_frontier.core import witness
from reserve_recovery.core import Slot,online

PEAKS=(F(1),F(2),F(3),F(4))
FRACTIONS=(F(0),F(1,4),F(1,2),F(1),F(2))
BASELINES=('rolling_nash','rolling_maxmin','greedy_recovery')


def cost_frontier(periods,debt,peak):
    """Integer gain -> minimum additional bytes; all donor losses forbidden."""
    states={0:(0,())}
    for options in periods:
        updated={}
        for gain,(cost,path) in states.items():
            for a in options:
                if a.harm or a.multiplier>peak: continue
                key=min(debt,gain+a.gain)
                candidate=(cost+max(a.bytes-a.reference_bytes,0),path+(a.rungs,))
                if key not in updated or candidate<updated[key]: updated[key]=candidate
        # Greater gain at no greater cost dominates. Exact tie uses rung tuples.
        states={}; cheapest=None
        for gain in sorted(updated,reverse=True):
            cost,path=updated[gain]
            if cheapest is None or cost<cheapest:
                states[gain]=(cost,path); cheapest=cost
    return states


def decode(periods,rungs):
    return tuple(next(a for a in options if a.rungs==r) for options,r in zip(periods,rungs))


def minimum_half(states,debt):
    target=(debt+1)//2
    options=[(cost,-gain,path) for gain,(cost,path) in states.items() if gain>=target]
    return min(options) if options else None


def best_under(states,reserve):
    options=[(-gain,cost,path) for gain,(cost,path) in states.items() if cost<=reserve]
    if not options: raise ValueError('no baseline feasible')
    negative_gain,cost,path=min(options)
    return -negative_gain,cost,path


def summarize_path(periods,rungs,debt):
    path=decode(periods,rungs); w=witness(path,debt)
    extra=sum(max(a.bytes-a.reference_bytes,0) for a in path)
    means=tuple(F(sum(a.quality[u] for a in path),1000*len(path)) for u in (0,1))
    assert all(a.harm==0 and a.gain>=0 for a in path)
    return {**w,'extra_bytes':extra,'post_means':means,'worst_post_quality':min(means),
            'mean_post_quality':sum(means)/2,'peak_payload_mbps':max(F(a.bytes*8,10_000_000) for a in path),
            'peak_extra_mbps':max(F(max(a.bytes-a.reference_bytes,0)*8,10_000_000) for a in path),
            'average_extra_mbps':F(extra*8,40_000_000)}


def slots(periods,peak):
    result=[]
    for options in periods:
        ref=options[0].reference; base=options[0].reference_bytes
        actions=tuple(Action(f'r{a.rungs[0]}d{a.rungs[1]}',tuple(F(q,1000) for q in a.quality),a.bytes)
                      for a in options)
        result.append(Slot(Step(tuple(F(q,1000) for q in ref),actions,peak*base),base))
    return tuple(result)


def grouped(rows):
    groups={'all':rows}
    for key in ('cohort','scene'):
        for name in sorted({r[key] for r in rows}): groups[name]=[r for r in rows if r[key]==name]
    summaries={}
    for name,group in groups.items():
        cells=[]
        for peak,rho,policy in product(PEAKS,FRACTIONS,BASELINES+('offline',)):
            selected=[v for r in group for v in r['outcomes'] if (v['peak'],v['reserve_fraction'],v['policy'])==(peak,rho,policy)]
            assert len(selected)==len(group)
            cells.append({'peak':peak,'reserve_fraction':rho,'policy':policy,'episodes':len(selected),
                'half_repaid':sum(r['unpaid_fraction']<=F(1,2) for r in selected),
                'mean_unpaid_fraction':sum(r['unpaid_fraction'] for r in selected)/len(selected),
                'mean_extra_bytes':F(sum(r['extra_bytes'] for r in selected),len(selected)),
                'mean_worst_quality':sum(r['worst_post_quality'] for r in selected)/len(selected),
                'mean_quality':sum(r['mean_post_quality'] for r in selected)/len(selected)})
        demands=[]
        for peak in PEAKS:
            witnesses=[r['minimum_reserve'][str(peak)] for r in group if r['minimum_reserve'][str(peak)] is not None]
            def stats(field):
                values=sorted(w[field] for w in witnesses)
                return None if not values else {'minimum':values[0],'median':values[(len(values)-1)//2],'maximum':values[-1]}
            demands.append({'peak':peak,'feasible':len(witnesses),'infeasible':len(group)-len(witnesses),
                **{field:stats(field) for field in ('extra_bytes','reserve_fraction','peak_payload_mbps','peak_extra_mbps','average_extra_mbps')}})
        summaries[name]={'episodes':len(group),'cells':cells,'minimum_reserve_demands':demands}
    return summaries


def analysis(progress=False):
    rows=[]; witnesses=0; comparisons=0
    for number,(e,periods) in enumerate(load(),1):
        total_base=sum(p[0].reference_bytes for p in periods)
        contract=Contract((F(e.loss,1000),0),(0,0),(0,0))
        history=tuple(tuple(F(q,1000) for q in row) for row in e.history)
        outcomes=[]; minima={}
        for peak in PEAKS:
            frontier=cost_frontier(periods,e.loss,peak)
            required=minimum_half(frontier,e.loss)
            if required is None: minima[str(peak)]=None
            else:
                cost,negative_gain,path=required; w=summarize_path(periods,path,e.loss)
                assert w['extra_bytes']==cost and w['delivered_units']==-negative_gain and w['peak_multiplier']<=peak
                minima[str(peak)]={**w,'reserve_fraction':F(cost,total_base)}; witnesses+=1
            schedule=slots(periods,peak)
            for rho in FRACTIONS:
                reserve=rho*total_base
                gain,cost,path=best_under(frontier,reserve); w=summarize_path(periods,path,e.loss)
                assert gain==w['delivered_units'] and cost==w['extra_bytes'] and cost<=reserve
                common={'peak':peak,'reserve_fraction':rho,'reserve_bytes':reserve}
                outcomes.append({**common,'policy':'offline','unpaid_fraction':F(e.loss-gain,e.loss),**w})
                for name in BASELINES:
                    r=online(name,schedule,contract,reserve,history)
                    rungs=tuple((int(x['action'][1]),int(x['action'][3])) for x in r['trace'])
                    w2=summarize_path(periods,rungs,e.loss)
                    assert r['terminal_max_fraction']==w2['remaining_fraction']>=w['remaining_fraction']
                    assert r['extra_bytes']==w2['extra_bytes']<=reserve
                    assert sum(r['donor_spent'])==0
                    outcomes.append({**common,'policy':name,'unpaid_fraction':r['terminal_max_fraction'],**w2})
                    comparisons+=1
        rows.append({'key':e.key,'cohort':e.cohort,'scene':e.scene,'recipient':e.recipient,'donor':e.donor,
                     'original_loss_units':e.loss,'baseline_bytes':total_base,'minimum_reserve':minima,'outcomes':outcomes})
        if progress and number%28==0: print(f'Exposed reserve audit {number}/168',flush=True)
    return {'episodes':rows,'summary':grouped(rows),'minimum_reserve_witnesses':witnesses,
            'online_vs_oracle_checks':comparisons,'network_supply_validated':False}
