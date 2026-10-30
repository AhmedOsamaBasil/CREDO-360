"""Synthetic integration/guard tests: no original media, poses or GPU execution."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from unittest.mock import patch
import zipfile
import numpy as np
from wu_pipeline import media, metrics
from wu_pipeline.spec import digest, verify as verify_original, RUNTIME
from . import prepare
from .spec import registration, REGISTRATION, verify
from .audit import contained, validate_labels, validate_manifest, inspect_failure


def label(unit):
    return {'native_mse': [[1.] * (60 // unit)] * 6,
        'negative_micro_mse': [[-1000000] * (60 // unit)] * 6,
        'duration_ticks': [unit * 150000] * (60 // unit),
        'independent_scalar_micro_exact': True, 'information_scope': 'offline_evaluation_only'}


def planned_clip(eligible=True):
    return {'clip': 'e1v01', 'condition': 'synthetic', 'experiment': 1, 'eligible': eligible,
            'source_ids': ['1'] if eligible else [], 'pairs': [['1', '2']] if eligible else [],
            'parent_exclusion_reasons': []}


def fixture():
    return {'plan': {'clips': [planned_clip()], 'expected': {
        'registered_clips': 1, 'eligible_clips': 1, 'directed_pairs': 1,
        'renditions': 6, 'parents': 36, 'recovery_children': 80, 'trace_label_rows': 1}}}


class RegistrationTests(unittest.TestCase):
    def test_plan_exactly_inherited(self):
        self.assertEqual(registration()['plan'], verify_original()['plan'])

    def test_registration_bound(self):
        value = registration()
        self.assertEqual(value['original_registration_sha256'], digest(verify_original()))
        self.assertEqual(len(value['boundary_evidence']), 2)
        self.assertFalse(value['real_v2_outputs_present_at_freeze'])

    def test_saved_registration(self):
        if not REGISTRATION.exists():
            self.skipTest('Registration not frozen yet')
        self.assertEqual(verify(), registration())

    def test_numeric_functions_are_original(self):
        self.assertIs(prepare.mse_map, metrics.mse_map)
        self.assertIs(prepare.aggregate_native, metrics.aggregate_native)
        self.assertIs(prepare.phase_check, media.phase_check)
        self.assertIs(prepare.sample_frames, media.sample_frames)
        self.assertIs(prepare.split_verified, media.split_verified)
        self.assertIs(prepare.describe, media.describe)

    def test_bounded_command_all_rungs(self):
        for rung in range(6):
            with self.subTest(rung=rung):
                old = media.encode_command('i', 'o', rung)
                new = prepare.bounded_command('i', 'o', rung)
                self.assertEqual(new, old[:-1] + ['-frames:v', '1800', 'o'])

    def test_no_source_access_on_wrong_activation(self):
        with patch.object(prepare, 'verify', return_value=fixture()), \
                patch.object(prepare, 'authorize_original') as original:
            with self.assertRaises(ValueError):
                prepare.authorize(Path('source'), Path('out'), 'wrong')
            original.assert_not_called()

    def test_existing_output_refused_before_sources(self):
        frozen = fixture()
        with tempfile.TemporaryDirectory() as folder, patch.object(prepare, 'verify', return_value=frozen), \
                patch.object(prepare, 'authorize_original') as original:
            with self.assertRaises(ValueError):
                prepare.authorize(Path('source'), Path(folder), digest(frozen))
            original.assert_not_called()

    def test_original_runtime_and_source_guard_retained(self):
        original = verify_original()
        frozen = {'plan': original['plan']}
        with patch.object(prepare, 'verify', return_value=frozen), \
                patch.object(prepare, 'private_new_output'), \
                patch.object(prepare, 'authorize_original', return_value=original) as guard:
            prepare.authorize(Path('source'), Path('out'), digest(frozen))
            guard.assert_called_once_with(Path('source'), Path('out'), digest(original))

    def test_plan_mutation_rejected(self):
        frozen = fixture()
        with patch.object(prepare, 'verify', return_value=frozen), patch.object(prepare, 'private_new_output'), \
                patch.object(prepare, 'authorize_original', return_value={'plan': {}}):
            with self.assertRaises(ValueError):
                prepare.authorize(Path('source'), Path('out'), digest(frozen))


class JournalTests(unittest.TestCase):
    def test_sequence_and_last(self):
        stream = io.BytesIO()
        with redirect_stdout(io.StringIO()):
            journal = prepare.Journal(stream)
            journal.emit('phase_start', clip='e1v01')
            journal.emit('encoding_start', clip='e1v01', rung=0)
        rows = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual([r['sequence'] for r in rows], [0, 1])
        self.assertEqual(journal.last, rows[-1])

    def test_private_field_refused(self):
        with self.assertRaises(ValueError):
            prepare.Journal(io.BytesIO()).emit('test', absolute_path='secret')

    def test_exclusive_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.json'
            prepare.save(path, {'original': True})
            with self.assertRaises(FileExistsError):
                prepare.save(path, {'original': False})
            self.assertTrue(json.loads(path.read_text())['original'])


class IntegrationTests(unittest.TestCase):
    def setup_fake(self, stack, source, output, fail=False):
        source.mkdir()
        (source / 'e1v01.mp4').write_bytes(b'synthetic-placeholder-not-media')
        with zipfile.ZipFile(source / 'vr-dataset.zip', 'w'):
            pass
        stack.enter_context(patch.object(prepare, 'authorize', return_value=fixture()))
        stack.enter_context(patch.object(prepare, 'load_roster', return_value={'rows': []}))
        stack.enter_context(patch.object(prepare, 'validate_archive_directory'))
        stack.enter_context(patch.object(prepare, 'phase_check', return_value={
            'samples': 60, 'different_sample_bins': [19], 'changes_primary_sampler': False}))
        stack.enter_context(patch.object(prepare, 'sample_frames', return_value='synthetic-frame-placeholder'))
        calls = stack.enter_context(patch.object(prepare, 'call', side_effect=ValueError('synthetic failure') if fail else None))
        def describe(path, seconds, root):
            return {'relative_path': path.relative_to(root).as_posix(), 'frames': seconds * 30}, [], []
        stack.enter_context(patch.object(prepare, 'describe', side_effect=describe))
        def split(path, directory, unit, total, root):
            return [{'index': i, 'relative_path': (directory / f'part_{i}.mp4').relative_to(root).as_posix()}
                    for i in range(total // unit)]
        stack.enter_context(patch.object(prepare, 'split_verified', side_effect=split))
        stack.enter_context(patch.object(prepare, 'mse_map', return_value=np.ones((60, 6, 12), dtype='<f4')))
        stack.enter_context(patch.object(prepare, 'load_selected', return_value='synthetic-pose-placeholder'))
        stack.enter_context(patch.object(prepare, 'project_selected', return_value=({'accepted': True}, None)))
        stack.enter_context(patch.object(prepare, 'aggregate_native', side_effect=lambda maps, poses, unit: label(unit)))
        return calls

    def test_full_control_flow_with_generated_stubs(self):
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack, redirect_stdout(io.StringIO()):
            source, output = Path(folder) / 'source', Path(folder) / 'output'
            calls = self.setup_fake(stack, source, output)
            report = prepare.execute(source, output, 'synthetic-activation')
            self.assertEqual(report['counts'], fixture()['plan']['expected'])
            self.assertEqual(calls.call_count, 6)
            self.assertTrue(all(c.args[0][-3:-1] == ['-frames:v', '1800'] for c in calls.call_args_list))
            self.assertTrue((output / 'e1v01/phase.json').exists())
            self.assertTrue((output / 'e1v01/r5_map.npy').exists())
            self.assertTrue((output / 'e1v01/label_1.json').exists())
            validate_manifest(report, fixture())

    def test_failure_keeps_phase_and_no_retry(self):
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack, redirect_stdout(io.StringIO()):
            source, output = Path(folder) / 'source', Path(folder) / 'output'
            calls = self.setup_fake(stack, source, output, fail=True)
            with self.assertRaises(ValueError):
                prepare.execute(source, output, 'synthetic-activation')
            calls.assert_called_once()
            report = inspect_failure(output, fixture())
            self.assertEqual(report['failure']['last_stage']['stage'], 'encoding_start')
            self.assertFalse(report['completed_confirmation'])
            self.assertTrue((output / 'e1v01/phase.json').exists())
            self.assertFalse((output / 'manifest.json').exists())

    def test_phase_failure_saved_before_encoding(self):
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack, redirect_stdout(io.StringIO()):
            source, output = Path(folder) / 'source', Path(folder) / 'output'
            calls = self.setup_fake(stack, source, output)
            stack.enter_context(patch.object(prepare, 'phase_check', side_effect=ValueError('synthetic phase failure')))
            with self.assertRaises(ValueError):
                prepare.execute(source, output, 'synthetic-activation')
            calls.assert_not_called()
            report = inspect_failure(output, fixture())
            self.assertEqual(report['failure']['last_stage']['stage'], 'phase_start')

    def test_mutated_success_scope_rejected(self):
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack, redirect_stdout(io.StringIO()):
            source, output = Path(folder) / 'source', Path(folder) / 'output'
            self.setup_fake(stack, source, output)
            report = prepare.execute(source, output, 'synthetic-activation')
            report['controller_access_to_future_labels_allowed'] = True
            with self.assertRaises(ValueError):
                validate_manifest(report, fixture())


class AuditTests(unittest.TestCase):
    def labels(self):
        return {'information_scope': 'offline_evaluation_only', 'rows': [
            {'source_id': '1', 'parent': label(10), 'child': label(2)}]}

    def test_label_fixture(self):
        validate_labels(self.labels(), ['1'])

    def test_micro_conversion(self):
        r = self.labels()
        r['rows'][0]['parent']['negative_micro_mse'][0][0] = -999999
        with self.assertRaises(ValueError):
            validate_labels(r, ['1'])

    def test_label_roster(self):
        with self.assertRaises(ValueError):
            validate_labels(self.labels(), ['2'])

    def test_nonfinite(self):
        r = self.labels()
        r['rows'][0]['parent']['native_mse'][0][0] = float('nan')
        with self.assertRaises(ValueError):
            validate_labels(r, ['1'])

    def test_floored_oracle_scope(self):
        r = self.labels()
        r['information_scope'] = 'current_controller_input'
        with self.assertRaises(ValueError):
            validate_labels(r, ['1'])

    def test_duration(self):
        r = self.labels()
        r['rows'][0]['child']['duration_ticks'][0] = 300001
        with self.assertRaises(ValueError):
            validate_labels(r, ['1'])

    def test_scalar_check_required(self):
        r = self.labels()
        r['rows'][0]['child']['independent_scalar_micro_exact'] = False
        with self.assertRaises(ValueError):
            validate_labels(r, ['1'])

    def test_unsafe_paths(self):
        for path in ('../secret', '/secret', 'C:/secret', 'a\\b', 'a/../b'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                contained(Path('root'), path)

    def test_contained_path(self):
        self.assertEqual(contained(Path('root'), 'a/b'), (Path('root') / 'a/b').resolve())


if __name__ == '__main__':
    unittest.main()
