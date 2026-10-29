import io
import itertools
import math
from unittest.mock import Mock
import unittest
import numpy as np
from .core import (plan,member,load_trace,parse_trace,forward,ascending_crossings,clock_summary,
    candidate_uv,uv_unit,match_points,mapping_gate,held_reference)
from wu_source.clocks import HEADER


class GuardTests(unittest.TestCase):
    def test_partition(self):
        p=plan(); self.assertEqual(len(p['confirmation_clips']),16)
        self.assertEqual(sum(x.startswith('e1') for x in p['confirmation_clips']),8)
    def test_exact_mapping(self):
        self.assertEqual(member('e2v04','48'),'Formated_Data/Experiment_2/48/video_3.csv')
    def test_reserved_rejected_before_open(self):
        for clip in plan()['confirmation_clips']:
            z=Mock()
            with self.assertRaises(ValueError): load_trace(z,clip,'1')
            z.open.assert_not_called(); z.getinfo.assert_not_called()
    def test_identity_guard(self):
        for identity in ('0','49','01','../1'):
            with self.assertRaises(ValueError): member('e1v02',identity)
    def test_private_calendar_positions(self):
        source=','.join(HEADER)+'\n2020-01-01 10:00:00.000,0,0,0,0,1,opaque,opaque,opaque\n2020-01-01 10:00:00.020,0.02,0,0,0,1,opaque,opaque,opaque\n'
        wall,t,q=parse_trace(io.StringIO(source))
        np.testing.assert_allclose(wall,[0,.02]); np.testing.assert_allclose(t,[0,.02])
        self.assertEqual(q.shape,(2,4))


class CrossingTests(unittest.TestCase):
    def test_unique_duplicates_retained(self): np.testing.assert_equal(ascending_crossings([0,.49,.51,.51,.6],.5),[2])
    def test_first_unbracketed_not_used(self): self.assertEqual(len(ascending_crossings([.51,.6],.5)),0)
    def test_reset_two_crossings(self): np.testing.assert_equal(ascending_crossings([0,.51,0,.52],.5),[1,3])
    def test_age_limit(self): self.assertEqual(len(ascending_crossings([0,.7],.5)),0)
    def test_exact_age_boundary(self): np.testing.assert_equal(ascending_crossings([0,.6],.5),[1])
    def test_invalid(self):
        for t in ([0,float('nan')],[0,-1]):
            with self.assertRaises(ValueError): ascending_crossings(t,.5)
    def test_no_sorting(self): np.testing.assert_equal(ascending_crossings([0,.53,.2,.54,.1,.52],.5),[1,3,5])
    def test_summary_ambiguity(self):
        t=np.array([0,.51,.1,.52,60]); wall=np.arange(5.)
        v=np.array([[0,0,1],[0,0,1],[0,0,1],[1,0,0],[0,0,1]])
        r=clock_summary(wall,t,v)
        self.assertEqual(r['targets_multiple'],1); self.assertAlmostEqual(r['first_last_max_angular_difference_degrees'],90)
    def test_wall_backward_preserved(self):
        r=clock_summary(np.array([0,1,.5]),np.array([0,.51,60]),np.array([[0,0,1]]*3))
        self.assertEqual(r['wall_backward_steps'],1)


class ProjectionTests(unittest.TestCase):
    def test_unit_normalization_explicit(self):
        vectors,err=forward([[0,0,0,1.001]])
        np.testing.assert_allclose(vectors,[[0,0,1]]); self.assertAlmostEqual(err,.001)
    def test_bad_norm_rejected(self):
        for q in ([[0,0,0,0]],[[0,0,0,1.1]],[[0,0,math.nan,1]]):
            with self.assertRaises(ValueError): forward(q)
    def test_both_signs(self):
        np.testing.assert_allclose(candidate_uv([[0,0,1]],1),[[.25,.5]])
        np.testing.assert_allclose(candidate_uv([[0,0,1]],-1),[[.75,.5]])
    def test_spherical_seam(self):
        self.assertLess(match_points([[0,.5]],[[1,.5]])[0],1e-5)
    def test_permutation(self):
        a=np.array([[.1,.3],[.4,.6],[.8,.5]])
        self.assertLess(max(match_points(a,a[[2,0,1]])),1e-5)
    def test_independent_assignment(self):
        a=np.array([[.1,.3],[.4,.6],[.8,.5]]); b=np.array([[.42,.61],[.79,.48],[.09,.32]])
        x,y=uv_unit(a),uv_unit(b); d=np.degrees(np.arccos(np.clip(x@y.T,-1,1)))
        expected=min(sum(d[i,p[i]] for i in range(3)) for p in itertools.permutations(range(3)))
        self.assertAlmostEqual(sum(match_points(a,b)),expected)
    def test_no_unmatched_hidden(self):
        with self.assertRaises(ValueError): match_points([[.1,.3]],[[.1,.3],[.2,.4]])
    def test_hold_previous_reference(self):
        points={49:('old','a'),52:('new','b')}
        self.assertEqual(held_reference(points,5),('old','a')); self.assertIsNone(held_reference(points,4))
    def test_gate_separates_sign(self):
        cells=[{'wrap_sign':s,'crossing':c,'points':48,'errors_degrees':[.1 if s==1 else 20]*48} for s in (-1,1) for c in ('first','last') for _ in range(5)]
        self.assertEqual(mapping_gate(cells)['supported_sign'],1)
    def test_gate_incomplete_abstains(self): self.assertIsNone(mapping_gate([])['supported_sign'])
    def test_gate_ambiguous_abstains(self):
        cells=[{'wrap_sign':s,'crossing':c,'points':48,'errors_degrees':[.1]*48} for s in (-1,1) for c in ('first','last') for _ in range(5)]
        self.assertIsNone(mapping_gate(cells)['supported_sign'])


if __name__=='__main__': unittest.main()
