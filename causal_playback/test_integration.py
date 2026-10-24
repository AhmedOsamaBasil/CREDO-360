"""Additional post-run verification tests; no controller changes."""
from copy import deepcopy
from dataclasses import replace
import pytest
from causal_playback.test_core import sample,training
from causal_playback.core import POLICIES
from causal_playback.replay import simulate
from causal_playback.check_support import clock_ledger
from reserve_recovery.run import encode


@pytest.mark.parametrize('policy',POLICIES)
def test_future_mutations_at_every_decision(policy):
    r=sample(); original=simulate(r,training(),policy)
    for t in range(2,6):
        altered=replace(r,quality=r.quality[:t]+((((1000,)*6,(5000,)*6),)*(6-t)))
        changed=simulate(altered,training(),policy)
        for j in range(t-1):
            assert original['rounds'][j]['decision']==changed['rounds'][j]['decision']
            assert original['rounds'][j]['view']==changed['rounds'][j]['view']


def test_independent_clock_matches_all_policies():
    r=sample()
    for policy in POLICIES:
        row=encode(simulate(r,training(),policy)); result=clock_ledger(row,r)
        assert result['startup']>0 and result['additional_stall']>=0


def test_premature_feedback_rejected_by_independent_check():
    r=sample(); row=encode(simulate(r,training(),'knn_recovery'))
    assert len(row['rounds'][1]['view']['observations'])==4
    row['rounds'][1]['view']['observations'].append([2,0,2,3000])
    with pytest.raises(AssertionError): clock_ledger(row,r)


def test_false_credit_rejected_by_independent_check():
    r=sample(); row=encode(simulate(r,training(),'knn_recovery'))
    row['rounds'][1]['view']['observed_credit']=10
    with pytest.raises(AssertionError): clock_ledger(row,r)


def test_omitted_startup_stall_rejected():
    r=sample(); row=encode(simulate(r,training(),'knn_recovery'))
    row['stall_seconds'][0]=0
    with pytest.raises(AssertionError): clock_ledger(row,r)


def test_wrong_selected_byte_count_rejected():
    r=sample(); row=encode(simulate(r,training(),'knn_recovery'))
    row['rounds'][0]['file_bytes'][0]+=1
    with pytest.raises(AssertionError): clock_ledger(row,r)
