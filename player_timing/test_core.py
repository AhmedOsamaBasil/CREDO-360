import unittest
from player_timing.core import receipt_schedule,queue,resources,ledger,scores,tail_witness
from player_timing.audit import audit_service


class CoreTests(unittest.TestCase):
    def test_two_clients_share_cap(self):
        requests,arrivals=receipt_schedule([[150000,300000]],10)
        self.assertEqual(requests,[0]);self.assertEqual(arrivals,[[2.13,3.13]])
    def test_request_cadence(self):
        r,a=receipt_schedule([[150000,150000]]*2,2)
        self.assertAlmostEqual(r[1],2.13)
    def test_cold_conservation(self):
        e,g=queue([[1,2],[11,12]],[10,10]);self.assertEqual(e,[[11,12],[21,22]])
    def test_buffer_charged(self):
        e,g=queue([[1,2],[3,4]],[2,2],True)
        self.assertEqual(g,4);self.assertEqual(e,[[6,6],[8,8]])
    def test_buffer_rounding(self):
        e,g=queue([[1,2],[11,12]],[10,10],True);self.assertEqual(g,2)
    def test_no_buffer_deadline_shift(self):
        self.assertFalse(ledger(100,[60],[0,0],[41])['half'])
    def test_exact_deadline(self):
        self.assertTrue(ledger(100,[50],[0,0],[40])['protected_half'])
    def test_censor_not_success(self):
        self.assertFalse(ledger(100,[70],[0,0],[None])['half'])
    def test_floors_kept(self):
        x=ledger(100,[70],[0,1],[20]);self.assertTrue(x['half']);self.assertFalse(x['protected_half'])
    def test_reserve_no_refunds(self):
        x=resources([[40,60],[20,20]],[[20,20],[40,60]],[0,1],50)
        self.assertEqual(x['extra_bytes'],60);self.assertFalse(x['reserve_ok'])
    def test_cap_parent_aggregation(self):
        x=resources([[400000,400000]]*2,[[1,1]]*2,[0,0],9999999);self.assertFalse(x['cap_ok'])
    def test_invalid_inputs(self):
        for args in (([],[],True),([[0,0]],[0],False)):
            with self.assertRaises(ValueError):queue(*args)
        with self.assertRaises(ValueError):receipt_schedule([[0,2]],2)
    def test_partial_child_not_parent(self):
        case={'units':[{'parent':p} for p in range(4) for _ in range(2)],'loss':100,
            'parent_gains':[60,0,0,0],'parent_floor_violations':[0,0],
            'chunk_gains':[30,30,0,0,0,0,0,0],'chunk_floor_violations':[0,0]}
        x=scores(case,[[20,20],[41,41]]+[[60,60]]*6)
        self.assertEqual(x['original_parent_account']['credit'],0)
        self.assertEqual(x['secondary_chunk_account']['credit'],30)
    def test_tail_witness(self):
        self.assertFalse(tail_witness([],60));self.assertFalse(tail_witness([{'mediaTime':1}],60))
        self.assertTrue(tail_witness([{'mediaTime':59/30}],60))
    def test_service_duplicate_detected(self):
        with self.assertRaises(ValueError):audit_service({'transfers':[{'id':'a'},{'id':'a'}],'batches':[]})
    def test_service_early_detected(self):
        with self.assertRaises(ValueError):audit_service({'transfers':[{'id':'a','eligible':1,'request':0,'bytes':1,'completed':None}],
            'batches':[{'at':.1,'interval_start':.09,'budget':1500,'sent':{'a':1}}]})


if __name__=='__main__':unittest.main()
