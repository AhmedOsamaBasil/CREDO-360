"""Synthetic tests only: no participant file or source video is required."""
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from source_preflight.intake import (
    catalogue, clock_metadata, configuration, file_digests, inspect_archive,
    safe_name, seconds, test_info as parse_session,
)


def clock(rows=None):
    # Deliberately nonnumeric pose tokens prove these checks do not use poses.
    return io.BytesIO((''.join(f'{i / 20:.2f} {i // 2} opaque pose data here\n'
                    for i in range(1201)) if rows is None else rows).encode())


def config(clip, offset=None):
    return io.BytesIO(('[Config]\ntextureConfig=Video1\nprojectionConfig=Projection\n'
        '[Video1]\ntype=video\nnbFrame=2100\nstartOffsetInSecond='
        f'{clip["offset_seconds"] if offset is None else offset}\n'
        'pathToVideo=private-path-do-not-export\n[Projection]\ntype=Equirectangular\n').encode())


def archive_bytes(extra=(), missing=None, session_repeat=False):
    result = io.BytesIO()
    clips = catalogue()
    with tarfile.open(fileobj=result, mode='w:gz') as archive:
        entries = []
        for user in ('uid-synthetic-A', 'uid-synthetic-B'):
            for session in (('test0', 'test1') if session_repeat else ('test0',)):
                root = f'results/{user}/{session}'
                entries.append((root + '/testInfo.txt', ''.join(
                    c['id'] + ' ' + 'a' * 32 + '\n' for c in clips).encode()))
                for clip in clips:
                    entries.append((root + '/' + clip['id'] + '.ini', config(clip).read()))
                    entries.append((root + '/' + clip['id'] + '/' + clip['id'] + '_0.txt', clock().read()))
            entries.append((f'results/{user}/formAnswers.txt', b'\xffPRIVATE_SENTINEL'))
        for name, data in entries + list(extra):
            if missing and missing in name:
                continue
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    result.seek(0)
    return result


class ClockTests(unittest.TestCase):
    def test_dense_candidate_is_not_alignment(self):
        result = clock_metadata(clock())
        self.assertTrue(result['candidate_clock_eligible'])
        self.assertEqual(result['covered_samples'], 60)
        self.assertFalse(result['frame_mapping_verified'])
        self.assertFalse(result['pose_values_parsed'])

    def test_exact_tenth_accepted(self):
        rows = '0 0 a b c d\n' + ''.join(f'{i + .6:.1f} {i + 1} a b c d\n' for i in range(60))
        rows += '60 61 a b c d\n'
        self.assertTrue(clock_metadata(clock(rows))['candidate_clock_eligible'])

    def test_above_tenth_not_rounded(self):
        rows = '0 0 a b c d\n' + ''.join(f'{i + .600001:.6f} {i + 1} a b c d\n' for i in range(60))
        rows += '60 61 a b c d\n'
        self.assertFalse(clock_metadata(clock(rows))['candidate_clock_eligible'])

    def test_sparse_fails_coverage(self):
        self.assertFalse(clock_metadata(clock('0 0 a b c d\n60 1 a b c d\n'))['candidate_clock_eligible'])

    def test_short_span_fails(self):
        self.assertFalse(clock_metadata(clock('0 0 a b c d\n59.5 1 a b c d\n'))['candidate_clock_eligible'])

    def test_nonzero_first_frame_not_certified(self):
        self.assertFalse(clock_metadata(clock('0 1 a b c d\n60 2 a b c d\n'))['candidate_clock_eligible'])

    def test_absolute_clock_is_candidate_only(self):
        self.assertEqual(clock_metadata(clock('100 0 a b c d\n160 1 a b c d\n'))['span_seconds'], '60')

    def test_repeated_frame_allowed(self):
        self.assertEqual(clock_metadata(clock('0 0 a b c d\n1 0 a b c d\n'))['repeated_frame_rows'], 1)

    def test_backwards_frame_rejected(self):
        with self.assertRaisesRegex(ValueError, 'frame_reversal'):
            clock_metadata(clock('0 1 a b c d\n1 0 a b c d\n'))

    def test_repeated_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, 'timestamp_not'):
            clock_metadata(clock('0 0 a b c d\n0 1 a b c d\n'))

    def test_backwards_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, 'timestamp_not'):
            clock_metadata(clock('1 0 a b c d\n0 1 a b c d\n'))

    def test_empty_and_bad_width(self):
        for raw in ('', '\n', '0 0 a b c\n', '0 0 a b c d extra\n'):
            with self.assertRaises(ValueError):
                clock_metadata(clock(raw))

    def test_nonfinite_precision_and_range(self):
        for token in ('NaN', 'sNaN', 'Infinity', '-Infinity', '1e999999', '1e-99999', 'x', '9' * 65):
            with self.assertRaises(ValueError):
                seconds(token)

    def test_invalid_frames(self):
        for frame in ('-1', '1.0', '18446744073709551615', '1000000000'):
            with self.assertRaises(ValueError):
                clock_metadata(clock(f'0 {frame} a b c d\n'))

    def test_line_limit(self):
        with self.assertRaisesRegex(ValueError, 'line_limit'):
            clock_metadata(clock('0 0 ' + 'a' * 4100 + ' b c d\n'))


class SourceMetadataTests(unittest.TestCase):
    def test_catalogue_preserves_original_ids_offsets(self):
        self.assertEqual({c['id']: c['offset_seconds'] for c in catalogue()}, {
            'Diving-2OzlksZBTiA': 40, 'Rollercoaster-8lsB-P8nGSM': 65,
            'Timelapse-CIw8R8thnm8': 0, 'Venise-s-AJRFQuAtE': 0, 'Paris-sJxiPiAaB4k': 0})

    def test_session_checksum(self):
        self.assertEqual(parse_session(io.BytesIO(b'video ' + b'A' * 32 + b'\n')), {'video': 'a' * 32})

    def test_session_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            parse_session(io.BytesIO((b'video ' + b'a' * 32 + b'\n') * 2))

    def test_session_malformed(self):
        for raw in (b'', b'video bad\n', b'video ' + b'a' * 32 + b' extra\n'):
            with self.assertRaises(ValueError):
                parse_session(io.BytesIO(raw))

    def test_configuration_checks_offset(self):
        clip = catalogue()[0]
        self.assertEqual(configuration(config(clip), clip)['offset_seconds'], 40)
        with self.assertRaisesRegex(ValueError, 'configuration_offset'):
            configuration(config(clip, 0), clip)

    def test_configuration_does_not_emit_path(self):
        clip = catalogue()[0]
        self.assertNotIn('private-path', json.dumps(configuration(config(clip), clip)))

    def test_file_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.bin'
            path.write_bytes(b'abc')
            self.assertEqual(file_digests(path), {
                'md5': '900150983cd24fb0d6963f7d28e17f72',
                'sha256': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'})


class ArchiveTests(unittest.TestCase):
    def test_complete_synthetic_stays_blocked(self):
        result = inspect_archive(archive_bytes())
        self.assertEqual(result['trace_files'], 10)
        self.assertEqual(result['opened_metadata_files'], 22)
        self.assertEqual(result['issues'], {})
        self.assertEqual(result['state'], 'blocked_before_outcomes')
        self.assertFalse(result['source_adapter_frozen'])
        self.assertFalse(result['reuse_terms_verified'])
        self.assertFalse(result['raw_data_republishable'])
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(result))
        self.assertNotIn('uid-synthetic', json.dumps(result))

    def test_missing_clip_retained(self):
        result = inspect_archive(archive_bytes(missing=catalogue()[0]['id']))
        self.assertEqual(len(result['clips']), 5)
        self.assertEqual(result['issues']['insufficient_clip_traces'], 1)

    def test_missing_configuration_not_silenced(self):
        self.assertEqual(inspect_archive(archive_bytes(missing='.ini'))['issues']['missing_configuration'], 10)

    def test_missing_checksum_not_silenced(self):
        self.assertEqual(inspect_archive(archive_bytes(missing='testInfo'))['issues']['missing_session_checksum'], 10)

    def test_multiple_sessions_not_independent_people(self):
        self.assertEqual(inspect_archive(archive_bytes(session_repeat=True))['issues']['multiple_sessions_for_identity_clip'], 10)

    def test_unknown_run_not_substituted(self):
        c = catalogue()[0]['id']
        extra = [(f'results/uid-synthetic-A/test0/{c}/{c}_1.txt', b'NOT READ')]
        self.assertEqual(inspect_archive(archive_bytes(extra))['issues']['unexpected_trace_run'], 1)

    def test_unsafe_names_rejected(self):
        for name in ('../x', '/x', 'a/../b', 'C:/x', 'a\\b', './x', 'a//b'):
            with self.assertRaises(ValueError):
                safe_name(tarfile.TarInfo(name))

    def test_links_and_devices_rejected(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE):
            member = tarfile.TarInfo('safe-name')
            member.type = kind
            with self.assertRaises(ValueError):
                safe_name(member)

    def test_duplicate_names_rejected(self):
        extra = [('results/uid-synthetic-A/formAnswers.txt', b'not opened')]
        with self.assertRaisesRegex(ValueError, 'duplicate_or_case_alias'):
            inspect_archive(archive_bytes(extra))

    def test_case_alias_rejected(self):
        extra = [('RESULTS/UID-SYNTHETIC-A/FORMANSWERS.TXT', b'not opened')]
        with self.assertRaisesRegex(ValueError, 'duplicate_or_case_alias'):
            inspect_archive(archive_bytes(extra))


if __name__ == '__main__':
    unittest.main()
