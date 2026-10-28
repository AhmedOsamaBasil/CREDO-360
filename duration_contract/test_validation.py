"""Post-batch validation of the frozen engineering contract and artifact coverage."""
import gzip
import json
import unittest
import numpy as np
from metric_contract.data import ROOT
from duration_contract.diagnose import resource_ledger, REPLAY, MEASURED


class ResourceTests(unittest.TestCase):
    def test_savings_do_not_refund(self):
        costs = np.ones((6,6), dtype=int) * 100
        costs[2,3] = costs[4,3] = 200
        costs[3,3] = 1
        with self.assertRaisesRegex(ValueError, "reserve"):
            resource_ledger({"costs": costs, "reserve": 199}, [[3,2], [3,2], [3,2], [2,2]])

    def test_round_cap_and_structural_floor(self):
        record = {"costs": np.ones((6,6), dtype=int) * 800001, "reserve": 10000000}
        with self.assertRaisesRegex(ValueError, "cap"):
            resource_ledger(record, [[2,2]] * 4)
        with self.assertRaisesRegex(ValueError, "rung"):
            resource_ledger(record, [[1,2]] * 4)


@unittest.skipUnless(REPLAY.exists() and MEASURED.exists(), "Published batch not yet available")
class ArtifactTests(unittest.TestCase):
    def test_full_batch_and_negative_control(self):
        measured = json.loads(MEASURED.read_text())
        self.assertEqual(measured["sessions"], 19)
        self.assertEqual(measured["frames_checked"], 45594)
        self.assertEqual(sum(r["negative_control"] for r in measured["rows"]), 1)
        control = next(r for r in measured["rows"] if r["negative_control"])
        self.assertEqual(control["deadline_credit"], 0)
        self.assertEqual(control["recipient_completed_segments_by_deadline"], 0)

    def test_replay_coverage_and_protection(self):
        with gzip.open(REPLAY, "rt") as f:
            replay = json.load(f)
        self.assertEqual(len(replay["rows"]), 3024)
        self.assertEqual(replay["checks"], {"nominal_score_parity": 2688, "scalar_bound_queries": 336})
        for r in replay["rows"]:
            self.assertEqual(r["protected_half_by_deadline"], bool(r["half_by_deadline"] and
                             not r["recipient_floor_violations"] and not r["donor_floor_violations"]))
            self.assertGreaterEqual(r["deadline_unpaid"], r["eventual_unpaid"])

    def test_partial_final_is_only_media_difference(self):
        with gzip.open(ROOT / "duration_contract/data/media_v1/timelines.json.gz", "rt") as f:
            rows = json.load(f)["rows"]
        self.assertEqual(len(rows), 216)
        short = [r for r in rows if r["total_ticks"] != 1500000]
        self.assertEqual(len(short), 6)
        self.assertTrue(all(r["scene"] == "River01" and r["segment"] == 5 and
                            r["packets"] == 299 and r["total_ticks"] == 1495000 for r in short))


if __name__ == "__main__":
    unittest.main()
