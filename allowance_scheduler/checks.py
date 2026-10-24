"""Exact finite model checks, never performance estimates on empirical data."""
from fractions import Fraction as F
from itertools import product
from allowance_scheduler.cases import two_future, problems
from allowance_scheduler.core import plan, observation, execute
from allowance_scheduler.game import minimax, verify_certificate


def model_checks():
    formula_cases = []
    grid = (F(1,4), F(1,2), F(1), F(3,2), F(2))
    for a, b, debt in product(grid, grid, (F(2), F(3), F(4))):
        if not a < b: continue
        problem = two_future(a, b, debt)
        result = plan(problem.scenarios, problem.contract)
        root = (observation(problem.scenarios[0][0]),)
        p = sum((w for w, rule in zip(result['solution']['weights'], result['policies']) if rule.mapping[root] == 'boost'), F(0))
        value = a*(b-a)/(b*debt)
        assert p == a/b and result['solution']['value'] == value
        formula_cases.append({'a': a, 'b': b, 'D': debt, 'spend_probability': p, 'regret_bound': value})
    games = 0
    for values in product((F(0), F(1,3), F(2,3), F(1)), repeat=4):
        matrix = (values[:2], values[2:])
        result = minimax(matrix)
        verify_certificate(matrix, result['weights'], result['dual'], result['value'])
        assert result['value'] <= min(max(row) for row in matrix)
        games += 1
    executions = 0
    for problem in problems():
        result = plan(problem.scenarios, problem.contract)
        # Check every enumerated causal policy, not only selected winners.
        for i, rule in enumerate(result['policies']):
            for j, scenario in enumerate(problem.scenarios):
                actual = execute(rule, problem.contract, scenario)
                assert not actual.pop('model_breach')
                assert actual == result['outcomes'][i][j]
                for initial, remaining, paid in zip(problem.contract.debt, actual['outstanding'], actual['delivered_compensation']):
                    assert initial == remaining+paid
                assert all(x <= b for x, b in zip(actual['donor_spent'], problem.contract.donor_total_allowance))
                executions += 1
    return {'closed_form_cases': formula_cases, 'matrix_games_checked': games,
            'causal_policy_scenario_executions': executions, 'exact_certificate_and_pathwise_guards': True}
