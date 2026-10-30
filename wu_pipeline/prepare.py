"""Explicitly activated future private preparation; never run during code freeze."""
import argparse
import json
from pathlib import Path
import zipfile
import numpy as np
from wu_source.acquire import canonical,sha256
from wu_pose.core import load_roster,load_selected,project_selected
from wu_qualification.core import validate_archive_directory
from .spec import ROOT,RUNTIME,verify,digest
from .media import call,encode_command,describe,split_verified,phase_check,sample_frames,fingerprint
from .metrics import mse_map,aggregate_native


def authorize(private,output,activation):
    frozen=verify()
    if activation!=digest(frozen): raise ValueError('Explicit registered-digest activation required')
    output=output.resolve(); private=private.resolve()
    if output.is_relative_to(ROOT.resolve()) or output.exists() or output.is_relative_to(private) or private.is_relative_to(output):
        raise ValueError('Use a new private output outside software and source directories')
    if fingerprint()!=json.loads(RUNTIME.read_text()): raise ValueError('Frozen media runtime differs')
    for asset in frozen['plan']['private_files_checked']:
        path=private/('vr-dataset.zip' if asset['id']=='traces' else asset['id']+'.mp4')
        if path.stat().st_size!=asset['bytes'] or sha256(path)!=asset['sha256']:
            raise ValueError('Private original source differs')
    return frozen


def derive(private,output,frozen,progress):
    parent=load_roster(); records={(r['clip'],r['source_id']):r for r in parent['rows']}
    clips=[]
    with zipfile.ZipFile(private/'vr-dataset.zip') as archive:
        validate_archive_directory(archive)
        for selected in frozen['plan']['clips']:
            clip=selected['clip']
            if not selected['eligible']:
                clips.append({**selected,'status':'retained_metadata_exclusion'}); continue
            directory=output/clip; directory.mkdir()
            source=private/(clip+'.mp4'); phase=phase_check(source)
            reference=sample_frames(source); maps=[]; media=[]
            for rung in range(6):
                rendition=directory/f'r{rung}.mp4'; call(encode_command(source,rendition,rung))
                full,_,_=describe(rendition,60,output)
                parents=split_verified(rendition,directory/f'r{rung}_parents',10,60,output)
                for item in parents:
                    item['children']=split_verified(output/item['relative_path'],
                        directory/f'r{rung}_s{item["index"]}_children',2,10,output) if rung>=2 and item['index']>=2 else []
                media.append({'rung':rung,'rendition':full,'parents':parents})
                maps.append(mse_map(reference,sample_frames(rendition)))
                progress({'clip':clip,'rung':rung,'stage':'encoded_remuxed_and_measured'})
            maps=np.stack(maps); map_path=directory/'sender_maps.npz'
            np.savez_compressed(map_path,mse=maps)
            labels=[]
            for identity in selected['source_ids']:
                fields=load_selected(archive,records,clip,identity); status,poses=project_selected(fields)
                if not status['accepted']: raise ValueError('Previously validated pose changed')
                labels.append({'source_id':identity,'parent':aggregate_native(maps,poses,10),
                    'child':aggregate_native(maps,poses,2)})
            label_path=directory/'offline_evaluation_labels.json'
            label_path.write_bytes(canonical({'information_scope':'offline_evaluation_only','rows':labels}))
            clips.append({**selected,'status':'prepared_offline','media':media,'phase_diagnostic':phase,
                'sender_maps_sha256':sha256(map_path),'offline_labels_sha256':sha256(label_path),
                'trace_label_rows':len(labels),'source_sha256':sha256(source)})
    count={'registered_clips':len(clips),'eligible_clips':sum(c['status']=='prepared_offline' for c in clips),
        'directed_pairs':sum(len(c['pairs']) for c in clips),'renditions':sum(len(c.get('media',[])) for c in clips),
        'parents':sum(len(m['parents']) for c in clips for m in c.get('media',[])),
        'recovery_children':sum(len(p['children']) for c in clips for m in c.get('media',[]) for p in m['parents']),
        'trace_label_rows':sum(c.get('trace_label_rows',0) for c in clips)}
    if count!=frozen['plan']['expected']: raise ValueError('Incomplete preparation census')
    return {'schema':'wu-private-preparation-v1','registration_sha256':digest(frozen),'clips':clips,
        'counts':count,'quality_outputs_created':True,'recovery_experiment_performed':False,
        'controller_access_to_future_labels_allowed':False,'runtime':json.loads(RUNTIME.read_text())}


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--private-dir',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--activate-fresh-quality',required=True,help='Exact published registration digest; requires separate author approval')
    a=p.parse_args(); frozen=authorize(a.private_dir,a.output,a.activate_fresh_quality)
    a.output.mkdir(parents=True)
    try:
        with (a.output/'progress.jsonl').open('xb') as f:
            def progress(x): f.write(canonical(x)+b'\n'); f.flush(); print(json.dumps(x),flush=True)
            report=derive(a.private_dir,a.output,frozen,progress)
        (a.output/'manifest.json').write_bytes(canonical(report))
        print(json.dumps({'manifest_sha256':digest(report),'counts':report['counts']}))
    except Exception as e:
        (a.output/'failure.json').write_bytes(canonical({'status':'failed_incomplete','type':type(e).__name__,
            'registration_sha256':digest(frozen),'automatic_retry':False}))
        raise SystemExit('Preparation stopped; partial private files and sanitized progress retained') from None


if __name__=='__main__': main()
