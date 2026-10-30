"""Post-batch artifact checks; these do not change the frozen selection method."""
import copy
import json
import unittest

from .core import PACKAGE
from .run import METHOD,digest,method_record,validate


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory=PACKAGE/'results/metadata_v1'
        cls.original=json.loads((directory/'report.json').read_text())
        cls.metadata=json.loads((directory/'metadata.json').read_text())

    def setUp(self): self.report=copy.deepcopy(self.original)

    def reject(self):
        with self.assertRaises(ValueError): validate(self.report)

    def test_registered_method(self):
        self.assertEqual(json.loads(METHOD.read_text()),method_record())

    def test_artifact_binding(self):
        self.assertEqual(self.metadata,{'report_sha256':digest(self.report),
            'method_sha256':digest(method_record())})

    def test_complete_counts(self):
        result=validate(self.report)
        self.assertEqual((result['trace_files'],result['clock_qualified_traces'],
            result['metadata_qualified_traces'],result['qualified_clips']), (768,547,452,10))
        self.assertEqual(result['independent_target_checks'],46080)
        self.assertEqual([c['directed_pairs'] for c in result['conditions']],[216,236])

    def test_missing_row(self):
        self.report['rows'].pop(); self.reject()

    def test_duplicate_row(self):
        self.report['rows'][0]=copy.deepcopy(self.report['rows'][1]); self.reject()

    def test_source_binding(self):
        self.report['private_files_checked'][0]['sha256']='0'*64; self.reject()

    def test_method_binding(self):
        self.report['method_sha256']='0'*64; self.reject()

    def test_calibration_exclusions(self):
        self.report['calibration_exclusions'].pop(); self.reject()

    def test_scope_not_upgraded(self):
        for key in ('pose_values_interpreted','quaternion_validity_checked',
                    'quality_outcomes_derived','recovery_outcomes_derived',
                    'full_source_ready','automatic_outcome_launch','identity_disjoint'):
            with self.subTest(key=key):
                self.report=copy.deepcopy(self.original)
                self.report[key]=True; self.reject()

    def test_media_origin_not_repaired(self):
        self.report['media']['e2v02']['first_pts_seconds']=0; self.reject()

    def test_media_failure_not_removed(self):
        self.report['media']['e2v09']['qualified']=True; self.reject()

    def test_pair_roster_not_changed(self):
        self.report['clips'][0]['directed_pairs'][0][1]='49'; self.reject()

    def test_clip_census_not_changed(self):
        self.report['clips'].pop(); self.reject()

    def test_target_counts_shape(self):
        self.report['rows'][0]['clock_evidence']['crossing_counts'].pop(); self.reject()

    def test_target_counts_not_negative(self):
        self.report['rows'][0]['clock_evidence']['crossing_counts'][0]=-1; self.reject()

    def test_reason_not_removed(self):
        row=next(r for r in self.report['rows'] if r['clock_reasons'])
        row['clock_reasons']=[]; self.reject()

    def test_scalar_check_required(self):
        self.report['rows'][0]['independent_clock_check']=False; self.reject()

    def test_selected_indices_digest(self):
        row=next(r for r in self.report['rows'] if r['clock_qualified'])
        row['selected_row_indices_sha256']='invalid'; self.reject()

    def test_media_only_exclusions_counted(self):
        qualified=[r for r in self.report['rows'] if r['clock_qualified'] and not r['metadata_qualified']]
        self.assertEqual(len(qualified),95)
        self.assertEqual({r['clip'] for r in qualified},{'e2v02','e2v09'})

    def test_no_private_source_values_in_schema(self):
        expected={'clip','source_id','trace_member_sha256','metadata_error','clock_qualified',
            'clock_reasons','clock_evidence','independent_clock_check','selected_row_indices_sha256',
            'media_qualified','metadata_qualified','exclusion_reasons'}
        evidence={'rows','first_playback_seconds','maximum_playback_seconds','wall_invalid',
            'wall_backward_steps','wall_duplicate_steps','crossing_counts','unique_crossing_age_seconds'}
        for row in self.report['rows']:
            self.assertEqual(set(row),expected)
            self.assertIsNone(row['metadata_error'])
            self.assertEqual(set(row['clock_evidence']),evidence)


if __name__=='__main__': unittest.main()
