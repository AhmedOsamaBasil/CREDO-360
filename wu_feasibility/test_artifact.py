"""Post-outcome integrity and census tests; no changes to registered evaluation."""
import copy
import gzip
import json
import unittest
from .spec import PACKAGE, digest, verify
from .run import summarize
from .replication import differences, witness_only, verify_saved

PRIMARY = PACKAGE/'results/attempt_01'
REPLICA = PACKAGE/'results/replication_linux_v1'


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (PRIMARY/'metadata.json').exists():
            raise unittest.SkipTest('Results not yet published')
        cls.metadata = json.loads((PRIMARY/'metadata.json').read_text())
        cls.clips = [json.loads(gzip.decompress((PRIMARY/(k+'.json.gz')).read_bytes()))
                     for k in sorted(cls.metadata['clip_sha256'])]
        cls.summary = json.loads((PRIMARY/'summary.json').read_text())

    def test_method_binding(self):
        self.assertEqual(digest(verify()), self.metadata['registration_sha256'])

    def test_exact_clip_hashes(self):
        for clip in self.clips:
            self.assertEqual(digest(clip), self.metadata['clip_sha256'][clip['clip']])

    def test_summary_hash(self):
        self.assertEqual(digest(self.summary), self.metadata['summary_sha256'])

    def test_full_file_census(self):
        self.assertEqual({p.name for p in PRIMARY.iterdir()},
                         {k+'.json.gz' for k in self.metadata['clip_sha256']} | {'metadata.json', 'summary.json'})

    def test_complete_registration_and_pair_census(self):
        self.assertEqual(len(self.clips), 16)
        self.assertEqual(sum(c['eligible'] for c in self.clips), 10)
        self.assertEqual(sum(len(c['pairs']) for c in self.clips), 452)
        self.assertEqual(len({(c['clip'], p['recipient'], p['donor']) for c in self.clips for p in c['pairs']}), 452)

    def test_original_exclusions_remain(self):
        self.assertEqual({c['clip'] for c in self.clips if not c['eligible']},
                         {'e1v07', 'e1v08', 'e1v09', 'e2v02', 'e2v05', 'e2v09'})

    def test_primary_counts(self):
        lookup = {c['condition']: c['secondary_pooled_counts'] for c in self.summary['conditions']}
        self.assertEqual(lookup['free_exploration']['additional_rejections'], 10)
        self.assertEqual(lookup['free_exploration']['opportunity_promise_gaps'], 2)
        self.assertEqual(lookup['content_focused_memory_test']['additional_rejections'], 46)
        self.assertEqual(lookup['content_focused_memory_test']['opportunity_promise_gaps'], 48)

    def test_no_certified_success_inferred(self):
        for c in self.summary['clips']:
            self.assertIsNone(c['fulfilled_admission_fraction'])
            self.assertEqual(c['decisions'].get('admit', 0), 0)

    def test_independent_summary_reconstruction(self):
        self.assertEqual(summarize(self.clips), self.summary)

    def test_no_semantic_tolerance(self):
        mutated = copy.deepcopy(self.clips[0]); mutated['pairs'][0]['loss'] += 1
        self.assertFalse(witness_only(differences(self.clips[0], mutated)))

    def test_saved_platform_difference_retained(self):
        if not (REPLICA/'metadata.json').exists(): self.skipTest('Replica not yet published')
        result = verify_saved(REPLICA)
        self.assertFalse(result['exact_replay_passed'])
        self.assertEqual(result['differences'], 4)
        self.assertTrue(result['only_extremal_witness_ids_differ'])
        self.assertTrue(result['summary_exact'])


if __name__ == '__main__':
    unittest.main()
