from fractions import Fraction as F
from itertools import product
from copy import deepcopy
import pytest
from causal_compensation.core import plan,verify_plan,selected_gain,critical_scenarios,take


def test_pathwise_cap_removes_risky_mixture_not_just_its_mean():
    bounded=plan(2000,1000,((0,2000),),F(1,2))
    assert bounded['feasible'] and verify_plan(bounded)
    assert bounded['certificate']['upper']==F(1,2)
    assert all(not w or selected_gain(i,(1000,0),2000)==1000 for i,w in enumerate(bounded['weights']))
    loose=plan(2000,1000,((0,2000),),F(1))
    assert loose['certificate']['upper']==F(1,4) and verify_plan(loose)


def test_infeasible_cap_is_not_relaxed_or_labeled_satisfied():
    r=plan(2000,1000,((0,2000),),F(1,4))
    assert not r['feasible'] and r['alpha']==F(1,4) and r['certificate']['gap'] is None
    assert all(not w or r['worst_loss'][i]>r['alpha'] for i,w in enumerate(r['weights']))
    assert verify_plan(r)


def test_absolute_cap_is_on_each_support_policy_not_expected_loss():
    r=plan(2000,1000,((0,2000),),F(3,4))
    assert all(not w or r['worst_loss'][i]<=F(3,4) for i,w in enumerate(r['weights']))
    assert sum(w for i,w in enumerate(r['weights']) if take(i,0,2,1000,2000))==1


def test_critical_grid_bounds_match_full_small_integer_envelopes():
    # Exhaust every integer sequence, not just the solver's critical vertices.
    for debt,current,lo,hi in product((3,5,7),(0,2,4),(0,1),(4,7)):
        full=tuple((min(debt,current),)+s for s in product(range(lo,min(debt,hi)+1),repeat=2))
        critical=critical_scenarios(debt,current,((lo,hi),)*2)
        weights=(F(1,7),F(2,7),F(0),F(1,7),F(1,7),F(2,7))
        for i in range(6):
            assert max(debt-selected_gain(i,s,debt) for s in full)==max(debt-selected_gain(i,s,debt) for s in critical)
        regret=lambda s: sum(w*(max(s)-selected_gain(i,s,debt)) for i,w in enumerate(weights))
        assert max(map(regret,full))==max(map(regret,critical))


def test_certificates_and_constraints_across_small_games():
    for debt,current,alpha in product((3,7),(0,2,5),(F(1,4),F(1,2),F(1))):
        r=plan(debt,current,((0,4),(2,7)),alpha)
        assert verify_plan(r)


def test_invalid_certificate_detected():
    r=plan(2000,1000,((0,2000),),F(1,2))
    broken=deepcopy(r); broken['certificate']['upper']=F(0)
    with pytest.raises(AssertionError): verify_plan(broken)
    broken=deepcopy(r); broken['weights']=(F(0),)*5+(F(1),)
    with pytest.raises(AssertionError): verify_plan(broken)


def test_no_headroom_is_explicit_failure_for_nontrivial_cap():
    r=plan(10,0,((0,0),)*3,F(1,2))
    assert not r['feasible'] and r['worst_loss']==(F(1),)*6
    assert r['certificate']['upper']==0  # zero regret still leaves every unit unpaid


def test_policy_decisions_do_not_need_future_sequence():
    assert tuple(take(i,0,4,500,1000) for i in range(6))==(True,True,True,False,False,False)
    for i in range(6):
        assert not take(i,3,4,0,1000)
        assert take(i,3,4,1,1000)


def test_bad_inputs():
    with pytest.raises(ValueError): plan(0,0,((0,1),))
    with pytest.raises(ValueError): plan(3,0,((4,2),))
    with pytest.raises(ValueError): plan(3,0,((0,3),),F(2))
