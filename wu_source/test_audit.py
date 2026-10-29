import copy
import hashlib
import json
import unittest
from .acquire import canonical
from .audit import PACKAGE, bindings, validate


class PublishedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((PACKAGE/'results/source_v1/report.json').read_text())
    def reject(self,change):
        r=copy.deepcopy(self.report); change(r)
        with self.assertRaises(ValueError): validate(r)
    def test_full_report(self):
        self.assertEqual(validate(self.report),{'trace_files':864,'clock_eligible':94,'media_timing_pass':16,'ready_for_outcomes':False})
    def test_bindings(self):
        m=json.loads((PACKAGE/'results/source_v1/metadata.json').read_text())
        self.assertEqual(m['bindings'],bindings())
        self.assertEqual(m['report_sha256'],hashlib.sha256(canonical(self.report)).hexdigest())
    def test_no_ready_promotion(self): self.reject(lambda r:r.update(state='ready'))
    def test_no_pose_claim(self): self.reject(lambda r:r.update(participant_orientations_interpreted=True))
    def test_no_performance_claim(self): self.reject(lambda r:r.update(recovery_outcomes_derived=True))
    def test_no_geometry_claim(self): self.reject(lambda r:r['geometry_gate'].update(texture_wrap_sign_independently_verified=True))
    def test_no_missing_trace(self): self.reject(lambda r:r['clock_rows'].pop())
    def test_no_duplicate_trace(self): self.reject(lambda r:r['clock_rows'].__setitem__(0,r['clock_rows'][1]))
    def test_no_changed_asset(self): self.reject(lambda r:r['assets'][0].update(bytes=1))
    def test_no_invented_roster(self): self.reject(lambda r:r['clips'][0]['clock_eligible_source_ids'].append('99'))
    def test_no_clock_repair(self): self.reject(lambda r:r['posthoc_clock_diagnosis'].update(eligibility_revised=True))
    def test_no_changed_summary(self): self.reject(lambda r:r.update(clock_eligible_trace_count=864))
    def test_no_media_substitution(self): self.reject(lambda r:r['media']['records'][0].update(sha256='f'*64))
    def test_no_unreported_media_failure(self):
        self.reject(lambda r:next(m for m in r['media']['records'] if m['id']=='e2v02').update(target_timing_pass=True))


if __name__ == '__main__': unittest.main()
