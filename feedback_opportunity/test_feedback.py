import struct
import numpy as np
import pytest
from feedback_opportunity.feedback import mask,weights,HEADER,MAGIC,SIZE,unpack,reconstruct
from feedback_opportunity.frontier import Offer,dp,enumerate_paths
from multimedia_testbed.prepare_qoevave import viewport_weights


def packet(segment=0,rung=3,sequence=0,end=10):
    return HEADER.pack(MAGIC,bytes(32),segment,rung,sequence,end)+mask(0,0)*10


def test_mask_equivalence():
    for yaw in (-180,-165,-50,0,50,165,180,360):
        for pitch in (-90,-75,0,75,90):
            assert np.max(np.abs(weights(mask(yaw,pitch))-viewport_weights(yaw,pitch).ravel()))<1e-15


def test_client_wire_size(): assert len(packet())==SIZE==140


@pytest.mark.parametrize('p',[b'',packet()[:-1],packet()+b'0',packet(segment=1),packet(sequence=1),packet(end=9.9),packet(rung=6),packet(end=float('nan'))])
def test_invalid_packet(p):
    with pytest.raises(ValueError): unpack(p,'00'*32,0,0)


def test_wrong_descriptor_and_empty_mask():
    with pytest.raises(ValueError): unpack(packet(),'11'*32,0,0)
    with pytest.raises(ValueError): unpack(packet()[:50]+bytes(90),'00'*32,0,0)


def test_mean_mse_before_log_and_counterfactual():
    maps=np.ones((6,60,72),np.float32)*100
    maps[3,0:5]=10; maps[3,5:10]=1000
    r=reconstruct(packet(),maps,'00'*32,0,0)
    assert abs(r['psnr_db'][3]-10*np.log10(255**2/505))<1e-10
    assert r['reference_units']==r['quality_units'][2]


def test_future_maps_not_used_for_completed_feedback():
    maps=np.ones((6,60,72),np.float32)*100
    before=reconstruct(packet(),maps,'00'*32,0,0)
    maps[:,10:]=10000
    assert reconstruct(packet(),maps,'00'*32,0,0)==before


def test_oracle_budget_and_guard():
    base=Offer((2,2),0,0,(3000,3000),True)
    early=Offer((3,2),2,3,(3500,3000),True)
    late=Offer((4,2),5,3,(4000,3000),True)
    ps=((base,early),(base,late),(base,),(base,))
    r=enumerate_paths(ps,10,3,3)
    assert r['bounds']['strict']['gain']==5
    assert r['bounds']['exact_current_greedy']['unpaid_fraction']==.8
    assert r['bounds']['strict']['minimum_half_bytes']==3
    assert enumerate_paths(ps,10,3,4)['bounds']['quality_guard'] is None


def test_structural_bound_retains_actual_floor_loss():
    base=Offer((2,2),0,0,(3000,3000),True)
    loss=Offer((3,3),5,1,(4000,2999),False)
    r=enumerate_paths(((base,loss),(base,),(base,),(base,)),10,1,0)
    assert r['bounds']['structural']['gain']==5 and r['bounds']['strict']['gain']==0
