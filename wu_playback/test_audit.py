"""Synthetic event corruption and exact first-request accounting checks."""
import copy
from fractions import Fraction
import unittest
from .test_core import fixture
from .build import clip_cases
from .core import ideal, resource, scores
from .audit import audit, seconds_ticks


def example():
    case = copy.deepcopy(clip_cases(*fixture())[0])
    for unit in case['units']:
        unit['baseline_bytes'] = [100,100]
        for f in unit['files']: f['bytes'] = 100
    case['resource'] = resource(case['units'], 10000)
    timing = ideal(case['units'], False); case['ideal'] = {**timing, **scores(case,timing['end_ticks'])}
    session = {'index':0, 'case_id':case['case_id'], 'repetition':0, 'control':'none'}
    receipts=[]; segments=[[],[]]; frames=[[],[]]; events=[]; transfers=[]; reports=[]; batches=[]
    origin=7.
    for j in range(4):
        base=origin+j*11000
        batches.append({'at':j*11+.132,'interval_start':j*11+.13,'budget':300,
                        'sent':{f'{j}:0':100,f'{j}:1':100}})
        for u in (0,1):
            events.append({'type':'request','j':j,'u':u,'at':base})
            f=case['units'][j]['files'][u]
            receipts.append({'j':j,'u':u,'request':base,'headers':base+10,'receipt':base+170,'ready':base+171,'bytes':100,'sha256':f['sha256']})
            segment={'j':j,'u':u,'gateTime':0,'load':base+180,'playRequest':base+181,'playResolved':base+182,
                     'ended':base+10180,'reportReady':base+10181,'reportAck':base+10182,'duration':10.,'currentTime':10.,
                     'frameCount':1,'playbackQuality':None,'mediaEvents':[]}
            segments[u].append(segment)
            frames[u].append({'j':j,'u':u,'at':base+10179,'mediaTime':299/30,'expectedDisplayTime':base+10178,
                              'presentedFrames':1,'processingDuration':None})
            transfers.append({'id':f'{j}:{u}','request':j*11.,'eligible':j*11+.13,'bytes':100,'completed':j*11+.132})
            reports.append({'j':j,'u':u,'ended':segment['ended'],'reportReady':segment['reportReady'],'serverAt':j*11+10.2})
    raw={**session,'key':case['key'],'policy':case['policy'],'unit_seconds':10,'buffered':False,'status':'completed',
         'error':None,'pageErrors':[], 'browser':{'error':None,'receipts':receipts,'segments':segments,'frames':frames,'events':events},
         'server':{'transfers':transfers,'reports':reports,'batches':batches}}
    return raw,case,session


class AuditTests(unittest.TestCase):
    def test_valid_synthetic_trace(self):
        result=audit(*example());self.assertTrue(result['valid']);self.assertEqual(result['first_request_offset_ms'],7)

    def test_exact_request_aligned_ticks(self):
        self.assertEqual(seconds_ticks(40007,7),6000000)
        self.assertGreater(seconds_ticks(40007.000001,7),6000000)
        self.assertEqual(seconds_ticks(7.1,7),Fraction(15))

    def test_request_clock_change_detected(self):
        raw,c,s=example();raw['browser']['events'][0]['at']+=1
        with self.assertRaises(ValueError):audit(raw,c,s)

    def test_request_duplicate_detected(self):
        raw,c,s=example();raw['browser']['events'].append(raw['browser']['events'][0])
        with self.assertRaises(ValueError):audit(raw,c,s)

    def test_server_report_body_mismatch(self):
        raw,c,s=example();raw['server']['reports'][0]['ended']+=1
        with self.assertRaises(ValueError):audit(raw,c,s)

    def test_byte_identity_mismatch(self):
        raw,c,s=example();raw['browser']['receipts'][0]['bytes']+=1
        with self.assertRaises(ValueError):audit(raw,c,s)

    def test_rate_violation_detected(self):
        raw,c,s=example();raw['server']['batches'][0]['budget']=900000
        with self.assertRaises(ValueError):audit(raw,c,s)

    def test_callback_tail_not_invented(self):
        raw,c,s=example();raw['browser']['frames'][0]=[]
        for segment in raw['browser']['segments'][0]:segment['frameCount']=0
        result=audit(raw,c,s)
        self.assertEqual(result['missing_tail_witnesses'],4)
        self.assertEqual(result['request_aligned_accounts']['callback_tail']['original_parent_account']['credit'],0)

    def test_failed_session_not_success(self):
        raw,c,s=example();raw['status']='failed';raw['error']='watchdog'
        result=audit(raw,c,s);self.assertFalse(result['valid']);self.assertFalse(result['scored_as_success'])

    def test_changed_schedule_identity_rejected(self):
        raw,c,s=example();raw['repetition']=1
        with self.assertRaises(ValueError):audit(raw,c,s)


if __name__ == '__main__':unittest.main()
