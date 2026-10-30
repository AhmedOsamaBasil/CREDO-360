"""Synthetic checks required before reserved-source pose inspection."""
import hashlib
import io
import math
import unittest
from unittest.mock import Mock,patch
import zipfile
import numpy as np

from wu_qualification.test_core import fixture
from wu_qualification.core import parse_clocks,qualify_clock,member
from .core import (load_roster,guard,selected_fields,load_selected,quaternion_checks,
    scalar_vector,project_selected,summarize)
from .replication import compare


def identity(): return [[0,0,0,1.] for _ in range(60)]


class QuaternionTests(unittest.TestCase):
    def test_identity(self):
        status,poses=project_selected(identity())
        self.assertTrue(status['accepted']); self.assertEqual(poses.shape,(60,2))
        np.testing.assert_allclose(poses,np.tile([90.,0],(60,1)))

    def test_sign_invariance(self):
        q=identity(); q[0]=[.1,.2,.3,.9]; q[0]=(np.array(q[0])/np.linalg.norm(q[0])).tolist()
        a=project_selected(q)[1]; b=project_selected([[-v for v in row] for row in q])[1]
        np.testing.assert_allclose(a,b,atol=1e-12)

    def test_explicit_small_normalization(self):
        q=identity(); q[0][-1]=1.009
        status,poses=project_selected(q)
        self.assertTrue(status['accepted']); self.assertAlmostEqual(status['quaternion']['maximum_valid_selected_norm_error'],.009)
        np.testing.assert_allclose(poses,np.tile([90.,0],(60,1)))

    def failure(self,value,reason):
        q=identity(); q[20]=value; status,poses=project_selected(q)
        self.assertFalse(status['accepted']); self.assertIsNone(poses)
        self.assertEqual(status['reasons'],[reason]); self.assertEqual(status['quaternion']['invalid_samples'],1)
        self.assertIsNone(status['geometry'])

    def test_nonnumeric(self): self.failure(['private value',0,0,1],'nonnumeric_quaternion')
    def test_nonfinite_nan(self): self.failure([float('nan'),0,0,1],'nonfinite_quaternion')
    def test_nonfinite_inf(self): self.failure([0,0,0,float('inf')],'nonfinite_quaternion')
    def test_zero(self): self.failure([0,0,0,0],'zero_quaternion')
    def test_over_norm(self): self.failure([0,0,0,1.0101],'quaternion_norm_out_of_tolerance')
    def test_under_norm(self): self.failure([0,0,0,.9899],'quaternion_norm_out_of_tolerance')
    def test_overflow_safe(self): self.failure([1e308]*4,'quaternion_norm_out_of_tolerance')
    def test_shape(self):
        with self.assertRaises(ValueError): project_selected(identity()[:-1])

    def test_all_invalid(self):
        status,poses=project_selected([[0,0,0,0]]*60)
        self.assertIsNone(status['quaternion']['maximum_valid_selected_norm_error'])
        self.assertEqual(status['quaternion']['invalid_samples'],60)

    def test_multiple_reasons(self):
        q=identity(); q[0]=[0]*4; q[1]=['opaque']*4
        status,_=project_selected(q)
        self.assertEqual(status['reasons'],['nonnumeric_quaternion','zero_quaternion'])

    def test_random_hamilton_agreement(self):
        rng=np.random.default_rng(48016); q=rng.normal(size=(60,4)); q/=np.linalg.norm(q,axis=1)[:,None]
        status,_=project_selected(q.tolist()); self.assertTrue(status['accepted'])
        self.assertTrue(status['geometry']['tile_membership_exact'])

    def test_positive_x_seam(self):
        q=[[0,math.sqrt(.5),0,math.sqrt(.5)]]*60
        status,poses=project_selected(q); self.assertTrue(status['accepted'])
        self.assertTrue(np.all(np.abs(np.abs(poses[:,0])-180)<1e-10))

    def test_negative_z_axis(self):
        status,poses=project_selected([[0,1,0,0]]*60)
        np.testing.assert_allclose(poses,np.tile([-90.,0],(60,1)))

    def test_hamilton_axes(self):
        np.testing.assert_allclose(scalar_vector([0,0,0,1]),[0,0,1])
        np.testing.assert_allclose(scalar_vector([1,0,0,0]),[0,0,-1])

    def test_independent_mismatch_halts(self):
        with patch('wu_pose.core.scalar_vector',return_value=(1,0,0)):
            with self.assertRaisesRegex(ValueError,'Independent geometry mismatch'):
                project_selected(identity())

    def test_weight_membership_mismatch_halts(self):
        with patch('wu_pose.core.scalar_weights',return_value=np.ones((6,12))/72):
            with self.assertRaisesRegex(ValueError,'Independent geometry mismatch'):
                project_selected(identity())


class AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=load_roster(); cls.records={(r['clip'],r['source_id']):r for r in cls.parent['rows']}

    def test_qualified_guard_count(self):
        self.assertEqual(sum(r['metadata_qualified'] for r in self.records.values()),452)

    def test_excluded_member_not_read(self):
        for clip,identity in [('e1v07','1'),('e2v02','1'),('e2v09','1'),('e1v02','1'),('e2v04','1'),('e1v01','99')]:
            archive=Mock()
            with self.assertRaises(ValueError): load_selected(archive,self.records,clip,identity)
            archive.getinfo.assert_not_called(); archive.read.assert_not_called()

    def test_no_nonselected_pose_conversion(self):
        raw=fixture(); chosen=list(range(10,1200,20)); fields=selected_fields(raw,chosen)
        self.assertEqual(len(fields),60); self.assertEqual(fields[0],['opaque NOT A NUMBER']*4)

    def test_duplicate_indices(self):
        with self.assertRaises(ValueError): selected_fields(fixture(),[0]*60)

    def test_missing_selected_rows(self):
        with self.assertRaises(ValueError): selected_fields(fixture([0,1]),list(range(60)))

    def test_negative_indices(self):
        with self.assertRaises(ValueError): selected_fields(fixture(),list(range(-1,59)))

    def fake_archive(self,corrupt=False):
        raw=fixture(); wall,t=parse_clocks(raw)
        record={'metadata_qualified':True,'trace_member_sha256':hashlib.sha256(raw).hexdigest(),**qualify_clock(wall,t)}
        if corrupt: record['trace_member_sha256']='0'*64
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z: z.writestr(member('e1v01','1'),raw)
        return zipfile.ZipFile(io.BytesIO(stream.getvalue())),{('e1v01','1'):record}

    def test_complete_member_bindings(self):
        archive,records=self.fake_archive()
        with archive: fields=load_selected(archive,records,'e1v01','1')
        self.assertEqual(len(fields),60)

    def test_member_hash_mismatch(self):
        archive,records=self.fake_archive(True)
        with archive,self.assertRaisesRegex(ValueError,'Source member binding differs'):
            load_selected(archive,records,'e1v01','1')

    def test_index_hash_mismatch(self):
        archive,records=self.fake_archive(); records['e1v01','1']['selected_row_indices_sha256']='0'*64
        with archive,self.assertRaises(ValueError): load_selected(archive,records,'e1v01','1')

    def test_clock_evidence_mismatch(self):
        archive,records=self.fake_archive(); records['e1v01','1']['clock_evidence']['rows']=0
        with archive,self.assertRaisesRegex(ValueError,'Clock metadata differs'):
            load_selected(archive,records,'e1v01','1')


class PairTests(unittest.TestCase):
    def example(self):
        parent={'clips':[{'clip':'test','experiment':1,'condition':'free_exploration',
            'clip_qualified':True,'clip_reasons':[],'directed_pairs':[['1','2'],['2','3'],['3','1']]}]}
        rows=[{'clip':'test','source_id':str(i),'pose_validated':True} for i in range(1,4)]
        return parent,rows

    def test_all_pairs_fixed(self):
        parent,rows=self.example(); result=summarize(parent,rows)[0]
        self.assertEqual(result['usable_pairs'],3)
        self.assertEqual([[p['recipient'],p['donor']] for p in result['candidate_pairs']],parent['clips'][0]['directed_pairs'])

    def test_failed_identity_no_repartnering(self):
        parent,rows=self.example(); rows[1]['pose_validated']=False; result=summarize(parent,rows)[0]
        self.assertEqual(result['usable_pairs'],1); self.assertEqual(len(result['candidate_pairs']),3)
        self.assertEqual([p['usable'] for p in result['candidate_pairs']],[False,False,True])

    def test_all_fail_retained(self):
        parent,rows=self.example()
        for r in rows:r['pose_validated']=False
        result=summarize(parent,rows)[0]
        self.assertEqual(len(result['candidate_pairs']),3); self.assertEqual(result['usable_pairs'],0)


class ReplicationTests(unittest.TestCase):
    def test_exact(self): self.assertTrue(compare({'x':1.},{'x':1.})['exact_report_match'])
    def test_small_float_difference_retained(self):
        result=compare({'x':1.},{'x':1.+1e-12})
        self.assertFalse(result['exact_report_match']); self.assertEqual(result['differing_float_values'],1)
    def test_large_float_difference(self):
        with self.assertRaises(ValueError): compare({'x':1.},{'x':1.+1e-5})
    def test_count_difference(self):
        with self.assertRaises(ValueError): compare({'x':1},{'x':2})
    def test_bool_difference(self):
        with self.assertRaises(ValueError): compare({'x':False},{'x':True})
    def test_field_difference(self):
        with self.assertRaises(ValueError): compare({'x':1},{'y':1})
    def test_type_difference(self):
        with self.assertRaises(ValueError): compare({'x':1},{'x':1.})
    def test_nonfinite(self):
        with self.assertRaises(ValueError): compare({'x':float('nan')},{'x':float('nan')})


if __name__=='__main__': unittest.main()
