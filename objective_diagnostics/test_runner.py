import numpy as np
from objective_diagnostics import run


def model():
    return {'contexts':[(c,s) for c in ('a','b','c') for s in range(6)],
            'predicted':np.tile([1,2,3,4,4.5,5],(18,1)),
            'sizes':np.tile(np.arange(1,7)*10000,(18,1)), 'radius':.2,
            'split':{'calibration':list(range(9)),'test':list(range(9,28))}}


def test_capability_forecast_does_not_see_future_transition():
    m=model(); p=run.make_plan(0,m,'exposed_v2')
    _,_,caps,_=run.catalogue(m,p,39,'range_ceiling',6)
    assert np.all(caps == 5)  # future onset40 is not known at39
    _,_,caps,_=run.catalogue(m,p,79,'range_ceiling',6)
    assert np.all(caps[:,0] == 2)  # future restoration80 is not known at79


def test_contract_uses_only_past_bandwidth(monkeypatch):
    m=model(); p=run.make_plan(0,m,'exposed_v2')
    monkeypatch.setattr(run,'contract',lambda q,r,c,b,cap:{'budget':b,'target':[cap]*5})
    a=run.references(m,p,'range_ceiling')
    p['capacities_mbps'][40:]=[.5]*80
    b=run.references(m,p,'range_ceiling')
    for t in a:
        if int(t)<=40:
            assert a[t]['floor']['budget']==b[t]['floor']['budget']


def test_only_selected_post_action_feedback_is_read(monkeypatch):
    m=model(); p=run.make_plan(0,m,'exposed_v2')
    refs={'0':{'floor':{'target':[4.]*5},'fair':{'target':[4.5]*5}}}
    original=run.select
    current={'epoch':-1,'action':None}
    def checked_select(*args):
        current['epoch']+=1
        action,info=original(*args)
        current['action']=action.copy()
        return action,info
    monkeypatch.setattr(run,'select',checked_select)
    class Guard:
        def __init__(self,value): self.value=value
        def __getitem__(self,key):
            sid,contexts,actions=key
            assert current['action'] is not None
            t=current['epoch']
            assert contexts == [m['contexts'].index((c,t%6)) for c in p['contents']]
            caps=run.catalogue(m,p,t,'range_ceiling')[2][0]
            assert np.array_equal(actions,np.minimum(current['action'],caps))
            assert sid == [m['split']['test'].index(s) for s in p['subjects']]
            return np.full(5,self.value)
    rows=run.simulate(m,Guard(39.),Guard(.9),p,'range_ceiling','fair_nobank',refs)
    assert len(rows)==600
    for t in range(120):
        block=rows[5*t:5*t+5]
        assert sum(r['bytes'] for r in block)<=block[0]['nash_bytes']
        for r in block:
            assert abs(r['buffer_before_s']+10+r['stall_s']-r['round_duration_s']-r['buffer_after_s'])<1e-8
