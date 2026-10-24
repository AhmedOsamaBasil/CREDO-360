import numpy as np
import pytest
from objective_diagnostics.core import Ledger, contract, range_cap, select, POLICIES
from horizon_recovery.core import contract as previous_contract, action_table


def example():
    q = np.array([[1,2,3,4,4.5,5],[1,2.5,3.2,3.9,4.4,4.9]])
    c = np.array([[1,2,4,7,12,20],[1,3,5,8,13,21]],float)
    return q,c


def test_floor_contract_matches_frozen_solver():
    q,c = example()
    a,b = contract(q[None],.2,c[None],15,4), previous_contract(q[None],.2,c[None],15)
    assert a == b


def test_uncapped_target_can_exceed_four_but_remains_jointly_feasible():
    q = np.full((2,2,6),4.6); c = np.ones_like(q)
    assert contract(q,0,c,2,4)['target'] == pytest.approx([4,4])
    result = contract(q,0,c,2,5)
    assert result['target'] == pytest.approx([4.6,4.6])
    assert all(w['bytes'] <= w['byte_cap'] <= 2 for w in result['witness'])


def test_bank_cannot_be_mistaken_for_nonbank():
    ledger = Ledger(24,1)
    ledger.begin('bank'); ledger.update([4],[5])
    ledger.begin('bank'); ledger.update([4],[3.5])
    assert ledger.balance('bank') == [-.5]
    assert ledger.balance('nobank') == [.5]
    assert ledger.balance('memoryless') == [12.]


@pytest.mark.parametrize('mode',['bank','nobank'])
def test_terminal_prediction_equals_actual_window_update(mode):
    ledger = Ledger(3,2)
    for q in ([5,2],[3,4],[4.5,3]):
        ledger.begin(mode); ledger.update([4,4],q)
    expired,_ = ledger.begin(mode)
    assert expired == pytest.approx([-1,2])
    before = ledger.balance(mode)
    expected = np.maximum(before+np.array([4,4])-np.array([3.8,4.2]),0)
    ledger.update([4,4],[3.8,4.2])
    assert np.maximum(ledger.balance(mode),0) == pytest.approx(expected)
    assert len(ledger.residuals) == 3


def test_expiry_is_separate_and_cannot_be_reported_as_delivery():
    ledger = Ledger(2,1)
    ledger.begin('nobank'); ledger.update([4],[1])
    ledger.begin('nobank'); ledger.update([4],[4])
    expired,change = ledger.begin('nobank')
    assert expired == [3] and change == [-3]
    assert ledger.balance('nobank') == [0]


def test_negative_credit_used_in_candidate_terminal_score():
    q,c = example(); ledger = Ledger(24,2)
    for _ in range(5):
        ledger.begin('bank'); ledger.update([4,4],[5,5])
    ledger.begin('bank')
    a,info = select('floor_bank',q,.2,c,15,[4,4],ledger)
    b,_ = select('nash',q,.2,c,15,[4,4],ledger)
    assert np.array_equal(a,b)
    assert info['predicted_terminal'] == pytest.approx([0,0])


@pytest.mark.parametrize('policy',POLICIES)
def test_all_policies_respect_shared_cap(policy):
    q,c = example(); ledger = Ledger(24,2); ledger.begin('bank')
    action,info = select(policy,q,.2,c,15,[4,4],ledger)
    assert c[np.arange(2),action].sum() <= info['nash_bytes'] <= 15


def test_instant_leximin_is_exact():
    q,c = example(); ledger=Ledger(24,2); ledger.begin('bank')
    action,_ = select('instant_maxmin',q,.2,c,15,[4,4],ledger)
    table = action_table(q,.2,c,15)
    assert tuple(sorted(q[np.arange(2),action])) == max(tuple(sorted(row)) for row in table['quality'])


def test_rolling_rule_responds_to_past_disparity_above_floor():
    q=np.array([[4,4.2,4.4,4.6,4.8,5]]*2); c=np.array([[1,2,3,4,5,6]]*2)
    ledger=Ledger(24,2)
    for _ in range(10):
        ledger.begin('bank'); ledger.update([4,4],[4.1,4.9])
    ledger.begin('bank')
    a,_=select('window_maxmin',q,0,c,7,[4,4],ledger)
    assert a[0] > a[1]


def test_normalized_profile_uses_prefix_max_even_if_nonmonotone():
    q=np.array([2,3,2.5,4,3.5,5])
    cap=range_cap(q)
    assert cap == 2
    assert q.max()-q[:cap+1].max() >= .5*(q.max()-q[0])
    assert range_cap(np.full(6,5.)) == 5


def test_invalid_state_cycle_rejected():
    ledger=Ledger(2,1)
    with pytest.raises(RuntimeError): ledger.update([4],[3])
    ledger.begin('bank')
    with pytest.raises(RuntimeError): ledger.begin('bank')
