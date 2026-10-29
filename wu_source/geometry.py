"""Synthetic/source convention checks; no participant loader or default UV sign."""
import math


def forward_xyzw(q):
    if len(q) != 4 or not all(math.isfinite(v) for v in q):
        raise ValueError('Four finite quaternion components required')
    norm = sum(v * v for v in q)
    if abs(norm - 1) > 1e-6:
        raise ValueError('Unit quaternion required; no silent normalization')
    x, y, z, w = q
    return (2 * x * z + 2 * y * w,
            2 * y * z - 2 * x * w, 1 - 2 * x * x - 2 * y * y)


def candidate_uv(vector, *, wrap_sign):
    """Unverified texture candidate, never a default production adapter."""
    if type(wrap_sign) is not int or wrap_sign not in (-1, 1):
        raise ValueError('Explicit candidate sign required')
    if len(vector) != 3 or not all(math.isfinite(v) for v in vector):
        raise ValueError('Finite vector required')
    if abs(sum(v * v for v in vector) - 1) > 1e-6:
        raise ValueError('Unit vector required')
    x, y, z = vector
    return ((wrap_sign * math.atan2(z, x) / (2 * math.pi)) % 1,
            math.acos(max(-1, min(1, y))) / math.pi)
