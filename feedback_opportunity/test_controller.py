from dataclasses import replace
from copy import deepcopy
import pytest
from causal_playback.test_core import sample,training
from causal_playback.core import POLICIES
from feedback_opportunity.controller import simulate,FeedbackState


def feedback(r): return {(r.cohort,r.scene,sid,t):r.quality[t][u] for t in range(6) for u,sid in enumerate((r.recipient,r.donor))}


@pytest.mark.parametrize('policy',POLICIES)
def test_hidden_evaluation_labels_never_control_actions(policy):
    r=sample(); fb=feedback(r)
    altered=replace(r,loss=9999,quality=tuple(((1000,)*6,(5000,)*6) for _ in range(6)))
    a=simulate(r,training(),policy,fb); b=simulate(altered,training(),policy,fb)
    assert a['estimated_loss_units']==b['estimated_loss_units']==2000
    for x,y in zip(a['rounds'],b['rounds']):
        assert x['decision']==y['decision'] and x['view']==y['view']
    assert a['unpaid_fraction']!=b['unpaid_fraction']


def test_feedback_future_unavailable_until_played():
    r=sample(); fb=feedback(r); changed=dict(fb)
    changed[r.cohort,r.scene,r.recipient,3]=(1000,)*6
    a=simulate(r,training(),'knn_recovery',fb)
    b=simulate(r,training(),'knn_recovery',changed)
    for i in range(3): assert a['rounds'][i]['decision']==b['rounds'][i]['decision']


def test_zero_feedback_loss_not_fabricated():
    r=sample(); fb=feedback(r)
    for t in (0,1): fb[r.cohort,r.scene,r.recipient,t]=(3000,)*6
    for policy in POLICIES:
        a=simulate(r,training(),policy,fb)
        assert a['estimated_loss_units']==0 and a['original_loss_units']==2000


def test_feedback_only_after_playback():
    r=sample(); fb=feedback(r); state=FeedbackState(r,fb)
    decision={'rungs':(3,2),'predicted_quality':(3500,3000),'predicted_gain':500,'extra_bytes':300000}
    state.deliver(r,2,decision,(2,4),10)
    assert state.view(10)[0]['observed_credit']==0
    assert state.view(12)[0]['observed_credit']==500
