import unittest
import numpy as np
from feedback_opportunity.feedback import mask,weights
from admission_contract.core import spatial_bounds,certificate
from metric_contract.core import path_arrays,TICKS
from geometric_admission.geometry import representatives,family,integer_grid_family,matrix,validate_family,bounds,check_extrema


class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=family();cls.values={bytes.fromhex(r['mask_hex']) for r in cls.rows}

    def test_independent_complete_family(self):
        self.assertEqual(self.values,integer_grid_family());self.assertTrue(validate_family(self.rows)['integer_lattice_match'])

    def test_all_witness_orientations_match(self):
        for r in self.rows:self.assertEqual(mask(r['yaw'],r['pitch']).hex(),r['mask_hex'])

    def test_seam_and_rotations(self):
        for pitch in (-90,-65,0,65,90):
            self.assertEqual(mask(-180,pitch),mask(180,pitch))
            self.assertEqual(mask(17,pitch),mask(377,pitch))

    def test_boundary_and_adjacent_masks_covered(self):
        for yaw in representatives('yaw'):
            for pitch in representatives('pitch'):
                for e in (-1e-5,0,1e-5):
                    self.assertIn(mask(yaw+e,max(-90,min(90,pitch+e))),self.values)

    def test_random_orientations_covered(self):
        rng=np.random.default_rng(914)
        for yaw,pitch in zip(rng.uniform(-1080,1080,1500),rng.uniform(-90,90,1500)):
            self.assertIn(mask(yaw,pitch),self.values)

    def test_poles_nonempty_and_normalized(self):
        w=matrix(self.rows)
        self.assertTrue((w>=0).all());np.testing.assert_allclose(w.sum(axis=1),1,atol=1e-15)
        for y in range(-180,180,30):self.assertGreater(sum(weights(mask(y,90))),.99)

    def test_uniform_fields_geometry_matches_convex(self):
        maps=np.ones((6,60,72))*100;maps[3]=90
        lo,hi,_=bounds(maps,self.rows);oldlo,oldhi=spatial_bounds(maps)
        np.testing.assert_equal(lo,oldlo);np.testing.assert_equal(hi,oldhi)

    def test_tighter_than_single_tile_extrema(self):
        maps=np.ones((6,60,72))*100;maps[3]=90;maps[3,:,0]=101
        lo,hi,w=bounds(maps,self.rows);oldlo,oldhi=spatial_bounds(maps)
        self.assertGreater(lo[2,3],oldlo[2,3]);self.assertLessEqual(hi[2,3],oldhi[2,3]+1)
        self.assertTrue(check_extrema(maps,self.rows,lo,hi,w)['passed'])

    def test_representable_viewport_inside_bounds(self):
        rng=np.random.default_rng(124);maps=rng.uniform(1,100,(6,60,72));lo,hi,_=bounds(maps,self.rows)
        ws=np.stack([weights(mask(float(rng.uniform(-180,180)),float(rng.uniform(-90,90)))) for _ in range(60)])
        mse=np.sum(maps*ws,axis=2).reshape(6,6,10).mean(axis=2).T
        units=np.floor(mse*1e6+.5).astype(np.int64);delta=units[:,2:3]-units
        self.assertTrue(((delta>=lo)&(delta<=hi)).all())

    def test_geometric_certificate_can_admit_where_tile_cannot(self):
        maps=np.ones((6,60,72))*100;maps[3]=90;maps[3,:,0]=101
        lo,hi,_=bounds(maps,self.rows);oldlo,oldhi=spatial_bounds(maps)
        costs=np.ones((6,6),dtype=np.int64)*10000;ds=[10*TICKS]*6;arrays=path_arrays(costs,4,80000)
        debt=30_000_000*TICKS
        self.assertEqual(certificate(oldlo,oldhi,costs,arrays,ds,debt)['status'],'abstain')
        self.assertEqual(certificate(lo,hi,costs,arrays,ds,debt)['status'],'admit')

    def test_reference_exact_zero(self):
        lo,hi,w=bounds(np.ones((6,60,72)),self.rows)
        self.assertTrue((lo[:,2]==0).all());self.assertTrue((hi[:,2]==0).all())

    def test_invalid_maps(self):
        with self.assertRaises(ValueError):bounds(np.ones((6,60,71)),self.rows)
        with self.assertRaises(ValueError):bounds(np.full((6,60,72),float('nan')),self.rows)


if __name__=='__main__':unittest.main()
