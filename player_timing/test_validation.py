"""Independent accounting, raw-event corruption, and published-artifact tests."""
from copy import deepcopy
import gzip
import json
import unittest

from player_timing.audit import RAW, audit_service, audit_session
from player_timing.core import scores
from player_timing.diagnose import check_scalar, raw_crosschecks, scalar_score
from player_timing.prior_art_check import check as nash_counterexample
from player_timing.inspect import inspect_session
from player_timing.replay import DATA, OUT, provenance


def read(path):
    with gzip.open(path, 'rt') as stream:
        return json.load(stream)


class IndependentLedgerTests(unittest.TestCase):
    def setUp(self):
        self.case = {
            'units': [{'parent': p} for p in range(4) for _ in range(2)],
            'loss': 100, 'parent_gains': [60, 0, 0, 0],
            'chunk_gains': [30, 30, 0, 0, 0, 0, 0, 0],
            'parent_floor_violations': [0, 0], 'chunk_floor_violations': [0, 0],
        }

    def test_partial_parent_not_credited(self):
        ends = [20, 41] + [60] * 6
        self.assertEqual(scalar_score(self.case, ends)['credit'], 0)
        self.assertEqual(scalar_score(self.case, ends, True)['credit'], 30)

    def test_missing_tail_not_imputed(self):
        ends = [20, None] + [60] * 6
        self.assertFalse(scalar_score(self.case, ends)['half'])

    def test_boundary_and_floor_are_separate(self):
        ends = [39, 40] + [60] * 6
        self.case['parent_floor_violations'] = [0, 1]
        value = scalar_score(self.case, ends)
        self.assertTrue(value['half'])
        self.assertFalse(value['protected_half'])

    def test_independent_ledger_detects_changed_credit(self):
        ends = [39, 40] + [60] * 6
        saved = scores(self.case, [[t, t] for t in ends])
        check_scalar(self.case, ends, saved)
        saved['original_parent_account']['credit'] += 1
        with self.assertRaises(ValueError):
            check_scalar(self.case, ends, saved)

    def test_nash_efficiency_does_not_imply_equal_quality(self):
        result = nash_counterexample()
        self.assertEqual(result['first_share'], '1/3')
        self.assertEqual(result['polynomial_identity_checks'], 1001)


@unittest.skipUnless((OUT / 'results.json.gz').exists(), 'Replay not yet published')
class ReplayArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replay = read(OUT / 'results.json.gz')

    def test_complete_factorial_without_duplicate_cells(self):
        rows = self.replay['rows']
        self.assertEqual(len(rows), 2688)
        cells = {(r['key'], r['policy'], r['unit_seconds'], r['buffered']) for r in rows}
        self.assertEqual(len(cells), len(rows))
        self.assertEqual(len({r['key'] for r in rows}), 168)

    def test_all_independent_analytical_ledgers(self):
        for row in self.replay['rows']:
            check_scalar(row, [e[0] for e in row['ideal']['ends']], row['ideal'])

    def test_remux_preparation_identity_record(self):
        data = read(DATA)
        self.assertEqual(len(data['rows']), 96)
        self.assertEqual(sum(len(r['children']) for r in data['rows']), 480)
        for r in data['rows']:
            self.assertTrue(r['payload_and_decoded_parity'])
            self.assertEqual(sum(c['frames'] for c in r['children']), r['packets'])
            self.assertAlmostEqual(sum(c['duration'] for c in r['children']), r['duration'])

    def test_frozen_measurement_dependencies(self):
        meta = json.loads((OUT / 'metadata.json').read_text())
        for key, value in provenance().items():
            self.assertEqual(meta[key], value)


@unittest.skipUnless((RAW / 'session_00.json.gz').exists(), 'Browser records not yet published')
class RawEventCorruptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = read(RAW / 'session_00.json.gz')
        cls.case = json.loads((OUT / 'schedule.json').read_text())[0]

    def test_original_record_passes_both_layers(self):
        self.assertTrue(audit_session(self.raw, self.case)['valid'])
        self.assertGreater(raw_crosschecks(self.raw, self.case)['server_payload_identities'], 0)

    def test_changed_payload_is_rejected(self):
        r = deepcopy(self.raw)
        r['browser']['receipts'][0]['bytes'] += 1
        with self.assertRaises(ValueError):
            audit_session(r, self.case)

    def test_request_cadence_is_not_free(self):
        r = deepcopy(self.raw)
        next(x for x in r['browser']['receipts'] if x['j'] == 1)['request'] = 0
        with self.assertRaises(ValueError):
            audit_session(r, self.case)

    def test_report_identity_is_checked(self):
        r = deepcopy(self.raw)
        r['server']['reports'][0]['j'] = 99
        with self.assertRaises(ValueError):
            audit_session(r, self.case)

    def test_report_payload_is_checked(self):
        r = deepcopy(self.raw)
        r['server']['reports'][0]['ended'] += 1
        with self.assertRaises(ValueError):
            raw_crosschecks(r, self.case)

    def test_rate_overspend_is_checked(self):
        r = deepcopy(self.raw['server'])
        first = r['batches'][0]
        key = next(iter(first['sent']))
        first['sent'][key] = first['budget'] + 1
        with self.assertRaises(ValueError):
            audit_service(r)

    def test_credit_intervals_cannot_overlap(self):
        r = deepcopy(self.raw)
        r['server']['batches'][1]['interval_start'] = r['server']['batches'][0]['at'] - .001
        with self.assertRaises(ValueError):
            raw_crosschecks(r, self.case)

    def test_setup_and_control_are_not_omitted(self):
        r = deepcopy(self.raw)
        r['server']['transfers'][0]['eligible'] += .1
        with self.assertRaises(ValueError):
            raw_crosschecks(r, self.case)

    def test_partial_session_is_retained_as_failure(self):
        r = {'status': 'failed', 'error': 'Synthetic watchdog'}
        result = audit_session(r, self.case)
        self.assertFalse(result['valid'])
        self.assertEqual(result['error'], 'Synthetic watchdog')

    def test_case_inspector_preserves_contract(self):
        result = inspect_session(0)
        self.assertEqual(result['resource'], self.case['resource'])
        self.assertEqual(len(result['parents']), 4)
        self.assertEqual(result['key'], self.case['key'])

    def test_case_inspector_rejects_out_of_range(self):
        for index in (-1, 74):
            with self.assertRaises(ValueError):
                inspect_session(index)


if __name__ == '__main__':
    unittest.main()
