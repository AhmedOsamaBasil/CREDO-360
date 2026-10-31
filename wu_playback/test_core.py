"""Generated-data tests for fixed scheduling, exact credit and isolation."""
import copy
from fractions import Fraction
import unittest
from .core import ideal, resource, ledger, scores, scalar_scores, schedule, player_entry
from .build import clip_cases


def fixture(name='clip00'):
    media = []
    for rung in range(6):
        parents = []
        for t in range(6):
            def record(child=None):
                seconds = 10 if child is None else 2
                return {'relative_path': f'{name}/{rung}/{t}/{child}.mp4', 'sha256': 'a'*64,
                        'bytes': (20000+10000*rung) if child is None else (4000+2000*rung+17),
                        'frames': 30*seconds, 'duration_ticks': 150000*seconds}
            parent = record(); parent['children'] = [record(c) for c in range(5)] if rung >= 2 and t >= 2 else []
            parents.append(parent)
        media.append({'rung': rung, 'parents': parents})
    pair = {'recipient': 'a', 'donor': 'b', 'usable': True, 'failed_source_ids': []}
    clip = {'clip': name, 'condition': 'free', 'eligible': True, 'pairs': [pair], 'source_ids': ['a', 'b'], 'media': media}
    def labels(count, ticks):
        values = [100., 80., 60., 20., 10., 5.]
        return {'information_scope': 'offline_evaluation_only', 'independent_scalar_micro_exact': True,
                'native_mse': [[v]*count for v in values], 'negative_micro_mse': [[-int(v*1000000)]*count for v in values],
                'duration_ticks': [ticks]*count}
    data = {'information_scope': 'offline_evaluation_only', 'rows': [
        {'source_id': s, 'parent': labels(6, 1500000), 'child': labels(30, 300000)} for s in ('a', 'b')]}
    controls = [{'method': p, 'proposed_path': [[3, 2]]*4, 'executed_path': [[2, 2]]*4, 'status': 'abstain'}
                for p in ('cost_greedy', 'rolling_nash', 'maxmin')]
    feasibility = {'reserve_bytes': 320000, 'pairs': [{**pair, 'disposition': 'evaluated', 'loss': 120000000000000,
                    'modes': [{'execution_mode': 'ideal', 'controls': controls}]}]}
    return clip, feasibility, data


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.cases = clip_cases(*fixture())

    def test_all_twelve_cells(self): self.assertEqual(len(self.cases), 12)

    def test_ungated_proposals_not_fallback(self):
        self.assertTrue(all(c['path'] == [[3, 2]]*4 and c['original_gate_status'] == 'abstain' for c in self.cases))

    def test_primary_credit_independent_of_delivery_split(self):
        self.assertEqual(len({tuple(c['parent_gains']) for c in self.cases}), 1)
        self.assertEqual(len({c['loss'] for c in self.cases}), 1)

    def test_all_container_bytes_counted(self):
        parent = next(c for c in self.cases if c['unit_seconds'] == 10)
        child = next(c for c in self.cases if c['unit_seconds'] == 2)
        self.assertEqual(child['resource']['payload_bytes']-parent['resource']['payload_bytes'], 17*40)

    def test_charged_buffer(self):
        for c in self.cases:
            t = c['ideal']
            if c['buffered']:
                n = 1 if c['unit_seconds'] == 10 else 2
                self.assertEqual(t['buffer_gate_ticks'], max(x for a in t['arrival_ticks'][:n] for x in a))
            else: self.assertEqual(t['buffer_gate_ticks'], 0)

    def test_no_quality_in_player_entry(self):
        session = {'index': 0, 'case_id': self.cases[0]['case_id'], 'repetition': 0, 'control': 'none'}
        entry = player_entry(self.cases[0], session)
        self.assertEqual(set(entry), {'index','case_id','repetition','control','clip','key','policy','unit_seconds','buffered','units'})
        self.assertNotIn('loss', str(entry)); self.assertNotIn('gain', str(entry)); self.assertNotIn('ideal', entry)

    def test_missing_first_path_not_replaced(self):
        clip, result, data = fixture(); result['pairs'][0]['modes'][0]['controls'][0]['proposed_path'] = None
        with self.assertRaises(ValueError): clip_cases(clip, result, data)

    def test_different_debt_rejected(self):
        clip, result, data = fixture(); result['pairs'][0]['loss'] += 1
        with self.assertRaises(ValueError): clip_cases(clip, result, data)

    def test_unusable_first_pair_not_replaced(self):
        clip, result, data = fixture(); clip['pairs'][0]['usable'] = False
        with self.assertRaises(ValueError): clip_cases(clip, result, data)

    def test_changed_duration_rejected(self):
        clip, result, data = fixture(); clip['media'][3]['parents'][2]['children'][1]['duration_ticks'] += 1
        with self.assertRaises(ValueError): clip_cases(clip, result, data)

    def test_no_event_not_called_recovery(self):
        value = ledger(0, [100], [0,0], [0], {'cap_ok': True, 'reserve_ok': True})
        self.assertIsNone(value['half']); self.assertIsNone(value['fraction_repaid'])

    def test_complete_366_session_census(self):
        cases = [c for i in range(10) for c in clip_cases(*fixture(f'clip{i:02}'))]
        rows = schedule(cases)
        self.assertEqual(len(rows), 366)
        self.assertEqual([r['index'] for r in rows], list(range(366)))
        self.assertEqual(sum(r['control']=='none' for r in rows), 360)
        self.assertEqual([r['index'] for r in rows if r['control']!='none'], [120,121,242,243,364,365])

    def test_rotation_not_outcome_based(self):
        cases = [c for i in range(10) for c in clip_cases(*fixture(f'clip{i:02}'))]
        original = schedule(cases)
        for c in cases: c['loss'] = 42; c['ideal'] = {'adverse': True}
        self.assertEqual(schedule(cases), original)
        self.assertNotEqual(original[0]['case_id'], original[122]['case_id'])

    def test_duplicate_missing_cell_fails(self):
        cases = [c for i in range(10) for c in clip_cases(*fixture(f'clip{i:02}'))]
        cases[0] = cases[1]
        with self.assertRaises(ValueError): schedule(cases)

    def test_integer_credit_above_float_precision(self):
        gain = 2**55+1
        v = ledger(2*gain, [gain], [0,0], [6000000], {'cap_ok': True,'reserve_ok':True})
        self.assertEqual(v['credit'], gain); self.assertEqual(v['fraction_repaid'], '1/2')

    def test_exact_deadline_no_epsilon_credit(self):
        v = ledger(10, [5], [0,0], [Fraction(6000000)+Fraction(1,1000000)], {'cap_ok':True,'reserve_ok':True})
        self.assertEqual(v['credit'], 0)

    def test_incomplete_child_cannot_complete_parent(self):
        c = next(c for c in self.cases if c['unit_seconds']==2 and not c['buffered'])
        ends = [[1,1] for _ in c['units']]; ends[3][0] = None
        v = scores(c, ends)
        self.assertEqual(v['original_parent_account']['completed_units'], 3)
        self.assertEqual(v['secondary_chunk_account']['completed_units'], 19)
        self.assertEqual(scalar_scores(c,ends)['original_parent_account']['credit'], v['original_parent_account']['credit'])

    def test_late_floors_not_removed(self):
        c = copy.deepcopy(self.cases[0]); c['parent_floor_violations'] = [0,1]
        v = scores(c, [[1,1]]*len(c['units']))
        self.assertTrue(v['original_parent_account']['half']); self.assertFalse(v['original_parent_account']['protected_half'])


if __name__ == '__main__': unittest.main()
