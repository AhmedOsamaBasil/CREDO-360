from fractions import Fraction as F
from dataclasses import replace
import pytest
from recovery_objective.core import (Action, Contract, Step, event_loss, feedback,
    allowed, choose, online, oracle, ONLINE_POLICIES)
from recovery_objective.cases import all_cases
from recovery_objective.checks import check_single_recipient, check_multi_recipient


def case(name):
    return next(c for c in all_cases() if c.name == name)


def test_event_positive_shortfall_not_cancelled_by_prior_or_event_surplus():
    assert event_loss(((3, 3), (3, 3)), ((5, 3), (1, 3)), (True, False)) == (2, 0)


def test_reference_cannot_be_silently_relaxed():
    with pytest.raises(ValueError): Step((4, 4), (Action('low', (3, 3)),))


def test_no_expiry_and_no_phantom_feasibility_payment():
    c = case('no_recipient_headroom')
    schedule = c.schedule * 30
    result = online('greedy_recovery', schedule, c.contract)
    assert result['outstanding'] == (2, 0)
    assert result['delivered_compensation'] == (0, 0)
    assert result['recovery_step'] is None and not result['all_recovered']


def test_delivered_credit_clipped_to_unpaid_loss_no_future_prepayment():
    s = Step((3, 3), (Action('baseline', (3, 3)), Action('boost', (5, 2))))
    c = Contract((F(1, 2), 0), (0, 1), (0, 1))
    debt, spent, credit = feedback(s, s.actions[1], c, c.debt, (0, 0))
    assert debt == (0, 0) and credit == (F(1, 2), 0) and spent == (0, 1)


def test_cumulative_donor_harm_not_cancelled_by_prior_surplus():
    c = Contract((2, 0), (0, 1), (0, 1))
    s = Step((3, 3), (Action('baseline', (3, 3)), Action('boost', (4, 2)), Action('donor_surplus', (3, 5))))
    debt, spent, _ = feedback(s, s.actions[1], c, c.debt, (0, 0))
    debt, spent, _ = feedback(s, s.actions[2], c, debt, spent)
    assert spent == (0, 1)
    assert s.actions[1] not in allowed(s, c, spent)


@pytest.mark.parametrize('policy', ONLINE_POLICIES)
def test_same_current_information_cannot_see_different_future(policy):
    a, b = case('forgotten_event'), case('donor_budget_trap')
    contract = a.contract
    ra = online(policy, a.schedule, contract, a.history)
    rb = online(policy, b.schedule, contract, a.history)
    assert ra['trace'][0]['action'] == rb['trace'][0]['action']


@pytest.mark.parametrize('policy', ONLINE_POLICIES)
def test_permutation_of_action_enumeration_preserves_named_decisions(policy):
    c = case('future_opportunity_trap')
    shuffled = tuple(replace(s, actions=tuple(reversed(s.actions))) for s in c.schedule)
    assert online(policy, c.schedule, c.contract, c.history) == online(policy, shuffled, c.contract, c.history)


@pytest.mark.parametrize('name', ('zero_harm_allowance', 'no_recipient_headroom', 'quality_ceiling'))
def test_unrepayable_loss_remains_visible_for_every_policy(name):
    c = case(name)
    for policy in ONLINE_POLICIES:
        r = online(policy, c.schedule, c.contract, c.history)
        assert r['outstanding'] == c.contract.debt
    assert oracle(c.schedule, c.contract)['terminal_max_fraction'] == 1


def test_forgetting_witness_strict_recovery_separation_not_fairness_dominance():
    c = case('forgotten_event')
    recovery = online('greedy_recovery', c.schedule, c.contract, c.history)
    for policy in ('rolling_nash', 'rolling_maxmin'):
        r = online(policy, c.schedule, c.contract, c.history)
        assert r['outstanding'] == (2, 0) and recovery['outstanding'] == (0, 0)
        assert recovery['worst_post_quality'] < r['worst_post_quality']
    assert recovery['donor_spent'] == (0, 2)


def test_equal_success_not_cherry_picked_as_exclusive_benefit():
    c = case('shared_success_with_slack')
    for policy in ('rolling_nash', 'rolling_maxmin', 'greedy_recovery'):
        assert online(policy, c.schedule, c.contract, c.history)['all_recovered']


def test_myopic_recovery_fails_on_future_opportunity():
    c = case('future_opportunity_trap')
    greedy = online('greedy_recovery', c.schedule, c.contract, c.history)
    best = oracle(c.schedule, c.contract)
    assert greedy['terminal_max_fraction'] == 1 and best['terminal_max_fraction'] == F(1, 2)
    assert online('max_weight', c.schedule, c.contract, c.history)['terminal_max_fraction'] == F(1, 2)


def test_myopic_recovery_loses_to_rolling_nash_with_scarce_donor_budget():
    c = case('donor_budget_trap')
    greedy = online('greedy_recovery', c.schedule, c.contract, c.history)
    nash = online('rolling_nash', c.schedule, c.contract, c.history)
    assert greedy['outstanding'] == (1, 0) and nash['outstanding'] == (0, 0)
    assert oracle(c.schedule, c.contract)['outstanding'] == (0, 0)


def test_no_event_reduces_greedy_to_current_nash_tiebreak():
    s = Step((3, 3), (Action('base', (3, 3)), Action('better', (4, 3))))
    c = Contract((0, 0), (0, 0), (0, 0))
    assert choose('greedy_recovery', s, c, c.debt, (0, 0), ()).name == 'better'


def test_indistinguishable_first_slot_requires_different_oracle_choices():
    a, b = case('donor_budget_trap'), case('opportunity_disappears')
    assert a.schedule[0] == b.schedule[0] and a.contract == b.contract and a.history == b.history
    assert oracle(a.schedule, a.contract)['trace'][0]['action'] == 'baseline'
    assert oracle(b.schedule, b.contract)['trace'][0]['action'] == 'compensate'
    for policy in ONLINE_POLICIES:
        ra = online(policy, a.schedule, a.contract, a.history)
        rb = online(policy, b.schedule, b.contract, b.history)
        assert ra['trace'][0]['action'] == rb['trace'][0]['action']
        assert (ra['terminal_max_fraction'] > oracle(a.schedule, a.contract)['terminal_max_fraction'] or
                rb['terminal_max_fraction'] > oracle(b.schedule, b.contract)['terminal_max_fraction'])


def test_finite_exact_model_checks():
    assert check_single_recipient()['cases'] == 480
    result = check_multi_recipient()
    assert result['cases'] == 24
    assert result['policy_relationships']['greedy_recovery']['strictly_above_terminal_oracle'] > 0


def test_resource_constraint_is_shared_and_enforced():
    s = Step((3, 3), (Action('baseline', (3, 3)), Action('unaffordable', (5, 5), F(2))))
    c = Contract((1, 1), (0, 0), (0, 0))
    for p in ONLINE_POLICIES:
        assert choose(p, s, c, c.debt, (0, 0), ()).name == 'baseline'


def test_invalid_contract_and_nonpositive_utilities_rejected():
    with pytest.raises(ValueError): Contract((1, 0), (1, 1), (0, 1))
    with pytest.raises(ValueError): Contract((-1, 0), (0, 1), (0, 1))
    with pytest.raises(ValueError): Action('bad', (0, 3))
