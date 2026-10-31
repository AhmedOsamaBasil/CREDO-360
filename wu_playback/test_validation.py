"""Artifact and activation-boundary checks; no new playback session."""
import gzip
import json
import unittest
from unittest.mock import patch
from pathlib import Path
from .spec import PACKAGE, REGISTRATION, verify
from .build import OUT
from .core import player_entry, schedule
from .preflight import validate
from .synthetic_audit import inspect
from wu_feasibility.spec import digest, file_hash


class ValidationTests(unittest.TestCase):
    def test_bad_activation_before_media(self):
        with patch('wu_playback.preflight.verify',return_value={'fixed':True}):
            with self.assertRaisesRegex(ValueError,'Exact published'):
                validate(Path('must-not-open'), 'incorrect')

    def test_original_failure_retained(self):
        path=PACKAGE/'results/synthetic_01'
        if not path.exists():self.skipTest('No saved smoke yet')
        result=inspect(path,'source_metadata.json')
        self.assertEqual(result['valid'],0)
        self.assertEqual(result['rows'][0]['status'],'failed')
        self.assertEqual([r['status'] for r in result['rows'][1:]],['not_run_after_failure']*3)
        self.assertIn('ERR_NETWORK_ACCESS_DENIED',result['rows'][0]['error'])

    def test_generated_success_exact_reaudit(self):
        path=PACKAGE/'results/synthetic_02'
        if not path.exists():self.skipTest('No saved smoke yet')
        result=inspect(path,'source_metadata.json')
        self.assertEqual(result,json.loads((path/'report.json').read_text()))
        self.assertEqual(result['valid'],4);self.assertFalse(result['quality_claim'])
        self.assertEqual(sum(r['missing_tail_witnesses'] for r in result['rows']),0)

    def test_all_saved_synthetic_hashes(self):
        for name in ('synthetic_01','synthetic_02'):
            path=PACKAGE/'results'/name
            if not path.exists():self.skipTest('No saved smoke yet')
            meta=json.loads((path/'metadata.json').read_text())
            for filename,sha in meta['files'].items():self.assertEqual(file_hash(path/filename),sha)

    def test_frozen_method(self):
        if not REGISTRATION.exists():self.skipTest('Before freeze')
        value=verify();self.assertEqual(value['expected']['sessions'],366)
        self.assertFalse(value['real_wu_playback_before_freeze'])

    def test_plan_binding_and_projection(self):
        if not OUT.exists():self.skipTest('Plan not yet built')
        meta=json.loads((OUT/'metadata.json').read_text());plan=json.loads(gzip.decompress((OUT/'cases.json.gz').read_bytes()))
        delivery=json.loads((OUT/'delivery.json').read_text())
        self.assertEqual(digest(verify()),meta['registration_sha256'])
        self.assertEqual(digest(plan),meta['cases_sha256']);self.assertEqual(digest(delivery),meta['delivery_sha256'])
        self.assertEqual(schedule(plan['cases']),plan['sessions'])
        cases={c['case_id']:c for c in plan['cases']}
        self.assertEqual([player_entry(cases[s['case_id']],s) for s in plan['sessions']],delivery)

    def test_plan_roster_and_original_pairs(self):
        if not OUT.exists():self.skipTest('Plan not yet built')
        plan=json.loads(gzip.decompress((OUT/'cases.json.gz').read_bytes()))
        self.assertEqual(len(plan['roster']),16);self.assertEqual(len(plan['cases']),120)
        selected={r['clip']:r['first_pair'] for r in plan['roster'] if r['eligible']}
        self.assertEqual(len(selected),10)
        for case in plan['cases']:
            self.assertEqual(case['recipient'],selected[case['clip']]['recipient'])
            self.assertEqual(case['donor'],selected[case['clip']]['donor'])


if __name__=='__main__':unittest.main()
