"""Source-specific immutable pipeline registration; default operation is read-only."""
import argparse
import hashlib
import json
from pathlib import Path
from wu_source.acquire import canonical
from wu_pose.run import read_artifact,DEFAULT,method_record as pose_method
from confirmation_protocol.protocol import validate_design
from .media import LADDER,fingerprint

ROOT=Path(__file__).resolve().parents[1]; PACKAGE=ROOT/'wu_pipeline'
REGISTRATION=PACKAGE/'registration.json'; RUNTIME=PACKAGE/'runtime.json'


def digest(value): return hashlib.sha256(canonical(value)).hexdigest()


def plan():
    report=read_artifact(DEFAULT)
    design=validate_design(json.loads((ROOT/'confirmation_protocol/design.json').read_text()))
    if design['media_pipeline']['ladder_mbps']!=list(LADDER): raise ValueError('Ladder differs')
    clips=[]
    for c in report['clips']:
        clips.append({'clip':c['clip'],'experiment':c['experiment'],'condition':c['condition'],
            'eligible':c['usable_pairs']>0,'source_ids':c['pose_validated_source_ids'],
            'pairs':c['candidate_pairs'],'parent_exclusion_reasons':c['parent_clip_exclusion_reasons']})
    return {'schema':'wu-encoding-measurement-plan-v1','contract':design['contract'],
        'media_pipeline':design['media_pipeline'],'clips':clips,
        'private_files_checked':report['private_files_checked'],
        'expected':{'registered_clips':16,'eligible_clips':10,'directed_pairs':452,
            'renditions':60,'parents':360,'recovery_children':800,'trace_label_rows':452},
        'quality_outputs_created':False,'recovery_outputs_created':False,
        'synthetic_tests_only_at_freeze':True,'automatic_execution':False}


def bindings():
    result=pose_method()['bindings']
    paths=['wu_pipeline/'+n for n in ('PROTOCOL.md','media.py','metrics.py','spec.py','prepare.py','synthetic.py','test_core.py','runtime.json')]
    paths+=['wu_pose/method_v1.json','wu_pose/results/validation_v1/report.json','wu_pose/results/validation_v1/metadata.json',
        'wu_pose/results/linux_v1/report.json','wu_pose/results/replication_v1/report.json']
    for path in paths:
        result[path]=hashlib.sha256((ROOT/path).read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest()
    return result


def registration():
    return {'schema':'wu-encoding-measurement-registration-v1','plan':plan(),
        'bindings':bindings(),'runtime_sha256':digest(json.loads(RUNTIME.read_text())),
        'phase_diagnostic_required':True,'primary_sampler_changed':False,
        'fresh_outcomes_present':False}


def verify():
    saved=json.loads(REGISTRATION.read_text())
    if saved!=registration(): raise ValueError('Frozen pipeline changed')
    return saved


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--capture-runtime',action='store_true')
    p.add_argument('--freeze',action='store_true'); a=p.parse_args()
    if a.capture_runtime:
        with RUNTIME.open('xb') as f: f.write(canonical(fingerprint()))
        print('Media runtime recorded; no source media accessed'); return
    if a.freeze:
        with REGISTRATION.open('xb') as f: f.write(canonical(registration()))
    saved=verify()
    print(json.dumps({'registration_sha256':digest(saved),'expected':saved['plan']['expected'],
        'fresh_outcomes_present':False}))


if __name__=='__main__': main()
