import math
import unittest
import numpy as np
from temporal_viewport.core import (direction, angles, orientation_cells, distance_to_rectangle,
    mask_distances, required_sampled_speed, fit_speed, feature_table, scores_for_maps, SCALE)
from geometric_admission.geometry import family, bounds
from feedback_opportunity.feedback import mask
from metric_contract.core import TICKS


class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = family(); cls.cells = orientation_cells(cls.family)

    def test_all_masks_covered(self):
        self.assertEqual({r['mask_id'] for r in self.cells}, set(range(216)))

    def test_same_wrap_and_poles(self):
        self.assertAlmostEqual(float(angles(direction(179, 0), direction(-179, 0))), 2)
        self.assertAlmostEqual(float(angles(direction(0, 90), direction(170, 90))), 0)
        self.assertAlmostEqual(float(angles(direction(0, 0), direction(180, 0))), 180)

    def test_point_rectangle(self):
        for yaw, pitch in ((0, 0), (-179, 85), (180, -90)):
            for y, p in ((50, 0), (-180, 0), (10, 90)):
                cell = dict(yaw_lo=y, yaw_hi=y, pitch_lo=p, pitch_hi=p)
                self.assertAlmostEqual(distance_to_rectangle(yaw, pitch, cell), float(angles(direction(yaw, pitch), direction(y, p))), places=6)

    def test_rectangle_contains_interior(self):
        cell = dict(yaw_lo=-40, yaw_hi=40, pitch_lo=-20, pitch_hi=30)
        self.assertLess(distance_to_rectangle(5, 10, cell), 1e-5)
        self.assertAlmostEqual(distance_to_rectangle(60, 0, cell), 20)

    def test_closed_cell_distance_is_lower_bound(self):
        rng = np.random.default_rng(71)
        for _ in range(120):
            cell = self.cells[int(rng.integers(len(self.cells)))]; yaw, pitch = rng.uniform(-180, 180), rng.uniform(-90, 90)
            exact = distance_to_rectangle(yaw, pitch, cell)
            yy = np.linspace(cell['yaw_lo'], cell['yaw_hi'], 9)
            pp = np.linspace(cell['pitch_lo'], cell['pitch_hi'], 9)
            points = [float(angles(direction(yaw, pitch), direction(y, p))) for y in yy for p in pp]
            self.assertLessEqual(exact, min(points)+1e-6)

    def test_random_actual_masks_never_excluded(self):
        rng = np.random.default_rng(98); bymask = {r['mask_hex']: i for i, r in enumerate(self.family)}
        for yaw, pitch in ((179, 0), (0, 90), (-110, -45)):
            distances = mask_distances(yaw, pitch, self.family, self.cells)
            for y, p in zip(rng.uniform(-180, 180, 500), rng.uniform(-90, 90, 500)):
                radius = math.ceil(float(angles(direction(yaw, pitch), direction(y, p)))*SCALE)
                self.assertLessEqual(int(distances[bymask[mask(y, p).hex()]]), radius)

    def test_speed_units_and_bad_timestamps(self):
        self.assertAlmostEqual(required_sampled_speed([0, .02, .04], [0, 1, 2], [0, 0, 0]).max(), 50)
        with self.assertRaises(ValueError): required_sampled_speed([0, 0], [0, 0], [0, 0])
        with self.assertRaises(ValueError): direction(0, 91)

    def test_crossfit_excludes_scene_and_both_ids(self):
        rows = [{'key': f'{s}:{i}', 'scene': str(s), 'subject': i, 'whole_max_speed_microdeg_s': i}
                for s in range(6) for i in range(1, 29)]
        threshold, keys = fit_speed(rows, '0', {27, 28}, 1)
        self.assertEqual(threshold, 26); self.assertEqual(len(keys), 130)
        self.assertTrue(all(not k.startswith('0:') and k.split(':')[1] not in ('27', '28') for k in keys))

    def test_bound_nesting_and_full_sphere_limit(self):
        rng = np.random.default_rng(19); maps = rng.uniform(1, 20, (6, 60, 72))
        lower, _, _ = bounds(maps, self.family); scores = scores_for_maps(maps, self.family)
        distances = mask_distances(0, 0, self.family, self.cells)
        tables = [feature_table(scores, distances, TICKS//2, speed*SCALE, 10*TICKS, 2, [11*TICKS], lower)
                  for speed in (0, 5, 30, 360)]
        for a, b in zip(tables, tables[1:]):
            self.assertTrue(np.all(np.array(a[str(11*TICKS)]['lower']) >= np.array(b[str(11*TICKS)]['lower'])))
        self.assertEqual(tables[-1][str(11*TICKS)]['lower'], lower[2, 2:].tolist())
        self.assertEqual(tables[-1][str(11*TICKS)]['full_family_samples'], 10)

    def test_latency_widens_uncertainty(self):
        maps = np.random.default_rng(20).uniform(1, 20, (6, 60, 72))
        lower, _, _ = bounds(maps, self.family); distances = mask_distances(0, 0, self.family, self.cells)
        table = feature_table(scores_for_maps(maps, self.family), distances, TICKS//2, 15*SCALE, 10*TICKS, 2, [11*TICKS, 20*TICKS], lower)
        self.assertTrue(np.all(np.array(table[str(11*TICKS)]['lower']) >= np.array(table[str(20*TICKS)]['lower'])))

    def test_static_cone_can_have_nonvacuous_gain(self):
        maps = np.full((6, 60, 72), 20.0); maps[3] = 25.0
        bits = int.from_bytes(mask(0, 0), 'big')
        ids = [i for i in range(72) if bits >> i & 1]
        maps[3, :, ids] = 19.0
        lower, _, _ = bounds(maps, self.family)
        distances = mask_distances(0, 0, self.family, self.cells)
        table = feature_table(scores_for_maps(maps, self.family), distances, TICKS//2, 0, 10*TICKS, 2, [11*TICKS], lower)
        self.assertLess(lower[2, 3], 0)
        self.assertGreater(table[str(11*TICKS)]['lower'][1], 0)


if __name__ == '__main__':
    unittest.main()
