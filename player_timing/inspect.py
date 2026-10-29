"""Read-only inspection of one scheduled browser session and its fixed contract."""
import argparse
import gzip
import json

from player_timing.audit import RAW, audit_session
from player_timing.diagnose import raw_crosschecks, scalar_score
from player_timing.replay import OUT


def inspect_session(index):
    cases = json.loads((OUT / 'schedule.json').read_text())
    if index < 0 or index >= len(cases):
        raise ValueError('Session index must be between 0 and 73')
    case = cases[index]
    with gzip.open(RAW / f'session_{index:02}.json.gz', 'rt') as stream:
        raw = json.load(stream)
    result = audit_session(raw, case)
    if not result['valid']:
        return result
    raw_crosschecks(raw, case)
    first_request = min(r['request'] for r in raw['browser']['receipts']) / 1000
    ends = [r['ended'] / 1000 for r in raw['browser']['segments'][0]]
    parent_rows = []
    for parent, (ideal, measured, gain) in enumerate(zip(
            case['ideal']['parent_ends'], result['ended_score']['parent_ends'], case['parent_gains'])):
        parent_rows.append({'parent': parent + 2, 'ideal_ended_seconds': ideal,
                            'measured_ended_seconds': measured,
                            'available_credit_fraction': gain / case['loss'],
                            'ideal_on_time': ideal <= 40 + 1e-9,
                            'measured_on_time': measured <= 40 + 1e-9})
    return {k: result[k] for k in ('index', 'key', 'scene', 'policy', 'unit_seconds',
                                 'buffered', 'control', 'valid')} | {
        'resource': result['resource'], 'parents': parent_rows,
        'original_parent_account': result['ended_score']['original_parent_account'],
        'secondary_chunk_account': result['ended_score']['secondary_chunk_account'],
        'first_request_offset_ms': first_request * 1000,
        'request_aligned_parent_account': scalar_score(case, [t-first_request for t in ends]),
        'callback_count': result['callback_count'],
        'missing_tail_witnesses': result['missing_tail_witnesses'],
        'scope': 'One exposed software-player session; not a person, physical display or hard timing bound',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--index', type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_session(args.index), indent=2))
