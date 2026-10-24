from dataclasses import replace
import json
import pytest
from causal_playback.data import Record
from causal_playback.core import decide,residuals,neighbors,POLICIES,menu
from causal_playback.clock import State
from causal_playback.replay import simulate,choose_step,reserve
from service_opportunity.model import optimize,brute


def sample(key='target',offset=0):
    q=(2000,2500,3000,3500,4000,4500)
    quality=tuple((tuple(x+offset for x in q),q) for _ in range(6))
    sender=(q,)*6; costs=((10000,20000,100000,400000,800000,1800000),)*6
    return Record(key,'v2','scene',1,2,2000,quality,sender,costs)


def training(): return tuple(sample(f'train{i}',i*5) for i in range(8))


def test_residual_uses_only_selected_feedback():
    r=sample(); obs=((0,0,0,2200),(0,1,2,3000),(1,0,0,2400),(1,1,2,2800))
    assert residuals(obs,r.sender)==(300,-100)


def test_missing_history_rejected():
    with pytest.raises(ValueError): residuals(((0,0,0,2000),),sample().sender)


def test_current_observation_rejected():
    r=sample(); s=State(r); view,_=s.view(0)
    view['observations']+=((2,0,2,3000),)
    with pytest.raises(ValueError): decide('knn_recovery',r.loss,**view,sender=r.sender,costs=r.costs,t=2,training=training(),reserve=reserve(r))


def test_structural_floor():
    r=sample(); ps=menu(((5000,)*6,(5000,)*6),r.costs[2])
    assert len(ps)==16 and all(min(a.rungs)>=2 for a in ps)


def test_prediction_clipping():
    r=sample(); state=State(r); v,_=state.view(0)
    v['observations']=((0,0,0,5000),(0,1,0,1000))
    a=decide('knn_recovery',r.loss,**v,sender=r.sender,costs=r.costs,t=2,training=training(),reserve=reserve(r))
    assert max(a['current_estimates'][0])==5000 and min(a['current_estimates'][1])==1000


def test_no_current_or_future_label_leakage():
    r=sample(); changed=replace(r,quality=r.quality[:2]+((((1000,)*6,(5000,)*6),)*4))
    s=State(r); altered=State(changed)
    for t,start in ((2,0),(3,10)):
        a,info=choose_step(r,training(),s,'knn_recovery',t,start)
        b,other=choose_step(changed,training(),altered,'knn_recovery',t,start)
        assert a==b and info==other
        if t==2:
            s.deliver(r,t,a,(5,5),10); altered.deliver(changed,t,b,(5,5),10)
    # First changed labels are legitimately available only after playback end15.
    assert s.view(15)[0]['observations']!=altered.view(15)[0]['observations']


def test_download_is_not_playback_feedback():
    r=sample(); s=State(r); a,_=choose_step(r,training(),s,'knn_recovery',2,0)
    s.deliver(r,2,a,(2,4),10)
    v,released=s.view(10)
    assert not released and len(v['observations'])==4
    assert len(s.view(12)[1])==1 and len(s.view(14)[1])==1


def test_pending_commitments_not_actual_credit():
    r=sample(); s=State(r); a,_=choose_step(r,training(),s,'knn_recovery',2,0)
    s.deliver(r,2,a,(2,4),10)
    v,_=s.view(10)
    assert v['observed_credit']==0 and v['pending_gains']==(a['predicted_gain'],)


def test_clock_counts_controller_and_waiting():
    r=sample(); s=State(r); a,_=choose_step(r,training(),s,'greedy_recovery',2,.5)
    s.deliver(r,2,a,(2,4),10)
    assert s.stall.tolist()==[2,4] and s.finish.tolist()==[12,14]


def test_last_media_no_post_end_stall():
    r=sample(); s=State(r)
    for t in range(2,6):
        start=(t-2)*10; a,_=choose_step(r,training(),s,'cost_greedy',t,start)
        arrivals=(start+1,start+1) if t<5 else (31,60)
        s.deliver(r,t,a,arrivals,max(start+10,max(arrivals)))
    result=s.final()
    assert result['media_finish_seconds']==[41,70]
    assert result['stall_seconds']==[1,30]


def test_clock_backward_rejected():
    s=State(sample()); s.idle(1)
    with pytest.raises(ValueError): s.idle(.5)


def test_arrival_after_barrier_rejected():
    r=sample(); s=State(r); a,_=choose_step(r,training(),s,'cost_greedy',2,0)
    with pytest.raises(ValueError): s.deliver(r,2,a,(1,11),10)


def test_incomplete_final_rejected():
    with pytest.raises(ValueError): State(sample()).final()


def test_all_policies_budget_and_clock():
    r=sample()
    for policy in POLICIES:
        out=simulate(r,training(),policy)
        assert out['extra_bytes']<=reserve(r)
        assert out['donor_floor_violations']==out['recipient_floor_violations']==0
        assert all(max(round['decision']['rungs'])<=5 and sum(round['file_bytes'])<=1500000 for round in out['rounds'])
        assert all(abs(finish-40-stall)<1e-7 for finish,stall in zip(out['media_finish_seconds'],out['stall_seconds']))


def test_unpredicted_floor_loss_retained():
    r=sample(); s=State(r); a,_=choose_step(r,training(),s,'greedy_recovery',2,0)
    for t in range(2,6):
        a,_=choose_step(r,training(),s,'cost_greedy',t,(t-2)*10)
        if t==2:
            a={**a,'rungs':(2,3),'predicted_quality':(3000,3500),'predicted_gain':0,
               'bytes':500000,'extra_bytes':300000}
        q=list(r.quality); current=[list(x) for x in q[t]]
        if a['rungs'][1]>2: current[1][a['rungs'][1]]=1000
        q[t]=tuple(tuple(x) for x in current); changed=replace(r,quality=tuple(q))
        s.deliver(changed,t,a,((t-2)*10+2,)*2,(t-1)*10)
    result=s.final()
    assert result['donor_floor_violations']>=1


def test_dp_brute_structural_menu():
    r=sample(); p=menu(r.quality[2],r.costs[2])
    for debt in (0,500,2000):
        for budget in (0,100000,600000,1200000):
            assert optimize((p,p),debt,budget)[:2]==brute((p,p),debt,budget)[:2]


def test_neighbor_no_target_inputs():
    r=sample(); obs=((0,0,0,2000,2000),(0,1,2,3000,3000))
    assert len(neighbors(obs,r.loss,training()))==8


def test_zero_reserve_uses_baseline():
    r=sample(); s=State(r); v,_=s.view(0)
    for policy in POLICIES:
        a=decide(policy,r.loss,**v,sender=r.sender,costs=r.costs,t=2,training=training(),reserve=0)
        assert a['rungs']==(2,2)


def test_repeat_determinism():
    assert simulate(sample(),training(),'knn_recovery')==simulate(sample(),training(),'knn_recovery')
