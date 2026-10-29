"""Offline byte-range and catalogue tests; synthetic ZIP payloads only."""
import io
import json
import unittest
import urllib.error
import zipfile

from source_preflight.wu_probe import (
    CORRECTION, MEMBERS, RemoteDirectory, head_status, inspect_metadata,
    parse_video_metadata,
)


def document():
    header = 'VideoNo,VideoResolution,VideoDuration,FrameRate,FrameCount,Content,Category,Bitrate,VideoLink,DropboxLink\n'
    return (header + ''.join(f'{n},1920*960,2:00,30,3600,synthetic,Sport,1000,https://example.org/video,https://www.dropbox.com/s/id{n}/clip.mp4?dl=0\n'
                            for n in range(1, 10))).encode()


class Response(io.BytesIO):
    def __init__(self, data=b'', status=200, headers=None):
        super().__init__(data)
        self.status, self.headers = status, headers or {}


class Opener:
    def __init__(self, data, bad_status=False, bad_range=False, truncated=False):
        self.data, self.bad_status, self.bad_range, self.truncated = data, bad_status, bad_range, truncated
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request.get_method(), request.full_url, request.get_header('Range')))
        if request.get_method() == 'HEAD':
            return Response(headers={'Content-Length': str(len(self.data))})
        start, end = map(int, request.get_header('Range')[6:].split('-'))
        part = self.data[start:end + 1]
        return Response(part[:-1] if self.truncated else part,
            status=200 if self.bad_status else 206,
            headers={'Content-Range': 'invalid' if self.bad_range else f'bytes {start}-{end}/{len(self.data)}'})


def synthetic_zip(duplicate=False):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for member in MEMBERS:
            archive.writestr(member, document())
        archive.writestr('Formated_Data/userDemo.csv', 'PRIVATE_DEMOGRAPHICS')
        archive.writestr('Formated_Data/Experiment_1/Log/P1/video_1.csv', 'PRIVATE_POSES')
        if duplicate:
            archive.writestr(MEMBERS[0], document())
    return output.getvalue()


class RangeTests(unittest.TestCase):
    def test_exact_ranges_and_fresh_public_url(self):
        opener = Opener(b'0123456789')
        remote = RemoteDirectory(opener=opener)
        remote.seek(-3, 2)
        self.assertEqual(remote.read(), b'789')
        remote.seek(2)
        self.assertEqual(remote.read(2), b'23')
        self.assertEqual(remote.fetched, 5)
        self.assertEqual(remote.requests, 2)
        self.assertEqual(len({r[1] for r in opener.calls}), 1)

    def test_whole_body_fallback_rejected(self):
        with self.assertRaisesRegex(ValueError, 'range not honored'):
            RemoteDirectory(opener=Opener(b'abc', bad_status=True)).read(1)

    def test_wrong_content_range_rejected(self):
        with self.assertRaises(ValueError):
            RemoteDirectory(opener=Opener(b'abc', bad_range=True)).read(1)

    def test_short_response_rejected(self):
        with self.assertRaisesRegex(ValueError, 'length'):
            RemoteDirectory(opener=Opener(b'abc', truncated=True)).read(2)

    def test_bounds_and_origin(self):
        remote = RemoteDirectory(opener=Opener(b'abc'))
        for offset, origin in ((-1, 0), (4, 0), (0, 3)):
            with self.assertRaises(ValueError):
                remote.seek(offset, origin)

    def test_range_size_limit(self):
        remote = RemoteDirectory(opener=Opener(b'a' * (2 * 1024 ** 2 + 1)))
        with self.assertRaisesRegex(ValueError, 'limit'):
            remote.read()

    def test_count_limit(self):
        remote = RemoteDirectory(opener=Opener(b'a' * 40))
        for _ in range(30):
            remote.read(1)
        with self.assertRaisesRegex(ValueError, 'limit'):
            remote.read(1)

    def test_archive_directory_and_only_metadata(self):
        remote = RemoteDirectory(opener=Opener(synthetic_zip()))
        result = inspect_metadata(remote)
        self.assertEqual(len(result['records']), 18)
        self.assertEqual(len(result['metadata_documents']), 2)
        self.assertEqual(result['trace_members_opened'], 0)
        self.assertEqual(result['demographic_members_opened'], 0)
        self.assertEqual(result['video_bodies_downloaded'], 0)
        self.assertEqual(result['fresh_quality_or_recovery_outcomes'], 0)
        self.assertNotIn('PRIVATE_', json.dumps(result))


class WuMetadataTests(unittest.TestCase):
    def test_conditions_are_not_collapsed(self):
        first, second = parse_video_metadata(document(), 1), parse_video_metadata(document(), 2)
        self.assertTrue(all(r['experiment'] == 1 for r in first))
        self.assertTrue(all(r['experiment'] == 2 for r in second))

    def test_official_correction_is_explicit(self):
        second = parse_video_metadata(document(), 2)
        self.assertEqual(second[-1]['effective_stimulus_link'], CORRECTION)
        self.assertIsNotNone(second[-1]['correction_source'])
        self.assertNotEqual(second[-1]['original_stimulus_link'], CORRECTION)
        self.assertIsNone(second[-2]['correction_source'])

    def test_nominal_metadata_not_frame_mapping(self):
        rows = parse_video_metadata(document(), 1)
        self.assertEqual(rows[0]['nominal_seconds'], 120)
        self.assertIn('frame_rate_text', rows[0])
        self.assertNotIn('frame_mapping_verified', rows[0])

    def test_missing_or_duplicate_catalogue_rejected(self):
        raw = document().decode().splitlines(True)
        for rows in (raw[:-1], raw + raw[1:2]):
            with self.assertRaises(ValueError):
                parse_video_metadata(''.join(rows).encode(), 1)

    def test_bad_schema_and_non_source_links(self):
        for raw in (document().replace(b'VideoNo', b'other'), document().replace(b'www.dropbox.com', b'example.org')):
            with self.assertRaises(ValueError):
                parse_video_metadata(raw, 1)

    def test_invalid_scope(self):
        with self.assertRaises(ValueError):
            parse_video_metadata(document(), 3)

    def test_head_success_is_not_video_validation(self):
        record = parse_video_metadata(document(), 1)[0]
        result = head_status(record, Opener(b'abc'))
        self.assertEqual(result['status'], 200)
        self.assertFalse(result['media_verified'])
        self.assertFalse(result['body_downloaded'])

    def test_failed_head_retained(self):
        def fail(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 404, 'gone', {}, None)
        result = head_status(parse_video_metadata(document(), 1)[0], fail)
        self.assertEqual(result['status'], 404)
        self.assertFalse(result['media_verified'])


if __name__ == '__main__':
    unittest.main()
