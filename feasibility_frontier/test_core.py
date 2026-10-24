from fractions import Fraction as F
from itertools import product
from random import Random
import pytest
from feasibility_frontier.core import (Action,actions,frontier,required,feasible,dp_feasible,
                                      verify_witness,EPSILONS,TRANSFERS,prune)


def option(g,h,c=F(1),r=1):
    return Action(g,h,F(c),int(F(c)*100),(r,0),(3000+g,3000-h),(3000,3000),100)


def direct(periods,debt,m,epsilon,budget,resource):
    return any(sum(a.gain for a in path)*2>=debt and sum(a.count for a in path)<=m
               and max(a.harm for a in path)<=epsilon and sum(a.harm for a in path)<=budget
               and max(a.multiplier for a in path)<=resource for path in product(*periods))


def test_two_small_repayments_require_two_actions():
    periods=((option(0,0,r=0),option(300,125)),)*2
    r=frontier(periods,1000)
    assert required(r['frontiers'],1,125,250) is None
    assert feasible(r['frontiers'],2,125,250,F(1))
    assert not feasible(r['frontiers'],2,125,249,F(1))


def test_resource_for_donor_loss_tradeoff_is_not_averaged():
    periods=((option(0,0,r=0),option(500,500,F(1),1),option(500,0,F(3,2),2)),)
    r=frontier(periods,1000)
    assert required(r['frontiers'],1,500,500)['peak_multiplier']==1
    assert required(r['frontiers'],1,500,0)['peak_multiplier']==F(3,2)
    assert not feasible(r['frontiers'],1,500,0,F(149,100))


def test_per_step_cap_is_separate_from_total_cap():
    p=((option(0,0,r=0),option(600,500)),)
    f=frontier(p,1000)['frontiers']
    assert required(f,1,250,4000) is None
    assert required(f,1,500,500) is not None


def test_complete_small_cases_match_direct_and_independent_dp():
    for debt in (500,999,1500):
        periods=((option(0,0,r=0),option(250,125,F(1),1),option(700,0,F(3,2),2)),
                 (option(0,0,r=0),option(400,250,F(1),1),option(800,500,F(5,4),2)))
        reduced=frontier(periods,debt); full=frontier(periods,debt,pruning=False)
        for m,e,b,r in product((1,2,4),(0,125,250,500),(0,125,250,500,1000),(F(1),F(5,4),F(3,2))):
            expected=direct(periods,debt,m,e,b,r)
            assert feasible(reduced['frontiers'],m,e,b,r)==expected
            assert feasible(full['frontiers'],m,e,b,r)==expected
            assert dp_feasible(periods,debt,m,e,b,r)==expected


def test_every_saved_witness_replays_original_actions():
    p=((option(0,0,r=0),option(400,125,F(1),1),option(600,0,F(3,2),2)),)*4
    result=frontier(p,2000)
    for key,points in result['frontiers'].items():
        m,e=map(int,key.split(':'))
        for point in points: assert verify_witness(point,p,2000,m,e)


def test_infeasible_case_keeps_empty_frontiers():
    p=((option(0,0,r=0),option(10,0)),)*4
    assert all(not x for x in frontier(p,1000)['frontiers'].values())


def test_gain_cap_does_not_change_feasibility_and_ties_are_stable():
    p=(option(0,0,r=0),option(1000,125,r=1),option(2000,125,r=2))
    assert [a.rungs for a in prune(p,500)]==[(0,0),(1,0)]
    assert frontier((p,),1000)['frontiers']==frontier((tuple(reversed(p)),),1000)['frontiers']


def test_resource_ratios_are_exact_and_peak_not_total():
    p=((option(500,0,F(3,2)),),(option(0,0,F(1),0),))
    w=required(frontier(p,1000)['frontiers'],1,0,0)
    assert w['peak_multiplier']==F(3,2) and w['total_byte_ratio']==F(5,4)
    assert not feasible(frontier(p,1000)['frontiers'],1,0,0,F(5,4))


def test_full_action_space_and_recipient_floor():
    q=(1000,2000,3000,3500,4000,4500); c=(10,20,30,40,50,60)
    p=actions(q,q,c)
    assert len(p)==24 and all(a.quality[0]>=3000 for a in p)
    assert any(a.rungs==(5,2) and a.harm==0 for a in p)


def test_donor_surplus_never_refunds_harm():
    q=(1000,2000,3000,3500,4000,4500); c=(10,20,30,40,50,60)
    p=actions(q,q,c)
    assert next(a for a in p if a.rungs==(3,5)).harm==0


def test_odd_loss_target_is_rounded_up_not_down():
    p=((option(0,0,r=0),option(500,0)),)
    assert required(frontier(p,1001)['frontiers'],1,0,0) is None


def test_bad_inputs_and_tampered_witness():
    with pytest.raises(ValueError): frontier((),1000)
    with pytest.raises(ValueError): frontier(((option(0,0),),),0)
    p=((option(0,0,r=0),option(500,0)),)
    point=required(frontier(p,1000)['frontiers'],1,0,0).copy()
    point['donor_total_units']=99
    with pytest.raises(AssertionError): verify_witness(point,p,1000,1,0)


def test_varied_three_period_cases_at_exact_resource_boundaries():
    rng=Random(71)
    for _ in range(8):
        p=tuple(tuple([option(0,0,r=0)]+[
            option(rng.choice((0,125,400,800)),rng.choice((0,125,500)),
                   rng.choice((F(1),F(5,4),F(3,2))),r) for r in range(1,4)]) for t in range(3))
        debt=rng.choice((799,1000,1601))
        reduced=frontier(p,debt)['frontiers']; full=frontier(p,debt,pruning=False)['frontiers']
        for m,e,b,r in product((1,2,4),(0,125,500),(0,125,500,1000),(F(1),F(5,4),F(3,2))):
            expected=direct(p,debt,m,e,b,r)
            assert feasible(reduced,m,e,b,r)==expected
            assert feasible(full,m,e,b,r)==expected
            assert dp_feasible(p,debt,m,e,b,r)==expected
