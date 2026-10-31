"""Pure reporting checks; no measured campaign data are read."""
import copy
from fractions import Fraction
import unittest
from .reporting import fraction_stats, group_summary, summarize
from .test_audit import example
from .audit import audit
from .core import schedule


def fixture():
    row=audit(*example());cases=[]
    for clip in range(10):
        for policy in ('cost_greedy','rolling_nash','maxmin'):
            for unit in (10,2):
                for buffered in (False,True):
                    cases.append({'case_id':f'{clip}:{policy}:{unit}:{buffered}','clip':str(clip),
                        'condition':'a' if clip<5 else 'b','policy':policy,'unit_seconds':unit,'buffered':buffered})
    plan={'cases':cases,'sessions':schedule(cases)}
    rows=[{**copy.deepcopy(row),**session} for session in plan['sessions']]
    return {'rows':rows},plan


class ReportingTests(unittest.TestCase):
    def test_exact_signed_statistics(self):
        r=fraction_stats(['-1/3','0','1/2']);self.assertEqual(r['mean'],'1/18')
        self.assertEqual((r['negative'],r['zero'],r['positive']),(1,1,1))

    def test_empty_not_zero(self):
        self.assertIsNone(fraction_stats([])['mean'])

    def test_complete_plan(self):
        a,p=fixture();r=summarize(a,p)
        self.assertEqual(r['main']['scheduled'],360);self.assertEqual(len(r['by_cell']),122)
        self.assertEqual(len(r['equal_clip_macro']),24)
        self.assertTrue(all(x['complete_clips']==5 for x in r['equal_clip_macro']))

    def test_failed_row_retained_and_macro_missing(self):
        a,p=fixture();a['rows'][0]={**p['sessions'][0],'valid':False,'status':'failed','error':'watchdog'}
        r=summarize(a,p);self.assertEqual(r['all_scheduled']['invalid'],1)
        self.assertEqual(sum(x['incomplete_macro_not_estimated'] for x in r['equal_clip_macro']),1)
        self.assertEqual(r['main']['scheduled'],360)

    def test_missing_row_rejected(self):
        a,p=fixture();a['rows'].pop()
        with self.assertRaises(ValueError):summarize(a,p)

    def test_reordering_rejected(self):
        a,p=fixture();a['rows'][0],a['rows'][1]=a['rows'][1],a['rows'][0]
        with self.assertRaises(ValueError):summarize(a,p)

    def test_large_integer_not_float(self):
        row=audit(*example());row['parent_credit_minus_ideal']=2**80+1
        r=group_summary([row]);self.assertEqual(Fraction(r['parent_credit_minus_ideal']['mean']),2**80+1)

    def test_cap_failure_not_success(self):
        row=audit(*example());row['resource']['cap_ok']=False
        row['request_aligned_accounts']['ended']['original_parent_account']['resource_protected_half']=False
        r=group_summary([row]);self.assertEqual(r['resource_cap_failures'],1)
        self.assertEqual(r['observed_resource_protected_half'],0)


if __name__=='__main__':unittest.main()
