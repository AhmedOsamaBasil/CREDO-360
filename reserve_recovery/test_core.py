from dataclasses import replace
from fractions import Fraction as F
from itertools import product
import pytest
from recovery_objective.core import Action,Step,Contract
from reserve_recovery.core import Slot,extra,result,online,plan,execute,observation
from reserve_recovery.cases import offer,bounded,problems
from reserve_recovery.catalogue import cost_frontier,minimum_half,best_under
from feasibility_frontier.test_core import option


def test_bounded_future_has_pathwise_advantage_over_rolling_rules():
    p=bounded(); planned=plan(p.scenarios,p.contract,p.reserve)
    assert planned['admitted'] and planned['worst_loss']==F(2,5)
    for name in ('rolling_nash','rolling_maxmin','greedy_recovery'):
        assert max(online(name,s,p.contract,p.reserve,p.history)['terminal_max_fraction'] for s in p.scenarios)==F(3,5)


def test_all_declared_cases_have_exact_bellman_and_execution_agreement():
    for p in problems():
        planned=plan(p.scenarios,p.contract,p.reserve)
        rule=planned['policies'][planned['best']]
        for scenario,outcome in zip(p.scenarios,rule['outcomes']):
            actual=execute(rule,scenario,p.contract,p.reserve,p.history)
            assert not actual.pop('model_breach') and actual==outcome


def test_causal_admission_gap_is_not_offline_admission():
    p=problems()[-1]; planned=plan(p.scenarios,p.contract,p.reserve)
    assert all(r['terminal_max_fraction']==F(2,5) for r in planned['oracle'])
    assert planned['worst_loss']==F(7,10) and not planned['admitted']


def test_shared_prefix_actions_never_know_future_labels():
    p=bounded(); planned=plan(p.scenarios,p.contract,p.reserve)
    assert observation(p.scenarios[0][0])==observation(p.scenarios[1][0])
    assert all(rule['paths'][0][0]==rule['paths'][1][0] for rule in planned['policies'])


def test_bounded_formula_grid_is_exact():
    for a,c,b in product((F(1,10),F(1,4),F(2,5)),(F(1,2),F(3,5),F(4,5)),(F(9,10),F(1))):
        p=bounded(a,c,b); r=plan(p.scenarios,p.contract,p.reserve)
        assert r['worst_loss']==1-c and r['admitted']


def test_nonbinding_reserve_removes_timing_gap():
    p=bounded(reserve=2); r=plan(p.scenarios,p.contract,p.reserve)
    assert r['worst_loss']==0
    assert all(online('rolling_nash',s,p.contract,p.reserve,p.history)['all_recovered'] for s in p.scenarios)


def test_model_miss_keeps_budget_but_loses_recovery_guarantee():
    p=bounded(); r=plan(p.scenarios,p.contract,p.reserve)
    actual=(p.scenarios[0][0],offer(0))
    out=execute(r['policies'][r['best']],actual,p.contract,p.reserve,p.history)
    assert out['model_breach'] and out['terminal_max_fraction']==1
    assert out['extra_bytes']==0 and not out['half_repaid']


def test_capacity_cannot_be_replaced_by_reserve_tokens():
    p=problems()[5]; r=plan(p.scenarios,p.contract,p.reserve)
    assert r['worst_loss']==1
    assert r['policies'][r['best']]['outcomes'][0]['extra_bytes']==0


def test_savings_never_refill_the_reserve():
    baseline=Action('baseline',(3,3),1); cheap=Action('cheap',(3,3),F(1,2))
    first=Slot(Step((3,3),(baseline,cheap),2),1); second=offer(F(1,2))
    contract=Contract((1,0),(0,0),(0,0))
    with pytest.raises(ValueError): result((cheap,second.step.actions[1]),(first,second),contract,F(1,2))
    out=result((cheap,baseline),(first,second),contract,F(1,2))
    assert out['remaining_reserve_bytes']==F(1,2)


def test_baseline_infeasibility_is_explicit():
    with pytest.raises(ValueError): Slot(Step((3,3),(Action('base',(3,3),1),),1),2)
    with pytest.raises(ValueError): Slot(Step((3,3),(Action('base',(3,3),1),),1),F(1,2))


def test_reserve_conservation_and_boundary():
    s=(offer(F(2,5)),offer(F(3,5))); p=bounded()
    out=result(tuple(x.step.actions[1] for x in s),s,p.contract,2)
    assert out['extra_bytes']==2 and out['remaining_reserve_bytes']==0 and out['all_recovered']
    with pytest.raises(ValueError): result(tuple(x.step.actions[1] for x in s),s,p.contract,F(1999,1000))


def test_catalogue_dp_matches_unpruned_brute_force():
    p=((option(0,0,r=0),option(300,0,F(3,2),1),option(700,0,F(2),2)),)*3
    for debt,peak in product((500,1001,1800),(F(1),F(3,2),F(2))):
        states=cost_frontier(p,debt,peak)
        paths=[path for path in product(*p) if all(a.multiplier<=peak for a in path)]
        for reserve in (0,50,100,150,300):
            direct=max(min(debt,sum(a.gain for a in path)) for path in paths if sum(max(a.bytes-a.reference_bytes,0) for a in path)<=reserve)
            assert best_under(states,reserve)[0]==direct
        good=[sum(max(a.bytes-a.reference_bytes,0) for a in path) for path in paths if sum(a.gain for a in path)>=(debt+1)//2]
        answer=minimum_half(states,debt)
        assert (None if answer is None else answer[0])==(min(good) if good else None)


def test_donor_harm_is_never_hidden_by_resource_savings():
    p=((option(0,0,r=0),option(1000,1,F(1),1)),)
    assert minimum_half(cost_frontier(p,1000,F(1)),1000) is None


def test_unit_scaling_changes_bytes_not_scientific_decisions():
    p=bounded(); schedules=[]
    for s in p.scenarios:
        schedules.append(tuple(Slot(Step(x.step.reference,
            tuple(Action(a.name,a.quality,1000*a.resources) for a in x.step.actions),
            1000*x.step.resource_cap),1000*x.baseline_bytes) for x in s))
    r=plan(tuple(schedules),p.contract,1000*p.reserve)
    assert r['worst_loss']==plan(p.scenarios,p.contract,p.reserve)['worst_loss']


def test_odd_integer_loss_is_not_rounded_down_for_admission():
    p=((option(0,0,r=0),option(500,0,F(2),1)),)
    assert minimum_half(cost_frontier(p,1001,F(2)),1001) is None
    assert minimum_half(cost_frontier(p,1000,F(2)),1000)[0]==100


def test_gain_cost_dp_is_invariant_to_action_enumeration():
    p=((option(0,0,r=0),option(500,0,F(2),1),option(700,0,F(2),2)),)*2
    assert cost_frontier(p,1000,F(2))==cost_frontier(tuple(tuple(reversed(x)) for x in p),1000,F(2))


def test_negative_reserve_is_rejected():
    p=bounded()
    with pytest.raises(ValueError): plan(p.scenarios,p.contract,-1)
