from dataclasses import replace
import numpy as np
import pytest
from causal_playback.test_core import sample
from feedback_opportunity.test_controller import feedback
from feedback_opportunity.feedback import mask
from early_commitment.prepare import forecast
from early_commitment.core import visible_index,wait_time,transfer_offsets,decision,POLICIES
from early_commitment.replay import simulate


def forecasts(r):
    return {f'{r.cohort}:{r.scene}:{sid}':[[list(r.quality[t][u]) for t in range(6)] for h in range(60)] for u,sid in enumerate((r.recipient,r.donor))}


def test_future_masks_not_an_input():
    maps=np.full((6,60,6,12),20.); maps[:,:,:,4:8]=200.; maps=maps.reshape(6,60,72)
    a=[mask(0,0)]*60; b=a[:20]+[mask(170,0)]*40
    assert forecast(maps,a[:20])==forecast(maps,b[:20])
    assert forecast(maps,a)!=forecast(maps,b)


def test_completed_segment_forecast_unchanged_by_later_pose():
    maps=np.arange(6*60*72).reshape(6,60,72)+1.
    a=[mask(0,0)]*20
    assert forecast(maps,a)[:2]==forecast(maps,a+[mask(170,0)]*30)[:2]


def test_log_of_average_not_average_log():
    maps=np.ones((6,60,72)); maps[:,1::2,:]=100
    expected=int(np.floor(np.clip(1+(10*np.log10(255**2/50.5)-18)/6,1,5)*1000+.5))
    assert forecast(maps,[mask(0,0)])[0]==[expected]*6


def test_visible_prefix_waits_for_play_and_report():
    items=[{'segment':2,'play_end':(15,18)}]
    assert visible_index(items,0,5.57,.08,True)==19
    assert visible_index(items,0,5.58,.08,True)==20
    assert visible_index(items,1,10,.08,True)==21
    assert visible_index(items,0,14.99,.08,False)==19
    assert visible_index(items,0,15.08,.08,False)==29


def test_waiting_for_completion_requires_starvation_without_other_buffer():
    r=sample(); items=[{'segment':2,'play_end':(15.,15.)}]
    assert wait_time('wait_mpc',items,10,r.costs[3],800000,.08)==15.08
    assert wait_time('slack_mpc',items,10,r.costs[3],800000,.08)==10
    next_arrival=15.08+transfer_offsets((100000,100000))[0]
    assert next_arrival-15==pytest.approx(.08+.13+200000*8/1_200_000)


def test_slack_wait_allowed_with_another_queued_segment():
    r=sample(); items=[{'segment':2,'play_end':(15.,15.)},{'segment':3,'play_end':(25.,25.)}]
    assert wait_time('slack_mpc',items,14,r.costs[4],0,.08)==15.08


def test_no_free_wait_at_start():
    assert wait_time('wait_mpc',[],0,sample().costs[2],800000,.08)==0


@pytest.mark.parametrize('policy',POLICIES)
def test_hidden_labels_never_control_any_action(policy):
    r=sample(); changed=replace(r,loss=3000,quality=tuple(((1000,)*6,(5000,)*6) for t in range(6)))
    fb=feedback(r); fs=forecasts(r)
    a=simulate(r,policy,fb,fs); b=simulate(changed,policy,fb,fs)
    assert a['unpaid_fraction']!=b['unpaid_fraction']
    for x,y in zip(a['rounds'],b['rounds']):
        for key in ('decision','visible_indices','start','pending_gains','history'): assert x[key]==y[key]


def test_unavailable_prefix_mutations_do_not_change_first_decision():
    r=sample(); fs=forecasts(r); altered=forecasts(r)
    for key in altered:
        for h in range(20,60): altered[key][h]=[[1000]*6 for t in range(6)]
    a=simulate(r,'prefix_mpc',feedback(r),fs); b=simulate(r,'prefix_mpc',feedback(r),altered)
    assert a['rounds'][0]['decision']==b['rounds'][0]['decision']


def test_pending_projection_is_not_delivered_credit():
    r=sample(); result=simulate(r,'prefix_cost_greedy',feedback(r),forecasts(r))
    assert result['rounds'][1]['decision']['observed_credit']==0
    assert result['rounds'][1]['decision']['pending_predicted_credit']>0


@pytest.mark.parametrize('policy',POLICIES)
def test_clock_and_finite_reserve(policy):
    r=sample(); result=simulate(r,policy,feedback(r),forecasts(r))
    assert result['extra_bytes']<=result['reserve_bytes']
    for u in (0,1): assert result['media_finish_seconds'][u]==pytest.approx(40+result['stall_seconds'][u])
    assert all(sum(s['file_bytes'])<=1500000 for s in result['rounds'])


def test_lookahead_saves_scarce_allowance_for_later_gain():
    r=sample(); q=list(r.quality)
    q[2]=((2000,2500,3000,3100,3100,3100),r.quality[2][1])
    q[3]=((2000,2500,3000,4000,4000,4000),r.quality[3][1])
    q[4]=q[5]=((3000,)*6,(3000,)*6)
    common=(q,r.costs,2,2000,0,[],[(2000,3000)]*2,300000)
    a=decision('prefix_mpc',*common); b=decision('prefix_cost_greedy',*common)
    assert a['rungs']==(2,2) and a['planned_rungs'][1]==(3,2)
    assert b['rungs']==(3,2)


@pytest.mark.parametrize('h', [0,61])
def test_invalid_prefix_lengths(h):
    with pytest.raises(ValueError): forecast(np.ones((6,60,72)),[mask(0,0)]*h)
