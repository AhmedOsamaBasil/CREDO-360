"""Synthetic contract, rational duration, parser and pacing invariants."""
import unittest
import copy
import numpy as np
from duration_contract.core import (ticks,packet_timeline,playback,account,frame_record,pacing_step,oracle,TICKS,SLOT)
from duration_contract.run import scalar_bound
from metric_contract.core import path_arrays
from duration_contract.audit import audit_session
from duration_contract.run import schedule,secondary_psnr


def fixture():
    q=np.tile(np.array([-60,-50,-40,-30,-20,-10],dtype=np.int64),(6,2,1))
    costs=np.tile(np.array([100,200,300,400,500,600],dtype=np.int64),(6,1))
    return q,costs,[SLOT]*6


def synthetic_session():
    q,costs,_=fixture();record={"key":"v2:fixture:1:2","cohort":"v2","scene":"fixture",
                               "quality":np.stack([q]*4),"costs":costs}
    choices,arrivals=schedule(record,"baseline")
    media={}
    for t in range(6):media["v2","fixture",t,2]={"packets":2,"pts_ticks":[0,5000],"duration_ticks":[5000,5000],
                    "total_ticks":10000,"width":1920,"height":960,"sha256":"a"*64}
    ns=lambda tick:(tick*1000000000+TICKS//2)//TICKS
    row={"key":record["key"],"scene":"fixture","index":0,"policy":"baseline","negative_control":False,
         "status":"passed","error":None,"choices":choices,"scripted_arrivals_ticks":arrivals,
         "frames":[[],[]],"segments":[[],[]],"decoders":{}}
    for u in (0,1):
        cursor=0
        for j in range(4):
            release=ns(arrivals[j][u]);first=len(row["frames"][u])
            for i in range(2):
                ready=release+100+i;target=max(cursor,ready);duration=ns((i+1)*5000)-ns(i*5000)
                event={"segment":j+2,"frame":i,"pts_ticks":i*5000,"duration_ticks":5000,
                       "ready_ns":ready,"duration_ns":duration,"decoded_bytes":2764800,"md5":"b"*32,
                       "prior_end_ns":cursor,**pacing_step(cursor,ready,target+10)}
                row["frames"][u].append(event);cursor=event["present_ns"]+duration
            row["decoders"][f"{j}:{u}"]={"release_ns":release,"launched_ns":release,"finished_ns":release+200,
                    "returncode":0,"stderr":"","frames":2,"file_sha256":"a"*64}
            cursor+=5
            row["segments"][u].append({"first_frame_index":first,"frames":2,"duration_ticks":10000,"end_ns":cursor,"boundary_late_ns":5})
    return row,record,media


class DurationTests(unittest.TestCase):
    def test_fractional_duration_exact(self):
        self.assertEqual(ticks("299/30"),1495000)
        self.assertEqual(ticks("1/30"),5000)
        with self.assertRaises(ValueError):ticks("1/7")

    def test_first_pts_normalized(self):
        value=packet_timeline([{"pts":4,"duration":1},{"pts":3,"duration":1}],"1/30")
        self.assertEqual(value["first_pts"],3);self.assertEqual(value["pts_ticks"],[0,5000])
        self.assertEqual(value["total_ticks"],10000)

    def test_gap_duplicate_and_zero_rejected(self):
        for rows in ([{"pts":0,"duration":1},{"pts":2,"duration":1}],
                     [{"pts":0,"duration":1},{"pts":0,"duration":1}], [{"pts":0,"duration":0}]):
            with self.assertRaises(ValueError):packet_timeline(rows,"1/30")

    def test_partial_final_segment(self):
        nominal=playback([[0,0]]*4,[SLOT]*4)
        actual=playback([[0,0]]*4,[SLOT,SLOT,SLOT,ticks("299/30")])
        self.assertEqual(nominal["finish_ticks"][0]-actual["finish_ticks"][0],5000)

    def test_no_prearrival_playback(self):
        result=playback([[SLOT,2*SLOT]]*4,[SLOT]*4)
        self.assertEqual(result["startup_ticks"],[SLOT,2*SLOT])
        self.assertEqual(result["finish_ticks"],[5*SLOT,6*SLOT])

    def test_exact_deadline_included_but_late_excluded(self):
        q,costs,ds=fixture();choices=[[3,2]]*4
        included=account(q,ds,choices,[[40*TICKS,0]]*4)
        excluded=account(q,ds,choices,[[40*TICKS+1,0]]*4)
        self.assertEqual(included["deadline_unpaid"],0);self.assertEqual(excluded["deadline_credit"],0)

    def test_longer_wall_wait_never_earns_credit(self):
        q,costs,ds=fixture();choices=[[3,2]]*4
        a=account(q,ds,choices,[[1,1]]*4);b=account(q,ds,choices,[[999*TICKS,1]]*4)
        self.assertEqual(a["eventual_credit"],b["eventual_credit"])
        self.assertEqual(b["deadline_credit"],0)

    def test_actual_duration_weights_credit(self):
        q,costs,ds=fixture();choices=[[2,2],[2,2],[2,2],[3,2]]
        a=account(q,ds,choices,[[0,0]]*4);ds[-1]-=5000
        b=account(q,ds,choices,[[0,0]]*4)
        self.assertEqual(a["deadline_credit"]-b["deadline_credit"],50000)

    def test_protected_target_rejects_donor_loss(self):
        q,costs,ds=fixture();choices=[[3,1]]*4
        r=account(q,ds,choices,[[0,0]]*4)
        self.assertTrue(r["half_by_deadline"]);self.assertFalse(r["protected_half_by_deadline"])

    def test_zero_debt_not_success(self):
        q,costs,ds=fixture();q[:2,0,0]=q[:2,0,2]
        self.assertIsNone(account(q,ds,[[3,2]]*4,[[0,0]]*4)["half_by_deadline"])

    def test_framehash_parser(self):
        r=frame_record("0, 3, 3, 1, 2764800, "+"a"*32)
        self.assertEqual(r["pts"],3);self.assertEqual(r["duration"],1)
        for line in ("bad", "1,0,0,1,4,"+"a"*32,"0,0,0,0,4,"+"a"*32,"0,0,0,1,4,x"):
            with self.assertRaises(ValueError):frame_record(line)

    def test_pacing_conservation(self):
        r=pacing_step(10,15,18)
        self.assertEqual(r,{"target_ns":15,"present_ns":18,"decoder_wait_ns":5,"pacing_late_ns":3})
        self.assertEqual(10+r["decoder_wait_ns"]+r["pacing_late_ns"],r["present_ns"])

    def test_prefetched_frame_cannot_accelerate(self):
        self.assertEqual(pacing_step(100,50,90)["present_ns"],100)

    def test_independent_actual_duration_oracle(self):
        q,costs,ds=fixture();ds[-1]-=5000
        arrays=path_arrays(costs,4,200)
        out=oracle(q,costs,ds,arrays["choices"],arrays["cost"])
        gains,budgets,count=scalar_bound(q,costs,ds,200)
        self.assertEqual(out["strict_paths"],count)
        for n in gains:
            self.assertEqual(out[n]["gain"],gains[n]);self.assertEqual(out[n]["half_min_extra_bytes"],budgets[n])

    def test_independent_event_auditor_accepts_conserved_fixture(self):
        row,r,media=synthetic_session()
        result=audit_session(row,r,media)
        self.assertEqual(result["frames_checked"],16)
        self.assertEqual(result["deadline_credit"],0)

    def test_event_auditor_rejects_early_presentation(self):
        row,r,media=synthetic_session();row["frames"][0][0]["present_ns"]=0
        with self.assertRaises(ValueError):audit_session(row,r,media)

    def test_event_auditor_rejects_incomplete_frame_dwell(self):
        row,r,media=synthetic_session();row["segments"][0][0]["end_ns"]-=100
        with self.assertRaises(ValueError):audit_session(row,r,media)

    def test_event_auditor_rejects_wrong_file_identity(self):
        row,r,media=synthetic_session();row["decoders"]["0:0"]["file_sha256"]="0"*64
        with self.assertRaises(ValueError):audit_session(row,r,media)

    def test_event_auditor_rejects_missing_frame(self):
        row,r,media=synthetic_session();row["frames"][0][1]["frame"]=0
        with self.assertRaises(ValueError):audit_session(row,r,media)

    def test_secondary_psnr_keeps_user_and_rung_axes(self):
        quality=np.zeros((4,6,2,6),dtype=np.int64)
        quality[2,:,0,4]=40000000;quality[2,:,1,5]=50000000
        self.assertEqual(secondary_psnr(quality,[SLOT]*6,[[4,5]]*4),[40.,50.])
        with self.assertRaises(ValueError):secondary_psnr(quality[2],[SLOT]*6,[[4,5]]*4)


if __name__=="__main__":unittest.main()
