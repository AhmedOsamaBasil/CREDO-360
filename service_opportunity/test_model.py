from dataclasses import replace
from fractions import Fraction as F
from itertools import product
import pytest
from feasibility_frontier.core import actions
from service_opportunity.model import (CAPACITY,Record,forecast,optimize,brute,valid,
    predicted_periods,records,pool,sizes)
from service_opportunity.run import simulate
from feasibility_frontier.data import load


def period(gain=400,cost=200):
    return actions((1000,2000,3000,3000+gain,3000+gain,3000+gain),
                   (1000,2000,3000,3000,3000,3000),(20,50,100,cost,cost,cost))


def test_dp_brute_grid():
    for a,b,d,r in product((0,200,700),(0,300,800),(300,1000),(0,100,200,400)):
        ps=(period(a),period(b))
        assert optimize(ps,d,r)[:2]==brute(ps,d,r)[:2]


def test_wait_for_better_opportunity():
    g,c,p=optimize((period(400),period(700)),1000,100)
    assert (g,c)==(700,100) and p[0][0]==2 and p[1][0]>=3


def test_cap_independent_of_reserve():
    assert optimize((period(700),),1000,10000,200)[0]==0


def test_no_refund():
    ps=(period(0),period(700))
    assert optimize(ps,1000,99)[0]==0


def test_baseline_infeasible():
    with pytest.raises(ValueError): valid(period(),10000,199)


def test_negative_state_rejected():
    with pytest.raises(ValueError): optimize((period(),),-1,100)
    with pytest.raises(ValueError): optimize((period(),),100,-1)


def test_zero_debt():
    assert optimize((period(),period()),0,1000)[:2]==(0,0)


def test_all_action_floors():
    for a in valid(period(),1000):
        assert a.harm==0 and all(q>=b for q,b in zip(a.quality,a.reference))


def test_sender_sizes_roundtrip():
    assert sizes(period())==(20,50,100,200,200,200)


def test_forecast_rounding_and_prefix_only():
    q=(((3000,)*6,(3000,)*6),)*4
    training=tuple(Record(str(i),'train',1,2,1000,tuple(
        tuple(tuple(v+i%2 for v in u) for u in t) for t in q)) for i in range(8))
    future,neighbors=forecast(q[:1],1000,training)
    assert len(future)==3 and future[0][0][0]==3001 and len(neighbors)==8
    assert forecast(q,1000,training)[0]==()


def test_invalid_prefix():
    with pytest.raises(ValueError): forecast((),100,())


@pytest.fixture(scope='module')
def exposed(): return records(),load()


def test_training_exclusions(exposed):
    rs,_=exposed
    for target in rs:
        training=pool(rs,target)
        assert len(training)==130
        assert all(r.scene!=target.scene and not {r.recipient,r.donor}&{target.recipient,target.donor} for r in training)


def test_future_mutation_does_not_change_first_action(exposed):
    rs,data=exposed; e,ps=data[0]; target=next(r for r in rs if r.key==e.key)
    altered=replace(target,qualities=(target.qualities[0],)+((((1000,)*6,(5000,)*6),)*3))
    a=simulate(e,ps,target,pool(rs,target),F(1),'knn_mpc')
    b=simulate(e,ps,altered,pool(rs,target),F(1),'knn_mpc')
    for field in ('rungs','neighbors','predicted_qualities','planned_rungs'):
        assert a['decisions'][0][field]==b['decisions'][0][field]


def test_exposed_ledger_conservation(exposed):
    rs,data=exposed; e,ps=data[0]; r=next(x for x in rs if x.key==e.key)
    for p in ('knn_mpc','persistence_mpc','greedy_recovery','rolling_nash','rolling_maxmin','offline'):
        out=simulate(e,ps,r,pool(rs,r),F(1),p)
        assert out['extra_bytes']<=out['reserve_bytes'] and out['donor_total_units']==0
        assert sum(x['credit_units'] for x in out['decisions'])+out['decisions'][-1]['debt_after']==e.loss
        assert all(x['bytes']<=CAPACITY for x in out['trace'])


def test_exact_future_matches_oracle_first_objective(exposed):
    rs,data=exposed; e,ps=data[0]
    r=next(x for x in rs if x.key==e.key)
    predicted=predicted_periods(r.qualities,tuple(sizes(p) for p in ps))
    assert optimize(predicted,e.loss,2_000_000)==optimize(ps,e.loss,2_000_000)


def test_order_invariance():
    ps=(period(400),period(700))
    assert optimize(ps,1000,100)==optimize(tuple(tuple(reversed(p)) for p in ps),1000,100)
