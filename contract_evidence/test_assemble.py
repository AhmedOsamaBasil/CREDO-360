"""Constructed-fixture checks for the descriptive presentation layer."""
import copy
import unittest
from fractions import Fraction

from wu_feasibility.spec import digest
from wu_playback.reporting import summarize
from wu_playback.test_reporting import fixture as playback_fixture
from .assemble import mean_ratio, feasibility_tables, timing_tables, CONDITIONS
from .render import figure_data


def feasibility_fixture():
    clips=[]; conditions=[]; controls=[]
    for condition in CONDITIONS:
        for i in range(8):
            n=(44 if i==0 else 45) if i<5 else 0
            clip=f'{condition}:{i}'
            clips.append({'clip':clip,'condition':condition,'pairs':n,
                'primary_denominator':n,'disposition':'evaluated' if n else 'retained_metadata_exclusion',
                'no_event':0,'reference_infeasible':0,'known_trace_feasible':0,
                'opportunity_promise_gaps':0,'additional_rejections':0,
                'decisions':{'abstain':n} if n else {}})
            for mode in ('conditional_half_second','ideal'):
                controls.append({'clip':clip,'condition':condition,'execution_mode':mode,
                    'method':'certified_planner','denominator':n,'admissions':0,'fulfilled':0,'false_promises':0})
        macro={k:{'value':'0'} for k in ('admission_fraction','impossible_fraction',
            'additional_fraction','known_feasible_fraction','gap_fraction')}
        macro['abstain_fraction']={'value':'1'}
        conditions.append({'condition':condition,'equal_clip_macro':macro})
    # 224 in the first condition and 228 in the second, preserving the census.
    target=next(r for r in clips if r['condition']==CONDITIONS[1] and r['pairs'])
    target['pairs']+=4;target['primary_denominator']+=4;target['decisions']['abstain']+=4
    for row in controls:
        if row['clip']==target['clip']:row['denominator']+=4
    return {'schema':'wu-fixed-contract-feasibility-results-v1','clips':clips,
        'conditions':conditions,'policy_counts':controls,'soundness_violations':0,
        'checks':{},'control_equivalence':[],'quality_labels_previously_exposed':True}


class AssemblyTests(unittest.TestCase):
    def test_equal_clip_not_pooled(self):
        rows=[{'n':1,'d':2},{'n':0,'d':100}]
        self.assertEqual(mean_ratio(rows,'n','d'),'1/4')
        self.assertNotEqual(Fraction(mean_ratio(rows,'n','d')),Fraction(1,102))

    def test_zero_denominator_not_dropped(self):
        self.assertIsNone(mean_ratio([{'n':1,'d':2},{'n':0,'d':0}],'n','d'))

    def test_full_feasibility_census_and_undefined_admission_rate(self):
        result=feasibility_tables(feasibility_fixture())
        self.assertEqual(len(result['clips']),16)
        self.assertEqual(sum(r['pooled_episode_counts']['pairs'] for r in result['conditions']),452)
        self.assertTrue(all(r['fulfillment_fraction'] is None for r in result['controls']))

    def test_missing_clip_is_not_accepted(self):
        data=feasibility_fixture();data['clips'].pop()
        with self.assertRaises(ValueError):feasibility_tables(data)

    def test_rejection_increment_requires_nesting(self):
        data=feasibility_fixture();data['clips'][0]['additional_rejections']=1
        with self.assertRaises(ValueError):feasibility_tables(data)

    def test_changed_saved_macro_fails(self):
        data=feasibility_fixture();data['conditions'][0]['equal_clip_macro']['gap_fraction']['value']='1/10'
        with self.assertRaises(ValueError):feasibility_tables(data)

    def test_full_playback_census(self):
        audit,plan=playback_fixture();report=summarize(audit,plan)
        result=timing_tables(report,audit)
        self.assertEqual(len(result['session_comparisons']),366)
        self.assertEqual(result['main']['scheduled'],360)
        self.assertEqual(len(result['cells']),122)

    def test_playback_failure_stays_missing_not_zero(self):
        audit,plan=playback_fixture()
        audit['rows'][0]={**plan['sessions'][0],'valid':False,'status':'failed'}
        report=summarize(audit,plan);result=timing_tables(report,audit)
        self.assertIsNone(result['session_comparisons'][0]['result'])
        self.assertEqual(result['main']['scheduled'],360)
        self.assertEqual(result['main']['invalid'],1)

    def test_report_requires_exact_audit(self):
        audit,plan=playback_fixture();report=summarize(audit,plan)
        changed=copy.deepcopy(audit);changed['rows'][0]['status']='different'
        with self.assertRaises(ValueError):timing_tables(report,changed)

    def test_reordered_playback_rejected(self):
        audit,plan=playback_fixture();report=summarize(audit,plan)
        audit['rows'][0],audit['rows'][1]=audit['rows'][1],audit['rows'][0]
        report['audit_sha256']=digest(audit)
        with self.assertRaises(ValueError):timing_tables(report,audit)

    def test_figure_census_no_extreme_case_selection(self):
        audit,plan=playback_fixture();report=summarize(audit,plan)
        feasibility=feasibility_tables(feasibility_fixture())
        for i,row in enumerate(r for r in feasibility['clips'] if r['disposition']=='evaluated'):
            row['clip']=str(i)
        evidence={'schema':'recovery-contract-evidence-v1','feasibility':feasibility,
                  'timing':timing_tables(report,audit)}
        data=figure_data(evidence)
        self.assertEqual(len(data['clips']),10)
        self.assertEqual(sum(map(len,data['timing_cells'])),120)
        self.assertEqual(data['heatmap_range'],[-1,1])

    def test_figure_incomplete_cell_is_missing(self):
        audit,plan=playback_fixture()
        audit['rows'][0]={**plan['sessions'][0],'valid':False,'status':'failed'}
        report=summarize(audit,plan);feasibility=feasibility_tables(feasibility_fixture())
        for i,row in enumerate(r for r in feasibility['clips'] if r['disposition']=='evaluated'):
            row['clip']=str(i)
        data=figure_data({'schema':'recovery-contract-evidence-v1','feasibility':feasibility,
                         'timing':timing_tables(report,audit)})
        self.assertEqual(sum(c['delta'] is None for row in data['timing_cells'] for c in row),1)


if __name__=='__main__':unittest.main()
