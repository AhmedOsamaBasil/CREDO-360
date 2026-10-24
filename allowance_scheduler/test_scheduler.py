from fractions import Fraction as F
from dataclasses import replace
from itertools import product
import random
import pytest
from allowance_scheduler.core import (causal_policies, plan, Controller, observation,
    execute, expected_summary, sample_policy)
from allowance_scheduler.cases import two_future, problems, offer
from allowance_scheduler.game import minimax, verify_certificate
from allowance_scheduler.checks import model_checks
from recovery_objective.core import online, Action, Step


def problem(name): return next(p for p in problems() if p.name == name)


def test_exact_ambiguous_allowance_bound_and_strict_regret_comparison():
    p = two_future(); r = plan(p.scenarios, p.contract)
    assert r['solution']['value'] == F(1,4)
    assert min(max(row) for row in r['regrets']) == F(1,2)
    for baseline in ('rolling_nash', 'rolling_maxmin', 'greedy_recovery', 'max_weight'):
        regrets = [online(baseline, s, p.contract, p.history)['terminal_max_fraction']-b
                   for s, b in zip(p.scenarios, r['benchmarks'])]
        assert max(regrets) == (F(1) if baseline == 'rolling_maxmin' else F(1,2))
    # Better regret does not imply better worst absolute unpaid fraction.
    mixed = expected_summary(r, r['solution']['weights'])
    assert max(x['terminal_max_fraction'] for x in mixed) == F(3,4)
    assert max(r['losses'][r['absolute_minimax']]) == F(1,2)


def test_shared_prefix_cannot_choose_after_seeing_latent_future():
    p = two_future(); r = plan(p.scenarios, p.contract)
    for rule in r['policies']:
        a, b = Controller(rule, p.contract), Controller(rule, p.contract)
        assert a.advance(p.scenarios[0][0]).name == b.advance(p.scenarios[1][0]).name
    assert not any(max(row) == 0 for row in r['regrets'])


def test_delayed_revelation_does_not_grant_second_step_clairvoyance():
    p = problem('three_period_delayed_revelation'); r = plan(p.scenarios, p.contract)
    for rule in r['policies']:
        a, b = Controller(rule, p.contract), Controller(rule, p.contract)
        for t in range(2):
            assert a.advance(p.scenarios[0][t]).name == b.advance(p.scenarios[1][t]).name
    for i, w in enumerate(r['solution']['weights']):
        if w:
            assert r['policies'][i].paths[0][0].name == 'baseline'


@pytest.mark.parametrize('name,first', [('known_disappearance', 'boost'), ('known_better_later', 'baseline')])
def test_known_future_models_change_when_allowance_is_spent(name, first):
    p = problem(name); r = plan(p.scenarios, p.contract)
    assert r['solution']['value'] == 0
    for rule, weight in zip(r['policies'], r['solution']['weights']):
        if weight: assert Controller(rule, p.contract).advance(p.scenarios[0][0]).name == first


def test_misspecified_future_invalidates_certificate_but_not_protection():
    p = problem('known_better_later'); r = plan(p.scenarios, p.contract)
    actual = two_future().scenarios[0]
    for i, w in enumerate(r['solution']['weights']):
        if w:
            trace = execute(r['policies'][i], p.contract, actual)
            assert trace['model_breach'] and trace['outstanding'] == (2, 0)
            assert trace['donor_spent'] == (0, 0)
            assert trace['terminal_max_fraction']-F(1,2) > r['solution']['value']


def test_adversary_observing_random_policy_breaks_oblivious_bound():
    p = two_future(); r = plan(p.scenarios, p.contract)
    adaptive = sum((w*max(row) for w, row in zip(r['solution']['weights'], r['regrets'])), F(0))
    assert adaptive == F(1,2) > r['solution']['value'] == F(1,4)


def test_model_breach_fallback_is_persistent_and_uses_current_safe_set():
    p = two_future(); r = plan(p.scenarios, p.contract)
    c = Controller(r['policies'][0], p.contract)
    unexpected = Step((3,3), (Action('baseline', (3,3)), Action('unexpected', (4,3))))
    c.advance(unexpected)
    assert c.model_breach
    c.advance(offer(2))
    assert c.model_breach and all(v <= b for v, b in zip(c.spent, p.contract.donor_total_allowance))


def test_zero_regret_is_not_zero_unpaid_loss():
    p = problem('no_donor_allowance'); r = plan(p.scenarios, p.contract)
    assert r['solution']['value'] == 0
    assert all(row['terminal_max_fraction'] == 1 for row in expected_summary(r, r['solution']['weights']))


def test_two_recipients_use_integral_protected_paths_not_fractional_actions():
    p = problem('two_recipient_opportunities'); r = plan(p.scenarios, p.contract)
    assert r['solution']['value'] == F(1,4)
    assert expected_summary(r, r['solution']['weights'])[0]['terminal_max_fraction'] == F(3,4)
    for rule in r['policies']:
        for s in p.scenarios:
            trace = execute(rule, p.contract, s)
            assert all(x <= b for x, b in zip(trace['donor_spent'], p.contract.donor_total_allowance))


def test_random_sampler_uses_exact_partition_and_is_episode_local():
    class Draw:
        def __init__(self, n): self.n = n
        def randrange(self, denominator):
            assert denominator == 3
            return self.n
    assert [sample_policy((F(1,3), F(2,3)), Draw(i)) for i in range(3)] == [0, 1, 1]
    with pytest.raises(ValueError): sample_policy((F(1,3), F(1,3)), random.Random(0))


def test_reordering_actions_or_scenarios_preserves_game_value():
    p = problem('three_possible_future_gains'); original = plan(p.scenarios, p.contract)
    schedules = tuple(tuple(replace(s, actions=tuple(reversed(s.actions))) for s in path) for path in reversed(p.scenarios))
    changed = plan(schedules, p.contract)
    assert changed['solution']['value'] == original['solution']['value']


def test_exact_dual_certification_with_three_support_rows():
    matrix = ((F(1),F(0),F(0)), (F(0),F(1),F(0)), (F(0),F(0),F(1)))
    r = minimax(matrix)
    assert r['weights'] == r['dual'] == (F(1,3),)*3 and r['value'] == F(1,3)
    verify_certificate(matrix, r['weights'], r['dual'], r['value'])


def test_duplicate_and_dominated_rows_keep_full_dual_certificate():
    matrix = ((0,1), (1,0), (0,1), (1,1))
    r = minimax(matrix)
    assert r['value'] == F(1,2) and r['weights'][2:] == (0,0)
    assert len(r['certificate']['policy_lower']) == 4


def test_tampered_primal_or_dual_witness_is_rejected():
    matrix = ((F(0), F(1)), (F(1), F(0)))
    r = minimax(matrix)
    with pytest.raises(AssertionError):
        verify_certificate(matrix, (F(1), F(0)), r['dual'], r['value'])
    with pytest.raises(AssertionError):
        verify_certificate(matrix, r['weights'], (F(1), F(0)), r['value'])
    with pytest.raises(AssertionError):
        verify_certificate(matrix, r['weights'], r['dual'], F(1,3))


def test_four_scenario_support_is_certified_at_reference_solver_limit():
    matrix = tuple(tuple(F(int(i == j)) for j in range(4)) for i in range(4))
    r = minimax(matrix)
    assert r['weights'] == r['dual'] == (F(1,4),)*4
    assert r['value'] == F(1,4)


def test_exact_results_agree_with_independent_floating_linear_program():
    from scipy.optimize import linprog
    import numpy as np
    for p in problems():
        r = plan(p.scenarios, p.contract); matrix = np.array(r['regrets'], dtype=float)
        m, n = matrix.shape
        optimum = linprog([0.]*m+[1.], A_ub=np.column_stack((matrix.T, -np.ones(n))), b_ub=np.zeros(n),
                          A_eq=[([1.]*m)+[0.]], b_eq=[1.], bounds=[(0,None)]*m+[(None,None)], method='highs')
        assert optimum.success
        assert optimum.fun == pytest.approx(float(r['solution']['value']), abs=1e-10)


def test_model_check_families():
    result = model_checks()
    assert len(result['closed_form_cases']) == 30
    assert result['matrix_games_checked'] == 256
    assert result['causal_policy_scenario_executions'] > 0


def test_small_reference_solver_limits_and_bad_inputs():
    with pytest.raises(ValueError): minimax(())
    with pytest.raises(ValueError): minimax(((0,), (1,2)))
    with pytest.raises(ValueError): minimax(((0,0,0,0,0),))
    p = two_future()
    with pytest.raises(ValueError): causal_policies((p.scenarios[0], (offer(1),)), p.contract)
