"""Inspect exact endpoint evidence without altering frozen preparation code."""
from fractions import Fraction
import hashlib
from pathlib import Path
from wu_pipeline.media import encode_command, timeline
from wu_pipeline.spec import verify, digest, ROOT

PACKAGE = Path(__file__).resolve().parent


def bounded_command(source, target, rung, seconds=60):
    """Proposed amendment only; not wired into the real-source runner."""
    if type(seconds) is not int or seconds <= 0:
        raise ValueError('Positive integer duration required')
    original = encode_command(source, target, rung, seconds)
    return original[:-1] + ['-frames:v', str(seconds * 30), original[-1]]


def endpoint(info, seconds=60):
    if len(info['streams']) != 1 or not info['packets']:
        raise ValueError('Nonempty single-stream probe required')
    stream = info['streams'][0]
    packets = sorted(info['packets'], key=lambda p: int(p['pts']))
    tb = Fraction(stream['time_base'])
    pts = [int(p['pts']) * tb for p in packets]
    durations = [int(p['duration']) * tb for p in packets]
    try:
        timeline(info, seconds)
        error = None
    except ValueError as exc:
        error = str(exc)
    return {
        'packets': len(packets), 'expected_packets': seconds * 30,
        'stream_start': str(Fraction(stream['start_time'])),
        'first_pts': str(pts[0]), 'last_pts': str(pts[-1]),
        'presentation_end': str(pts[-1] + durations[-1]),
        'container_duration': info['format']['duration'],
        'uniform_grid': all(t == Fraction(i, 30) for i, t in enumerate(pts)),
        'uniform_duration': all(d == Fraction(1, 30) for d in durations),
        'packets_at_or_after_limit': sum(t >= seconds for t in pts),
        'frozen_validation_pass': error is None, 'validation_error': error,
    }


def bindings():
    files = ('__init__.py', 'core.py', 'run.py', 'test_boundary.py', 'PROTOCOL.md')
    return {'original_registration_sha256': digest(verify()), 'sources': {
        'wu_boundary/' + name: hashlib.sha256(
            (PACKAGE / name).read_text(encoding='utf-8').replace('\r\n', '\n').encode()
        ).hexdigest() for name in files}}


def private_new_output(directory):
    directory = directory.resolve()
    if directory.exists() or directory.is_relative_to(ROOT.resolve()) or ROOT.resolve().is_relative_to(directory):
        raise ValueError('New private output outside software required')
    return directory
