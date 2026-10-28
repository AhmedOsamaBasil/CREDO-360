import gzip
import json
import unittest
import numpy as np
from metric_contract.data import ROOT
from admission_contract.diagnose import independent_score,SOURCE


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.q=np.zeros((4,6,2,6),dtype=np.int64)
        self.q[3]=-100;self.q[3,:2,0,0]=-200
        self.r={'quality':self.q,'costs':np.ones((6,6),dtype=np.int64)*100,'reserve':800}
        self.ds=[1500000]*6

    def test_baseline_promise_is_not_success(self):
        score,spent=independent_score(self.r,self.ds,[[2,2]]*4,75000)
        self.assertFalse(score['protected_half_by_deadline']);self.assertEqual(spent,0)

    def test_resource_cap_violation_rejected(self):
        self.r['costs'][2,3]=1500001
        with self.assertRaisesRegex(ValueError,'Cap'):independent_score(self.r,self.ds,[[3,2]]*4,75000)

    def test_nonrefilling_reserve_violation_rejected(self):
        self.r['costs'][2,3]=1000;self.r['reserve']=899
        with self.assertRaisesRegex(ValueError,'Reserve'):independent_score(self.r,self.ds,[[3,2]]*4,75000)


@unittest.skipUnless(SOURCE.exists(),'Published batch unavailable')
class ArtifactTests(unittest.TestCase):
    def test_three_way_counts_and_undefined_precision(self):
        with gzip.open(SOURCE,'rt') as f:r=json.load(f)
        self.assertEqual(len(r['rows']),3192)
        self.assertEqual(r['checks']['scalar_certificate_queries'],336)
        for row in r['summary']:
            self.assertEqual(sum(row['status_counts'].values()),row['episodes'])
            if row['admitted']==0:self.assertIsNone(row['precision'])

    def test_unbounded_execution_never_admits(self):
        with gzip.open(SOURCE,'rt') as f:r=json.load(f)
        rows=[x for x in r['rows'] if x['eta']=='unbounded']
        self.assertEqual(len(rows),168);self.assertFalse(any(x['admitted'] for x in rows))

    def test_forecast_failures_are_retained(self):
        with gzip.open(SOURCE,'rt') as f:r=json.load(f)
        failed=[x for x in r['rows'] if x['method']=='point_planner' and x['eta']=='half_second' and x['admitted'] and not x['protected_success']]
        self.assertEqual(len(failed),1)
        self.assertEqual(failed[0]['key'],'v2:River01:12:11')


if __name__=='__main__':unittest.main()
