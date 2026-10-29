"""Offline checks for recorded access metadata and claim boundaries."""
import copy
import unittest

from source_preflight.audit import PACKAGE, OUT, digest, read, report, summarize


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.access = read(PACKAGE / 'results/access_v1/wu_metadata.json')
        self.review = read(PACKAGE / 'source_review.json')

    def test_all_links_reported_but_not_media_verified(self):
        result = summarize(self.access, self.review)
        self.assertEqual(result['successful_head_responses'], 18)
        self.assertEqual(result['condition_counts'], {'1': 9, '2': 9})
        self.assertFalse(result['source_adapter_frozen'])
        self.assertEqual(result['new_empirical_outcomes'], 0)

    def test_missing_link_rejected(self):
        self.access['video_head_checks'].pop()
        with self.assertRaises(ValueError):
            summarize(self.access, self.review)

    def test_failed_head_not_silenced(self):
        self.access['video_head_checks'][0]['status'] = 404
        self.assertEqual(summarize(self.access, self.review)['successful_head_responses'], 17)

    def test_promotion_rejected(self):
        for key in ('body_downloaded', 'media_verified'):
            access = copy.deepcopy(self.access)
            access['video_head_checks'][0][key] = True
            with self.assertRaises(ValueError):
                summarize(access, self.review)

    def test_outcome_access_rejected(self):
        self.access['trace_members_opened'] = 1
        with self.assertRaises(ValueError):
            summarize(self.access, self.review)

    def test_wrong_video9_correction_rejected(self):
        self.access['records'][-1]['effective_stimulus_link'] = self.access['records'][-2]['effective_stimulus_link']
        with self.assertRaises(ValueError):
            summarize(self.access, self.review)

    def test_saved_report_replays(self):
        if not (OUT / 'metadata.json').exists():
            self.skipTest('Assessment not yet frozen')
        result = report()
        self.assertEqual(result, read(OUT / 'report.json'))
        self.assertEqual(digest(result), read(OUT / 'metadata.json')['sha256'])


if __name__ == '__main__':
    unittest.main()
