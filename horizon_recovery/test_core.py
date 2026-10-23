"""Synthetic invariants; no held-out labels needed."""
import numpy as np
import pytest
from horizon_recovery.core import action_table, contract, WindowLedger, select_action
from horizon_recovery.run import caps, contracts, partition


def fixture():
    q = np.array([[1, 2, 3, 4, 4.5, 5], [1, 2.5, 3.2, 3.9, 4.4, 4.9]])
    c = np.array([[1, 2, 4, 7, 12, 20], [1, 3, 5, 8, 13, 21]], float)
    return q, c


def test_resource_cap_and_exact_objective():
    q, c = fixture()
    table = action_table(q, .2, c, 16)
    state, target = np.array([8., 2.]), np.array([3.5, 3.5])
    action, info = select_action('window_recovery', q, .2, c, 16, state, target, 12, 2)
    score = [sum(np.log(np.maximum(1, q[np.arange(2), a]-.2))) -
             2/(2*12)*sum(np.maximum(state+target-q[np.arange(2), a], 0)**2)
             for a in table['actions']]
    assert info['objective'] == pytest.approx(max(score))
    assert c[np.arange(2), action].sum() <= info['nash_bytes'] <= 16
    a, _ = select_action('nash', q, .2, c, 16, state, target, 12, 2)
    assert np.array_equal(a, table['nash_action'])


def test_joint_mixture_not_independent_maxima():
    q = np.array([[[1, 4, 4, 4, 4, 4], [1, 4, 4, 4, 4, 4]]], float)
    c = np.array([[[1, 2, 2, 2, 2, 2], [1, 2, 2, 2, 2, 2]]], float)
    result = contract(q, 0, c, 3)
    assert result['target'] == pytest.approx([2.5, 2.5])
    assert result['ceiling'] == pytest.approx([4, 4])
    assert sum(w['probability'] for w in result['witness']) == pytest.approx(1)
    assert all(w['bytes'] <= w['byte_cap'] <= 3 for w in result['witness'])


def test_capped_user_does_not_limit_other_entitlements():
    q = np.array([[[1, 1, 1, 1, 1, 1], [1, 2, 3, 4, 5, 5]]], float)
    c = np.ones_like(q)
    result = contract(q, 0, c, 2)
    assert result['target'] == pytest.approx([1, 4])


def test_contract_permutation_and_witness():
    q, c = fixture()
    prediction, costs = np.stack([q, q[:, ::-1]]), np.stack([c, c[:, ::-1]])
    result = contract(prediction, .3, costs, 15)
    permuted = contract(prediction[:, ::-1], .3, costs[:, ::-1], 15)
    assert result['target'] == pytest.approx(permuted['target'][::-1])
    actual = np.zeros(2)
    for t in range(2):
        rows = [w for w in result['witness'] if w['period'] == t]
        assert sum(w['probability'] for w in rows) == pytest.approx(1)
        for w in rows:
            assert w['bytes'] <= w['byte_cap'] + 1e-8
            actual += w['probability']*np.array(w['quality'])/2
    assert np.all(actual >= np.array(result['target'])-1e-7)


def test_signed_credit_expiry_and_scale_match():
    ledger = WindowLedger(2, 1)
    ledger.update([4], [2])
    assert ledger.state('window_recovery') == [2]
    assert ledger.state('memoryless_scaled') == [4]
    ledger.update([4], [5])
    assert ledger.state('window_recovery') == [1]
    assert ledger.state('memoryless_scaled') == [0]
    expired = ledger.update([4], [3])
    assert expired == [2]  # expiration is not delivery of compensation
    assert ledger.state('window_recovery') == [0]


def test_state_bounded_and_memoryless_discards_old_history():
    ledger = WindowLedger(12, 2)
    for _ in range(40):
        ledger.update([4, 4], [1, 5])
    assert np.array_equal(ledger.state('window_recovery'), [36, 0])
    assert np.array_equal(ledger.state('memoryless_scaled'), [36, 0])
    ledger.update([4, 4], [4, 4])
    assert np.array_equal(ledger.state('memoryless_scaled'), [0, 0])
    assert np.array_equal(ledger.state('window_recovery'), [33, 0])


def test_split_and_feedback_delay():
    split = partition([str(i) for i in range(28)])
    assert len(split['calibration']) == 9 and len(split['test']) == 19
    assert not set(split['calibration']) & set(split['test'])
    assert caps('delayed_ceiling', 40, 1)[1] == 5
    assert caps('delayed_ceiling', 40, 1, observed=False)[1] == 1
    assert caps('delayed_ceiling', 80, 1)[1] == 1
    assert caps('delayed_ceiling', 81, 1)[1] == 5


def test_contract_has_no_future_bandwidth_access(monkeypatch):
    import horizon_recovery.run as run
    monkeypatch.setattr(run, 'tables', lambda *a, **k: (None, None))
    monkeypatch.setattr(run, 'contract', lambda q, r, c, b: {'budget': b})
    plan = {'impaired_user': 0, 'capacities_mbps': [3.]*120}
    first = contracts({'radius': 0}, plan, 'known_ceiling')
    plan['capacities_mbps'][40:] = [1.]*80
    second = contracts({'radius': 0}, plan, 'known_ceiling')
    for t in first:
        if int(t) <= 40:
            assert first[t]['budget'] == second[t]['budget']


@pytest.mark.parametrize('radius,budget', [(-1, 3), (0, -1), (float('nan'), 3)])
def test_invalid_inputs(radius, budget):
    q, c = fixture()
    with pytest.raises(ValueError):
        action_table(q, radius, c, budget)
