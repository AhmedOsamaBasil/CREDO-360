"""Replay current-information policies, exposing future gains only to evaluation."""
from fractions import Fraction as F
from math import prod
from causal_compensation.core import take

CONTROLS = ('rolling_nash','rolling_maxmin','stateless_nash','greedy_recovery','baseline')
METRICS = ('unpaid_fraction','unpaid_utility','regret','cap_violation','donor_loss',
           'worst_post_quality','mean_post_quality','bytes','model_breach','transfer_count')


def replay(episode, policy, alpha=F(1,2), bounds=None):
    debt, spent, history, trace = episode.loss, False, list(episode.history), []
    breach, donor_loss, bytecount, qualities = False, 0, 0, []
    offers = episode.offers[2:]
    for t,o in enumerate(offers):
        if bounds is not None:
            lo,hi = bounds[t]
            if not min(episode.loss,lo) <= min(episode.loss,o.gain) <= min(episode.loss,hi): breach = True
        boost = False
        if episode.loss and not spent and o.gain > 0:
            if isinstance(policy,int):
                boost = True if breach else take(policy,t,len(offers),o.gain,episode.loss)
            elif policy == 'greedy_recovery': boost = True
            elif policy == 'baseline': pass
            elif policy in CONTROLS:
                past = tuple(sum(row[i] for row in history[-23:]) for i in range(2))
                def score(q,cost):
                    totals = tuple(p+x for p,x in zip(past,q))
                    primary = tuple(sorted(totals)) if policy == 'rolling_maxmin' else (prod(totals) if policy == 'rolling_nash' else prod(q),)
                    return primary+(prod(q),-cost)
                boost = score(o.transfer,o.transfer_bytes) > score(o.reference,o.baseline_bytes)
            else: raise ValueError('unknown control')
        q = o.transfer if boost else o.reference
        cost = o.transfer_bytes if boost else o.baseline_bytes
        credit = min(debt,o.gain) if boost else 0
        debt -= credit
        if boost: spent = True; donor_loss += o.harm
        assert cost <= o.baseline_bytes and q[0] >= o.reference[0] and donor_loss <= 500
        bytecount += cost; history.append(q); qualities.append(q)
        trace.append({'period':t,'gain':o.gain,'transfer':bool(boost),'quality':q,'bytes':cost,
                      'credit':credit,'outstanding':debt,'donor_loss':donor_loss,'model_breach':breach})
    loss = F(debt,episode.loss) if episode.loss else F(0)
    oracle = F(max(0,episode.loss-max(o.gain for o in offers)),episode.loss) if episode.loss else F(0)
    means = tuple(F(sum(q[i] for q in qualities),len(qualities)*1000) for i in range(2))
    assert debt+sum(r['credit'] for r in trace) == episode.loss
    assert sum(r['transfer'] for r in trace) <= 1
    return {'unpaid_fraction':loss,'unpaid_utility':F(debt,1000),'regret':loss-oracle,
            'cap_violation':F(int(loss>alpha)),'donor_loss':F(donor_loss,1000),
            'worst_post_quality':min(means),'mean_post_quality':sum(means)/2,'bytes':F(bytecount),
            'model_breach':F(int(breach)),'transfer_count':F(int(spent)),
            'oracle_unpaid_fraction':oracle,'trace':trace}


def mixture(episode, planned, alpha):
    bounds = ((episode.offers[2].gain,episode.offers[2].gain),)+tuple(planned['bounds'])
    paths = tuple({'policy':i,'weight':w,'outcome':replay(episode,i,alpha,bounds)}
                  for i,w in enumerate(planned['weights']) if w)
    expected = {key:sum((p['weight']*p['outcome'][key] for p in paths),F(0)) for key in METRICS}
    return {'expected':expected,'paths':paths}
