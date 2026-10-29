"""Offline replay of a metadata-only source assessment; no network or poses."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from source_preflight.wu_probe import CORRECTION, canonical

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
OUT = PACKAGE / 'results/preflight_v1'
OWN = ('__init__.py', 'intake.py', 'wu_probe.py', 'audit.py', 'test_intake.py',
       'test_wu_probe.py', 'test_audit.py', 'source_review.json', 'README.md')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def check(value, message):
    if not value:
        raise ValueError(message)


def summarize(access, review):
    expected = [(e, n) for e in (1, 2) for n in range(1, 10)]
    records, heads = access['records'], access['video_head_checks']
    check([(r['experiment'], r['video']) for r in records] == expected, 'Incomplete ordered source catalogue')
    check([(r['experiment'], r['video']) for r in heads] == expected, 'Incomplete ordered HEAD checks')
    for key in ('trace_members_opened', 'demographic_members_opened', 'video_bodies_downloaded', 'fresh_quality_or_recovery_outcomes'):
        check(access[key] == 0, 'Assessment exceeded metadata scope')
    check(all(h['method'] == 'HEAD' and h['body_downloaded'] is False
              and h['media_verified'] is False for h in heads), 'HEAD evidence promoted')
    check(records[-1]['effective_stimulus_link'] == CORRECTION
          and records[-1]['correction_source'] == 'https://wuchlei-thu.github.io/', 'Missing author correction')
    check(records[-1]['original_stimulus_link'] == records[-2]['original_stimulus_link'], 'Original duplicate changed')
    check(len({r['effective_stimulus_link'] for r in records}) == 18, 'Duplicate effective stimulus')
    check(review['source_adapter_frozen'] is False and review['manuscript_changed'] is False, 'Unsupported progression')
    reachable = [h for h in heads if h.get('status') == 200 and h.get('bytes', 0) > 0]
    return {'state': 'blocked_before_outcomes', 'recommended_next_source': 'wu2017',
        'catalogue_records': len(records), 'condition_counts': dict(Counter(str(r['experiment']) for r in records)),
        'successful_head_responses': len(reachable),
        'advertised_stimulus_bytes': sum(h['bytes'] for h in reachable),
        'official_corrections_applied': [{'experiment': 2, 'video': 9}],
        'source_adapter_frozen': False, 'new_empirical_outcomes': 0,
        'remaining_checks': ['private original-file acquisition and SHA-256 binding',
            'decoded PTS, source interval and geometry/landmark validation',
            'timestamp-and-ID-only eligibility and separate condition strata',
            'reuse basis, source-specific adapter freeze and independent checks'],
        'limitations': ['HEAD is not media validation', 'directory hash is not complete archive hash',
            'synthetic intake checks do not establish real-source alignment',
            'no participant-trace eligibility has been measured',
            'no positive feasibility or improved recovery result is established']}


def report():
    access = read(PACKAGE / 'results/access_v1/wu_metadata.json')
    review = read(PACKAGE / 'source_review.json')
    design = read(ROOT / 'confirmation_protocol/design.json')
    registration = read(ROOT / 'confirmation_protocol/results/design_v1/registration.json')
    check(digest(design) == registration['design_sha256'], 'Frozen design changed')
    return {'schema': 'external-source-preflight-v1', 'summary': summarize(access, review),
        'access_sha256': digest(access), 'review_sha256': digest(review),
        'design_sha256': digest(design),
        'source_sha256': {name: hashlib.sha256((PACKAGE / name).read_text(encoding='utf-8').replace('\r\n', '\n').encode()).hexdigest() for name in OWN}}


def main():
    parser = argparse.ArgumentParser(__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze', action='store_true')
    group.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.freeze:
        OUT.mkdir(parents=True, exist_ok=False)
        (OUT / 'report.json').write_bytes(canonical(result))
        (OUT / 'metadata.json').write_bytes(canonical({'sha256': digest(result)}))
    else:
        check(result == read(OUT / 'report.json'), 'Source assessment changed')
        check(digest(result) == read(OUT / 'metadata.json')['sha256'], 'Assessment hash mismatch')
    print(json.dumps({'sha256': digest(result), 'summary': result['summary']}))


if __name__ == '__main__':
    main()
