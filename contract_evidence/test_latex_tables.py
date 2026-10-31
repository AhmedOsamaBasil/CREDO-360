"""Constructed evidence checks; never consumes real playback outcomes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from .assemble import CONDITIONS, digest, feasibility_tables, timing_tables
from .test_assemble import feasibility_fixture
from wu_playback.test_reporting import fixture
from wu_playback.reporting import summarize
from .latex_tables import decimal, escape, tables, build


def example(invalid=False):
    audit, plan=fixture()
    for case in plan['cases']:
        case['condition']=dict(zip(('a','b'),CONDITIONS))[case['condition']]
    if invalid:
        audit['rows'][0]={**plan['sessions'][0],'valid':False,'status':'failed'}
    return {'schema':'recovery-contract-evidence-v1',
        'feasibility':feasibility_tables(feasibility_fixture()),
        'timing':timing_tables(summarize(audit,plan),audit)}


class LatexTablesTests(unittest.TestCase):
    def test_exact_half_even_and_signed_values(self):
        self.assertEqual(decimal('1/8',2),'0.12')
        self.assertEqual(decimal('3/8',2),'0.38')
        self.assertEqual(decimal('1/4',3,signed=True),'+0.250')
        self.assertEqual(decimal('-1/4',3,signed=True),'-0.250')
        self.assertEqual(decimal('0',3,signed=True),'0.000')

    def test_no_binary64_integer_round_trip(self):
        self.assertEqual(decimal('9007199254740993',0),'9007199254740993')

    def test_undefined_is_not_zero(self):
        self.assertEqual(decimal(None),'--')

    def test_literal_identifier_escaping(self):
        self.assertEqual(escape('x_1&y%'),r'x\_1\&y\%')

    def test_full_table_census(self):
        result=tables(example())
        self.assertEqual(len(result),7)
        self.assertEqual(result['feasibility_clip_rows.tex'].count(r'\\'),16)
        self.assertEqual(result['timing_macro_rows.tex'].count(r'\\'),12)
        self.assertEqual(result['timing_control_rows.tex'].count(r'\\'),2)

    def test_exclusions_and_undefined_fulfillment_retained(self):
        result=tables(example())
        self.assertEqual(result['feasibility_clip_rows.tex'].count('Metadata exclusion'),6)
        self.assertIn('--',result['control_conditional_rows.tex'])

    def test_incomplete_macro_and_invalid_denominator_retained(self):
        result=tables(example(invalid=True))
        self.assertIn('4/5 & --',result['timing_macro_rows.tex'])
        self.assertIn(r'\newcommand{\PlaybackInvalid}{1}',result['result_numbers.tex'])
        self.assertIn(r'\newcommand{\PlaybackScheduled}{366}',result['result_numbers.tex'])

    def test_missing_macro_rejected(self):
        evidence=example();evidence['timing']['equal_clip_macro'].pop()
        with self.assertRaises(ValueError):tables(evidence)

    def test_reordered_session_census_rejected(self):
        evidence=example();evidence['timing']['session_comparisons'].reverse()
        with self.assertRaises(ValueError):tables(evidence)

    def test_hash_bound_export_replays_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';source.mkdir();output=root/'output'
            evidence=example()
            (source/'evidence.json').write_text(json.dumps(evidence))
            (source/'metadata.json').write_text(json.dumps({'evidence_sha256':digest(evidence)}))
            saved=build(source,output)
            self.assertEqual(build(source,output,True),saved)
            with self.assertRaises(FileExistsError):build(source,output)
            with (output/'result_numbers.tex').open('a') as stream:stream.write('changed')
            with self.assertRaises(ValueError):build(source,output,True)

    def test_changed_evidence_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';source.mkdir();output=root/'output'
            evidence=example();changed=copy.deepcopy(evidence);changed['changed']=True
            (source/'evidence.json').write_text(json.dumps(changed))
            (source/'metadata.json').write_text(json.dumps({'evidence_sha256':digest(evidence)}))
            with self.assertRaises(ValueError):build(source,output)
            self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
