"""Constructed-fixture checks for the descriptive presentation layer."""
import copy
import unittest
from fractions import Fraction

from wu_feasibility.spec import digest
from wu_playback.reporting import summarize
from wu_playback.test_reporting import fixture as playback_fixture
from .assemble import mean_ratio, feasibility_tables, timing_tables, policy_bound_tables, CONDITIONS
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
    @staticmethod
    def bound_fixture():
        modes=('conditional_half_second','ideal')
        return [{'clip':'example','condition':CONDITIONS[0],'eligible':True,'resource_paths':10,
            'contexts':[{'execution_mode':mode,'adaptive_bound':{'credit_upper':2,'bellman_states':15}} for mode in modes],
            'pairs':[{'loss':loss,'modes':[{'execution_mode':mode,'adaptive_upper':2,
                'known_max':known,'known_trace_feasible':2*known>=loss} for mode in modes]}
                for loss,known in ((20,4),(40,25))]}]

    def test_existing_policy_upper_ratios_and_gap(self):
        result=policy_bound_tables(self.bound_fixture())[0]['modes'][0]
        self.assertEqual(result['positive_debt_pairs'],2)
        self.assertEqual(result['policy_upper_below_target'],2)
        self.assertEqual(result['maximum_upper_fraction'],'1/10')
        self.assertEqual(result['minimum_upper_fraction'],'1/20')
        self.assertEqual(result['opportunity_promise_gaps'],1)

    def test_target_equality_is_not_an_impossibility(self):
        rows=self.bound_fixture();rows[0]['pairs'][0]['loss']=4
        for mode in rows[0]['pairs'][0]['modes']:mode['known_trace_feasible']=True
        result=policy_bound_tables(rows)[0]['modes'][0]
        self.assertEqual(result['policy_upper_below_target'],1)
        self.assertEqual(result['maximum_upper_fraction'],'1/2')

    def test_policy_bound_context_disagreement_rejected(self):
        rows=self.bound_fixture();rows[0]['pairs'][0]['modes'][0]['adaptive_upper']=3
        with self.assertRaises(ValueError):policy_bound_tables(rows)

    def test_bound_zero_debt_and_exclusion_are_not_success(self):
        rows=self.bound_fixture();rows[0]['pairs'].append({'loss':0})
        rows.append({'clip':'excluded','condition':CONDITIONS[0],'eligible':False})
        result=policy_bound_tables(rows)
        self.assertEqual(result[0]['modes'][0]['positive_debt_pairs'],2)
        self.assertEqual(result[0]['modes'][0]['no_event_pairs'],1)
        self.assertEqual(result[1]['modes'],[])

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
