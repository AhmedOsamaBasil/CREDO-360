"""Post-batch integrity and failure-accounting tests, not selection changes."""
import copy
import json
import unittest
from .core import load_roster,summarize,digest,PACKAGE
from .run import DEFAULT,METHOD,method_record,validate,read_artifact
from .replication import compare


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=read_artifact(DEFAULT); cls.parent=load_roster()

    def setUp(self): self.report=copy.deepcopy(self.original)
    def reject(self):
        with self.assertRaises(ValueError): validate(self.report)
    def valid_row(self): return next(r for r in self.report['rows'] if r['pose_validated'])

    def test_frozen_method(self): self.assertEqual(json.loads(METHOD.read_text()),method_record())
    def test_complete_result(self):
        result=validate(self.report)
        self.assertEqual((result['registered_traces'],result['accessed_pose_traces'],
            result['validated_pose_traces'],result['selected_samples_checked']),(768,452,452,27120))
        self.assertEqual(result['pose_failed_traces'],0)
        self.assertEqual([c['usable_pairs'] for c in result['conditions']],[216,236])

    def test_all_parent_exclusions_retained(self):
        excluded=[r for r in self.report['rows'] if not r['metadata_qualified']]
        self.assertEqual(len(excluded),316)
        self.assertTrue(all(not r['pose_accessed'] and r['quaternion'] is None for r in excluded))

    def test_scope_flags(self):
        for key in self.report['scope']:
            with self.subTest(key=key):
                self.report=copy.deepcopy(self.original)
                self.report['scope'][key]=not self.report['scope'][key]; self.reject()

    def test_missing_row(self): self.report['rows'].pop(); self.reject()
    def test_changed_order(self):
        self.report['rows'][0],self.report['rows'][1]=self.report['rows'][1],self.report['rows'][0]; self.reject()
    def test_method_digest(self): self.report['method_sha256']='0'*64; self.reject()
    def test_parent_digest(self): self.report['parent_roster_sha256']='0'*64; self.reject()
    def test_source_hash(self):
        self.report['private_files_checked'][0]['sha256']='0'*64; self.reject()
    def test_selected_index_hash(self):
        self.valid_row()['selected_row_indices_sha256']='0'*64; self.reject()
    def test_raw_pose_field_rejected(self):
        self.valid_row()['yaw_pitch']=[[0,0]]; self.reject()
    def test_unqualified_access_rejected(self):
        row=next(r for r in self.report['rows'] if not r['metadata_qualified'])
        row['pose_accessed']=True; self.reject()
    def test_removed_exclusion(self):
        row=next(r for r in self.report['rows'] if r['parent_exclusion_reasons'])
        row['parent_exclusion_reasons']=[]; self.reject()
    def test_excess_norm_error(self):
        self.valid_row()['quaternion']['maximum_valid_selected_norm_error']=.011; self.reject()
    def test_nonfinite_error(self):
        self.valid_row()['quaternion']['maximum_valid_selected_norm_error']=float('nan'); self.reject()
    def test_partial_sample_count(self):
        self.valid_row()['quaternion']['selected_samples']=59; self.reject()
    def test_invalid_reason_count(self):
        self.valid_row()['quaternion']['invalid_reason_counts']['zero_quaternion']=-1; self.reject()
    def test_geometry_count(self):
        self.valid_row()['geometry']['samples_checked']=59; self.reject()
    def test_geometry_error(self):
        self.valid_row()['geometry']['maximum_circular_yaw_error_degrees']=1e-5; self.reject()
    def test_mask_membership(self):
        self.valid_row()['geometry']['tile_membership_exact']=False; self.reject()
    def test_missing_pair(self):
        self.report['clips'][0]['candidate_pairs'].pop(); self.reject()
    def test_replacement_pair(self):
        self.report['clips'][0]['candidate_pairs'][0]['donor']='49'; self.reject()

    def test_synthetic_failure_keeps_all_original_pairs(self):
        row=self.valid_row(); row['pose_validated']=False
        row['pose_failure_reasons']=['zero_quaternion']; row['geometry']=None
        row['quaternion']['invalid_samples']=1; row['quaternion']['invalid_reason_counts']['zero_quaternion']=1
        self.report['clips']=summarize(self.parent,self.report['rows'])
        result=validate(self.report)
        self.assertEqual(result['pose_failed_traces'],1)
        self.assertEqual(sum(c['candidate_pairs'] for c in result['conditions']),452)
        self.assertEqual(sum(c['usable_pairs'] for c in result['conditions']),450)

    def test_platform_report_and_comparison(self):
        linux=read_artifact(PACKAGE/'results/linux_v1')
        expected={'schema':'wu-pose-platform-comparison-v1','method_sha256':digest(method_record()),
            'comparison':compare(self.report,linux)}
        self.assertEqual(json.loads((PACKAGE/'results/replication_v1/report.json').read_text()),expected)


if __name__=='__main__': unittest.main()
