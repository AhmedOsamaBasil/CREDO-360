from dataclasses import replace
from fractions import Fraction as F
import pytest
from causal_compensation.data import Episode,Offer,quality_units,make_offer
from causal_compensation.model import forecast,training_pool
from causal_compensation.core import plan
from causal_compensation.replay import replay,mixture,CONTROLS


def offer(g): return Offer((3000,3000),(3000+g,2500) if g else (3000,3000),g,500 if g else 0,200,180 if g else 200,(3,1) if g else (2,2))
def episode(scene='target',recipient=1,donor=2,gains=(200,300,500,1000,1200,1500)):
    return Episode('v2',scene,recipient,donor,2000,((2000,3000),(2000,3000)),tuple(offer(g) for g in gains))
def training(): return tuple(episode('other'+str(i),3+2*i,4+2*i) for i in range(8))


def test_quality_rounding_and_caps_are_explicit():
    assert quality_units('18')==1000 and quality_units('42')==5000
    assert quality_units('0')==1000 and quality_units('100')==5000
    assert quality_units('18.003')==1001


def test_transfer_menu_respects_quality_and_byte_constraints():
    r=(1000,2000,3000,3500,4000,4500); d=(2200,2600,3000,3500,4000,4500)
    o=make_offer(r,d,(20,40,100,150,190,250))
    assert o.gain==500 and o.harm==400 and o.transfer_bytes==190
    assert o.rungs==(3,1)
    assert make_offer(r,d,(120,140,100,250,300,350)).gain==0


def test_forecast_training_excludes_target_scene_and_both_participants():
    target=episode()
    pool=training_pool(training()+(target,episode('another',2,31),episode('target',35,36)),target.scene,1,2)
    assert len(pool)==8 and all(e.scene!='target' and not {1,2}.intersection((e.recipient,e.donor)) for e in pool)


def test_target_future_mutation_cannot_change_initial_forecast():
    target=episode(); changed=replace(target,offers=target.offers[:3]+tuple(offer(g) for g in (0,0,0)))
    results=[]
    for e in (target,changed):
        pool=training_pool(training()+(e,),e.scene,e.recipient,e.donor)
        results.append(forecast(tuple(o.gain for o in e.offers[:3]),e.loss,pool))
    assert results[0]==results[1]


def test_model_uses_past_signal_and_records_neighbors():
    r=forecast((200,300,500),2000,training())
    assert r['bounds']==((950,1050),(1150,1250),(1450,1550))
    assert len(r['neighbors'])==8 and all(n['distance']==0 for n in r['neighbors'])
    with pytest.raises(ValueError): forecast((1,2),2000,training())


def test_actual_event_history_is_given_to_rolling_controls():
    e=episode(gains=(0,0,1000,0,0,0))
    # Past deprivation changes the rolling Nash choice; history is not balanced.
    actual=replay(e,'rolling_nash')
    assert actual['trace'][0]['transfer']
    # With +1/-0.5 even balanced Nash may transfer: compare the objective via a smaller gain.
    small=replace(e,offers=e.offers[:2]+(offer(450),)+e.offers[3:])
    assert replay(small,'rolling_nash')['trace'][0]['transfer']
    assert not replay(replace(small,history=((3000,3000),)*23),'rolling_nash')['trace'][0]['transfer']


def test_all_policies_conserve_debt_and_spend_at_most_once():
    e=episode()
    for p in CONTROLS+tuple(range(6)):
        r=replay(e,p)
        assert sum(t['transfer'] for t in r['trace'])<=1
        assert r['trace'][-1]['outstanding']+sum(t['credit'] for t in r['trace'])==e.loss
        assert r['donor_loss']<=F(1,2) and r['regret']>=0


def test_model_miss_can_break_terminal_cap_without_breaking_donor_safety():
    e=episode(gains=(0,0,500,0,0,0))
    p=plan(e.loss,500,((1500,1500),)*3,F(1,2))
    assert p['feasible']
    r=mixture(e,p,F(1,2))
    assert r['expected']['model_breach']==1 and r['expected']['cap_violation']==1
    assert r['expected']['donor_loss']<=F(1,2)


def test_zero_loss_never_spends_and_never_divides_by_zero():
    e=replace(episode(),loss=0)
    for p in CONTROLS:
        r=replay(e,p)
        assert r['unpaid_fraction']==r['transfer_count']==r['regret']==0


def test_sampled_policy_does_not_change_before_future_is_observed():
    e=episode(); alternate=replace(e,offers=e.offers[:3]+(offer(0),)*3)
    for p in range(6):
        assert replay(e,p)['trace'][0]==replay(alternate,p)['trace'][0]
