"""Frozen plan and synthetic-artifact checks; no runtime/media execution."""
import copy
import json
import unittest
from unittest.mock import patch
from .spec import PACKAGE,REGISTRATION,registration,verify,bindings,digest
from .synthetic import verify_report


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen=verify()
        cls.report=json.loads((PACKAGE/'results/synthetic_v1/report.json').read_text())

    def test_registration_reproduces(self): self.assertEqual(json.loads(REGISTRATION.read_text()),registration())
    def test_no_real_outcomes(self): self.assertFalse(self.frozen['fresh_outcomes_present'])
    def test_all_registered_clips(self): self.assertEqual(len(self.frozen['plan']['clips']),16)
    def test_condition_counts(self):
        clips=self.frozen['plan']['clips']
        self.assertEqual([sum(c['eligible'] for c in clips if c['experiment']==e) for e in (1,2)],[5,5])
    def test_original_pairs(self):
        clips=self.frozen['plan']['clips']
        self.assertEqual([sum(len(c['pairs']) for c in clips if c['experiment']==e) for e in (1,2)],[216,236])
    def test_asset_census(self): self.assertEqual(len(self.frozen['plan']['private_files_checked']),17)
    def test_planned_media_counts(self):
        e=self.frozen['plan']['expected']
        self.assertEqual((e['renditions'],e['parents'],e['recovery_children']),(60,360,800))
    def test_smoke_binding(self):
        metadata=json.loads((PACKAGE/'results/synthetic_v1/metadata.json').read_text())
        self.assertEqual(metadata,{'report_sha256':digest(self.report),'bindings':bindings()})
    def test_smoke_has_no_real_source(self): self.assertTrue(verify_report(self.report)['synthetic_only'])
    def test_phase_difference_retained(self):
        data=verify_report(self.report)['phase_different_bins']
        self.assertEqual(data['30000/1001'],[19,23,24,29,50,52,54,55,56])
        self.assertTrue(all(not data[r] for r in ('16','25','30')))
    def test_container_overhead_not_erased(self):
        self.assertGreater(sum(c['bytes'] for c in self.report['children']),self.report['parent']['bytes'])
        self.assertGreater(self.report['parent']['bytes'],self.report['parent']['payload_bytes'])
    def test_single_rung_smoke_scope(self):
        self.assertEqual(self.report['encoded_rungs_exercised'],[2])
        self.assertFalse(self.report['full_sixty_second_six_rung_campaign_executed'])
    def test_forbidden_scope_flags(self):
        for key in ('wu_media_accessed','wu_poses_accessed','fresh_research_outcomes','full_sixty_second_six_rung_campaign_executed'):
            with self.subTest(key=key):
                r=copy.deepcopy(self.report);r[key]=True
                with self.assertRaises(ValueError):verify_report(r)
    def test_wrong_child_count(self):
        r=copy.deepcopy(self.report);r['children'].pop()
        with self.assertRaises(ValueError):verify_report(r)
    def test_missing_phase_condition(self):
        r=copy.deepcopy(self.report);r['phase_checks'].pop()
        with self.assertRaises(ValueError):verify_report(r)
    def test_phase_not_used_to_change_target(self):
        r=copy.deepcopy(self.report);r['phase_checks'][0]['changes_primary_sampler']=True
        with self.assertRaises(ValueError):verify_report(r)


if __name__=='__main__':unittest.main()
