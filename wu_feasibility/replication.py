"""Post-freeze diagnostic: preserve complete platform outputs and exact differences.

Does not amend the registered evaluator or accept any discrepancy by tolerance.
"""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import platform
import re
import sys
from geometric_admission.geometry import family
from .run import evaluate_clip, summarize
from .spec import PACKAGE, EXPORT, canonical, digest, verify, file_hash
from wu_pipeline_v2.audit import verify_export

PRIMARY = PACKAGE/'results/attempt_01'


def differences(a, b, path=''):
    if type(a) is not type(b):
        return [{'path': path, 'primary': a, 'replica': b}]
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return [{'path': path, 'primary_keys': sorted(a), 'replica_keys': sorted(b)}]
        return [r for k in sorted(a) for r in differences(a[k], b[k], path+'/'+k)]
    if isinstance(a, list):
        if len(a) != len(b):
            return [{'path': path, 'primary_length': len(a), 'replica_length': len(b)}]
        return [r for i, (x, y) in enumerate(zip(a, b)) for r in differences(x, y, path+'/'+str(i))]
    return [] if a == b else [{'path': path, 'primary': a, 'replica': b}]


def original(clip):
    return json.loads(gzip.decompress((PRIMARY/(clip+'.json.gz')).read_bytes()))


def witness_only(diffs):
    """Classify evidence, never relabel an exact replay failure as a pass."""
    return all(re.fullmatch(r'/extremal_mask_witnesses/(minimum|maximum)_mask_id/[0-5]/([0-9]|[1-5][0-9])', d['path'])
               and type(d.get('primary')) is int and type(d.get('replica')) is int
               and 0 <= d['primary'] < 216 and 0 <= d['replica'] < 216 for d in diffs)


def verify_saved(output):
    meta = json.loads((output/'metadata.json').read_text())
    if meta['source_sha256'] != file_hash(Path(__file__)):
        raise ValueError('Replication source changed')
    if {p.name for p in output.iterdir()} != set(meta['files']) | {'metadata.json'}:
        raise ValueError('Replica file census differs')
    for name, sha in meta['files'].items():
        if Path(name).name != name or file_hash(output/name) != sha:
            raise ValueError('Replica file binding differs')
    comparison = json.loads((output/'comparison.json').read_text())
    clips = []
    for row in comparison['clips']:
        clip = row['clip']
        value = json.loads(gzip.decompress((output/(clip+'.json.gz')).read_bytes()))
        if digest(value) != row['replica_sha256'] or digest(original(clip)) != row['primary_sha256'] or differences(original(clip), value) != row['differences']:
            raise ValueError('Saved exact comparison differs')
        clips.append(value)
    summary = summarize(clips)
    if json.loads((output/'summary.json').read_text()) != summary or differences(json.loads((PRIMARY/'summary.json').read_text()), summary) != comparison['summary_differences']:
        raise ValueError('Saved summary comparison differs')
    if comparison['registration_sha256'] != digest(verify()):
        raise ValueError('Replica registration differs')
    ds = [d for c in comparison['clips'] for d in c['differences']]
    if len(ds) != comparison['exact_differences'] or witness_only(ds) != comparison['only_extremal_witness_ids_differ']:
        raise ValueError('Saved difference classification differs')
    return {'exact_replay_passed': not ds, 'differences': len(ds),
            'only_extremal_witness_ids_differ': witness_only(ds),
            'summary_exact': not comparison['summary_differences'], 'saved_hashes_verified': True}


def main():
    parser = argparse.ArgumentParser(__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--compare-clip')
    group.add_argument('--output', type=Path)
    group.add_argument('--verify-saved', type=Path)
    group.add_argument('--audit', action='store_true')
    args = parser.parse_args()
    if args.verify_saved:
        print(json.dumps(verify_saved(args.verify_saved)))
        return
    frozen = verify(); verify_export(EXPORT)
    clips = json.loads((EXPORT/'manifest.json').read_text())['clips']; masks = family()
    if args.audit:
        generated = []; ds = []
        for c in clips:
            value = evaluate_clip(c, masks)
            diff = differences(original(c['clip']), value)
            if not witness_only(diff):
                raise ValueError('Non-witness scientific output differs: '+c['clip'])
            ds.extend(diff); generated.append(value)
        if differences(json.loads((PRIMARY/'summary.json').read_text()), summarize(generated)):
            raise ValueError('Scientific summary differs')
        print(json.dumps({'exact_replay_passed': not ds, 'exact_differences': ds,
                          'all_non_witness_fields_exact': True, 'scalar_extrema_rechecked': True,
                          'post_freeze_scientific_audit': True}))
        return
    if args.compare_clip:
        selected = next(c for c in clips if c['clip'] == args.compare_clip)
        result = evaluate_clip(selected, masks)
        diff = differences(original(selected['clip']), result)
        print(json.dumps({'clip': selected['clip'], 'differences': len(diff), 'first_40': diff[:40]}))
        return
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    generated = []; comparisons = []
    for c in clips:
        result = evaluate_clip(c, masks)
        diff = differences(original(c['clip']), result)
        with (output/(c['clip']+'.json.gz')).open('xb') as stream:
            stream.write(gzip.compress(canonical(result), mtime=0))
        generated.append(result)
        comparisons.append({'clip': c['clip'], 'primary_sha256': digest(original(c['clip'])),
                            'replica_sha256': digest(result), 'differences': diff})
        print(json.dumps({'clip': c['clip'], 'exact_differences': len(diff)}), flush=True)
    summary = summarize(generated)
    comparison = {'schema': 'wu-feasibility-exact-platform-comparison-v1',
        'registered_method_changed': False, 'tolerance_acceptance': False,
        'platform': platform.system(), 'python': sys.version.split()[0],
        'registration_sha256': digest(frozen), 'clips': comparisons,
        'summary_differences': differences(json.loads((PRIMARY/'summary.json').read_text()), summary),
        'exact_differences': sum(len(c['differences']) for c in comparisons),
        'only_extremal_witness_ids_differ': witness_only([d for c in comparisons for d in c['differences']]),
        'original_strict_cross_platform_verification': 'failed_at_e1v05',
        'independent_extrema_checks_rerun_on_replica': True}
    for name, value in (('summary.json', summary), ('comparison.json', comparison)):
        with (output/name).open('xb') as stream:
            stream.write(canonical(value))
    metadata = {'source_sha256': file_hash(Path(__file__)),
                'files': {p.name: file_hash(p) for p in sorted(output.iterdir())}}
    with (output/'metadata.json').open('xb') as stream:
        stream.write(canonical(metadata))
    print(json.dumps({'exact_differences': comparison['exact_differences'],
                      'summary_differences': len(comparison['summary_differences'])}))


if __name__ == '__main__':
    main()
