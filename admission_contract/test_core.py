import unittest
import numpy as np
from metric_contract.core import path_arrays,TICKS
from duration_contract.core import account
from admission_contract.core import spatial_bounds,certificate,independent,entry_inputs,forecast,clocks,path_stats,ETA,control_path


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.maps=np.ones((6,60,72))*100
        self.maps[3]=90
        self.costs=np.ones((6,6),dtype=np.int64)*10000
        self.ds=[10*TICKS]*6;self.reserve=80000
        self.arrays=path_arrays(self.costs,4,self.reserve)
        self.lower,self.upper=spatial_bounds(self.maps)

    def test_nonvacuous_admission(self):
        c=certificate(self.lower,self.upper,self.costs,self.arrays,self.ds,30_000_000*TICKS)
        self.assertEqual(c['status'],'admit');self.assertGreater(c['certified_credit'],0)

    def test_impossible_even_with_all_four_segments(self):
        c=certificate(self.lower,self.upper,self.costs,self.arrays,self.ds,1_000_000_000*TICKS)
        self.assertEqual(c['status'],'impossible')

    def test_insufficient_certificate_is_not_impossibility(self):
        c=certificate(self.lower,self.upper,self.costs,self.arrays,self.ds,700_000_000*TICKS)
        self.assertEqual(c['status'],'abstain')

    def test_unbounded_execution_cannot_admit(self):
        c=certificate(self.lower,self.upper,self.costs,self.arrays,self.ds,30_000_000*TICKS,None)
        self.assertEqual(c['status'],'abstain');self.assertIsNone(c['path'])

    def test_zero_debt_not_admission(self):
        self.assertEqual(certificate(self.lower,self.upper,self.costs,self.arrays,self.ds,0)['status'],'not_applicable')

    def test_scalar_certificate_matches_vector(self):
        loss=30_000_000*TICKS
        c=certificate(self.lower,self.upper,self.costs,self.arrays,self.ds,loss)
        s=independent(self.lower,self.upper,self.costs,self.ds,self.reserve,loss,ETA)
        self.assertEqual((c['lower_max_credit'],c['upper_credit'],c['lower_safe_paths'],c['extra_bytes']),
                         (s['lower_max'],s['upper_max'],s['safe_paths'],s['minimum_cost']))

    def test_quality_floor_blocks_a_favorable_mean(self):
        self.maps[3,:,0]=101
        low,up=spatial_bounds(self.maps)
        c=certificate(low,up,self.costs,self.arrays,self.ds,30_000_000*TICKS)
        self.assertEqual(c['status'],'abstain')
        self.assertLess(low[2,3],0)

    def test_convex_envelope_contains_weighted_differences(self):
        rng=np.random.default_rng(413)
        maps=rng.uniform(1,100,(6,60,72));lo,hi=spatial_bounds(maps)
        w=rng.uniform(0,1,(60,72));w/=w.sum(axis=1,keepdims=True)
        e=np.sum(maps*w,axis=2).reshape(6,6,10).mean(axis=2).T
        rounded=np.floor(e*1e6+.5).astype(np.int64)
        difference=rounded[:,2:3]-rounded
        self.assertTrue(((lo<=difference)&(difference<=hi)).all())

    def test_reference_is_exact_despite_outward_guard(self):
        self.assertTrue((self.lower[:,2]==0).all());self.assertTrue((self.upper[:,2]==0).all())

    def test_future_labels_cannot_change_entry_or_forecast(self):
        q=np.ones((4,6,2,6),dtype=np.int64)*10_000_000;q[3]*=-1
        r={'quality':q};before=entry_inputs(r,self.ds);prediction=forecast(self.maps,before['past_reference_mse'])
        q[:,2:]*=1000
        after=entry_inputs(r,self.ds)
        self.assertEqual(before,after);np.testing.assert_equal(prediction,forecast(self.maps,after['past_reference_mse']))

    def test_only_completed_past_reference_is_accepted(self):
        with self.assertRaises(ValueError):forecast(self.maps,np.ones((6,2)))

    def test_execution_allowance_cannot_increase_credit(self):
        zero=clocks(self.costs,self.arrays['choices'],self.ds,0)
        delayed=clocks(self.costs,self.arrays['choices'],self.ds,ETA)
        self.assertTrue((delayed>=zero).all())
        _,a=path_stats(self.lower,self.arrays['choices'],zero,self.ds)
        _,b=path_stats(self.lower,self.arrays['choices'],delayed,self.ds)
        self.assertTrue((b<=a).all())

    def test_late_or_partial_segment_earns_nothing(self):
        paths=np.array([[[3,2]]*4]);ends=np.ones((1,4,2),dtype=np.int64)*40*TICKS
        _,on=path_stats(self.lower,paths,ends,self.ds)
        _,late=path_stats(self.lower,paths,ends+1,self.ds)
        self.assertGreater(on[0],0);self.assertEqual(late[0],0)

    def test_point_controls_respect_budget(self):
        predicted=forecast(self.maps,np.ones((2,2))*100_000_000)
        for name in ('cost_greedy','rolling_nash','maxmin'):
            path=control_path(name,predicted,self.costs,self.ds,0,[[30_000_000]*2]*2,30_000_000*TICKS,ETA)
            self.assertEqual(path.shape,(4,2))
            self.assertTrue(((path>=2)&(path<=5)).all())

    def test_invalid_maps_and_negative_timing_rejected(self):
        with self.assertRaises(ValueError):spatial_bounds(np.ones((6,60,71)))
        with self.assertRaises(ValueError):clocks(self.costs,self.arrays['choices'],self.ds,-1)

    def test_favorable_point_forecast_can_make_false_promise(self):
        self.maps[3,:,0]=101
        low,up=spatial_bounds(self.maps);loss=30_000_000*TICKS
        q=forecast(self.maps,np.ones((2,2))*100_000_000)
        path=np.array([[[3,2]]*4]);end=clocks(self.costs,path,self.ds,ETA)
        safe,gain=path_stats(q-q[:,:,2:3],path,end,self.ds)
        self.assertTrue(safe[0] and 2*gain[0]>=loss)
        actual=-np.ones((6,2,6),dtype=np.int64)*100_000_000
        actual[:2,0,0]=-101_500_000;actual[2:,0,3]=-101_000_000
        score=account(actual,self.ds,path[0].tolist(),end[0].tolist())
        self.assertFalse(score['protected_half_by_deadline'])
        self.assertEqual(certificate(low,up,self.costs,self.arrays,self.ds,loss)['status'],'abstain')

    def test_later_savings_do_not_refund_reserve(self):
        costs=self.costs.copy();costs[2,3]=20000;costs[3,3]=1
        arrays=path_arrays(costs,4,9999)
        path=np.array([[3,2],[3,2],[2,2],[2,2]])
        self.assertFalse(np.any(np.all(arrays['choices']==path,axis=(1,2))))


if __name__=='__main__':unittest.main()
