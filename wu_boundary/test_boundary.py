"""Offline endpoint and command regressions; never start a real source run."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from wu_pipeline.media import encode_command, timeline
from wu_pipeline.test_core import probe_fixture
from wu_pipeline.spec import ROOT
from .core import bounded_command, endpoint, private_new_output, PACKAGE
from .run import audit, validate, verify_saved


class BoundTests(unittest.TestCase):
    def test_only_output_frame_limit_added(self):
        for rung in range(6):
            with self.subTest(rung=rung):
                old = encode_command('input', 'output', rung)
                new = bounded_command('input', 'output', rung)
                self.assertEqual(new[:-3], old[:-1])
                self.assertEqual(new[-3:], ['-frames:v', '1800', old[-1]])

    def test_limit_is_output_side(self):
        c = bounded_command('input', 'output', 0)
        self.assertGreater(c.index('-frames:v'), c.index('-i'))
        self.assertLess(c.index('-t'), c.index('-i'))

    def test_no_overwrite(self):
        c = bounded_command('input', 'output', 0)
        self.assertIn('-n', c)
        self.assertNotIn('-y', c)

    def test_duration_validation(self):
        for value in (0, -1, True, 1.5, '60'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bounded_command('i', 'o', 0, value)

    def test_secondary_duration(self):
        self.assertEqual(bounded_command('i', 'o', 0, 10)[-2], '300')

    def test_rung_validation(self):
        with self.assertRaises(ValueError):
            bounded_command('i', 'o', 6)

    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            private_new_output(Path(folder))

    def test_repo_output_rejected(self):
        with self.assertRaises(ValueError):
            private_new_output(ROOT / 'nonexistent-private-boundary')

    def test_real_runner_unchanged(self):
        from wu_pipeline.prepare import encode_command as actual
        self.assertIs(actual, encode_command)
        self.assertNotIn('-frames:v', actual('i', 'o', 0))


class EndpointTests(unittest.TestCase):
    def test_exact_boundary(self):
        e = endpoint(probe_fixture(60))
        self.assertTrue(e['frozen_validation_pass'])
        self.assertEqual((e['packets'], e['last_pts'], e['presentation_end']), (1800, '1799/30', '60'))

    def test_extra_boundary_frame_rejected(self):
        p = probe_fixture(60)
        p['packets'].append({**p['packets'][0], 'pts': 1800, 'dts': 1798})
        p['format']['duration'] = '60.033333'
        e = endpoint(p)
        self.assertFalse(e['frozen_validation_pass'])
        self.assertEqual(e['packets_at_or_after_limit'], 1)
        self.assertEqual(e['presentation_end'], '1801/30')
        self.assertEqual(len(p['packets']), 1801)  # No silent truncation.

    def test_short_stream_not_padded(self):
        p = probe_fixture(60)
        p['packets'].pop()
        self.assertFalse(endpoint(p)['frozen_validation_pass'])

    def test_nonzero_origin(self):
        p = probe_fixture(60)
        p['streams'][0]['start_time'] = '0.04'
        self.assertFalse(endpoint(p)['frozen_validation_pass'])

    def test_gap(self):
        p = probe_fixture(60)
        p['packets'][7]['pts'] = 8
        self.assertFalse(endpoint(p)['uniform_grid'])
        self.assertFalse(endpoint(p)['frozen_validation_pass'])

    def test_duration_mismatch(self):
        p = probe_fixture(60)
        p['packets'][7]['duration'] = 2
        self.assertFalse(endpoint(p)['uniform_duration'])

    def test_container_tail_still_rejected(self):
        p = probe_fixture(60)
        p['format']['duration'] = '60.1'
        self.assertFalse(endpoint(p)['frozen_validation_pass'])

    def test_keyframes_still_required(self):
        p = probe_fixture(60)
        p['packets'][60]['flags'] = '_'
        self.assertFalse(endpoint(p)['frozen_validation_pass'])

    def test_order_invariant(self):
        p = probe_fixture(60)
        reference = endpoint(p)
        p['packets'].reverse()
        self.assertEqual(endpoint(p), reference)

    def test_no_packets(self):
        p = probe_fixture(60)
        p['packets'] = []
        with self.assertRaises(ValueError):
            endpoint(p)


class AuditGuardTests(unittest.TestCase):
    def test_incomplete_directory_refused(self):
        with tempfile.TemporaryDirectory() as folder, patch('wu_boundary.run.check_runtime'), \
                patch('wu_boundary.run.probe') as probe:
            with self.assertRaises(ValueError):
                audit(Path(folder))
            probe.assert_not_called()

    def test_unknown_report_rejected(self):
        from wu_pipeline.spec import RUNTIME
        import json
        with self.assertRaises(ValueError):
            validate({'schema': 'unknown', 'runtime': json.loads(RUNTIME.read_text())})

    def test_saved_failure(self):
        if not (PACKAGE / 'results/attempt_01/report.json').exists():
            self.skipTest('Read-only audit not yet generated')
        self.assertEqual(verify_saved('attempt_01')['schema'], 'wu-boundary-failure-v1')

    def test_saved_synthetic(self):
        if not (PACKAGE / 'results/synthetic_v1/report.json').exists():
            self.skipTest('Generated-only matrix not yet run')
        self.assertEqual(verify_saved('synthetic_v1')['schema'], 'wu-boundary-synthetic-v1')

    def test_scope_mutations_rejected(self):
        import json
        path = PACKAGE / 'results/synthetic_v1/report.json'
        if not path.exists():
            self.skipTest('Generated-only matrix not yet run')
        saved = json.loads(path.read_text())
        for key in ('wu_media_reencoded', 'quality_labels_created', 'real_runner_modified', 'all_six_rungs_exercised'):
            with self.subTest(key=key):
                r = copy.deepcopy(saved)
                r[key] = True
                with self.assertRaises(ValueError):
                    validate(r)

    def test_ledger_mutation_rejected(self):
        import json
        path = PACKAGE / 'results/attempt_01/report.json'
        if not path.exists():
            self.skipTest('Read-only audit not yet generated')
        r = json.loads(path.read_text())
        r['probe']['packets'].pop()
        with self.assertRaises(ValueError):
            validate(r)


if __name__ == '__main__':
    unittest.main()
