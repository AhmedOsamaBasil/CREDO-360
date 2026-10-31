"""Preserve generated-only browser compatibility evidence, including failures."""
import argparse
import gzip
import json
from pathlib import Path
from wu_feasibility.spec import ROOT, canonical, digest, file_hash
from .core import TICKS, ideal, resource, scores
from .audit import audit


def case_for(entry):
    units = [{**u, 'duration_ticks': int(u['duration']*TICKS),
              'baseline_bytes': [f['bytes'] for f in u['files']]} for u in entry['units']]
    case = {**entry, 'condition':'generated_only', 'loss':1, 'units':units,
            'parent_gains':[0]*4, 'chunk_gains':[0]*len(units),
            'parent_floor_violations':[0,0], 'chunk_floor_violations':[0,0],
            'resource':resource(units,0)}
    timing=ideal(units,entry['buffered']);case['ideal']={**timing,**scores(case,timing['end_ticks'])}
    return case


def inspect(private, metadata_name='metadata.json'):
    meta=json.loads((private/metadata_name).read_text())
    if meta['synthetic_only'] is not True or meta['wu_media_accessed'] is not False:
        raise ValueError('Generated-only evidence required')
    if meta['source_report_sha256']!=file_hash(ROOT/'wu_pipeline/results/synthetic_v1/report.json'):
        raise ValueError('Generated source binding changed')
    rows=[]; hashes={}
    for entry in meta['cases']:
        path=private/f"session_{entry['index']}.json.gz"
        if not path.exists():
            rows.append({'index':entry['index'],'status':'not_run_after_failure','valid':False});continue
        raw=json.loads(gzip.decompress(path.read_bytes()));hashes[path.name]=file_hash(path)
        session={k:entry[k] for k in ('index','case_id','repetition','control')}
        try:row=audit(raw,case_for(entry),session)
        except (ValueError,KeyError,TypeError) as e:
            row={'index':entry['index'],'status':'audit_failed','valid':False,'error':str(e)}
        rows.append(row)
    return {'schema':'wu-generated-playback-compatibility-v1','synthetic_only':True,'wu_media_accessed':False,
        'quality_claim':False,'dummy_zero_credit_ledger_only':True,'not_a_recovery_contract_success_test':True,
        'rows':rows,'valid':sum(r['valid'] for r in rows),'planned':len(meta['cases']),
        'raw_bindings':hashes,'runtime':meta['runtime'],'source_report_sha256':meta['source_report_sha256']}


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--private',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verify',action='store_true');a=p.parse_args()
    if a.verify:
        meta=json.loads((a.output/'metadata.json').read_text())
        if meta['audit_source_sha256']!=file_hash(Path(__file__)):raise ValueError('Synthetic audit source changed')
        for name,sha in meta['files'].items():
            if Path(name).name!=name or file_hash(a.output/name)!=sha:raise ValueError('Synthetic file hash differs')
        if {p.name for p in a.output.iterdir()}!=set(meta['files'])|{'metadata.json'}:raise ValueError('Synthetic census differs')
        # Export contains original runtime metadata and raw events, sufficient for offline audit.
        result=inspect(a.output,'source_metadata.json')
        if json.loads((a.output/'report.json').read_text())!=result:raise ValueError('Synthetic event audit differs')
    else:
        if a.private is None:p.error('Private generated attempt required')
        result=inspect(a.private);a.output.mkdir(parents=True,exist_ok=False)
        for path in sorted(a.private.iterdir()):
            if path.name=='metadata.json':target='source_metadata.json'
            elif path.name in result['raw_bindings']:target=path.name
            else:raise ValueError('Unexpected private synthetic file')
            with (a.output/target).open('xb') as f:f.write(path.read_bytes())
        with (a.output/'report.json').open('xb') as f:f.write(canonical(result))
        meta={'files':{p.name:file_hash(p) for p in sorted(a.output.iterdir())},
              'audit_source_sha256':file_hash(Path(__file__))}
        with (a.output/'metadata.json').open('xb') as f:f.write(canonical(meta))
    print(json.dumps({'report_sha256':digest(result),'valid':result['valid'],'planned':result['planned'],'synthetic_only':True}))


if __name__=='__main__':main()
