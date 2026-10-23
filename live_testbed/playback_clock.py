"""Playback accounting on a common clock, including synchronization waiting.

Completion times are measured from the round's playback boundary, not merely
the network-transfer start. A completed segment is inserted at its completion
time. Playback then continues until the common next-round boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PlaybackStep:
    buffer_s: np.ndarray
    stall_s: np.ndarray
    elapsed_s: float


def advance_round(
    buffer_s: np.ndarray,
    completion_s: np.ndarray,
    end_s: float,
    segment_s: float = 10.0,
    delivered: np.ndarray | None = None,
) -> PlaybackStep:
    """Advance one synchronized round without discarding buffered media.

    With B initial buffer, D delivered duration and S stall, conservation is
    B + D + S = end_s + final_buffer. Even a fast client can stall while it
    waits for the slowest client *after* receiving its own segment.
    """
    buffers = np.asarray(buffer_s, dtype=float)
    arrivals = np.asarray(completion_s, dtype=float)
    success = np.ones(buffers.shape, dtype=bool) if delivered is None else np.asarray(delivered, dtype=bool)
    if buffers.ndim != 1 or arrivals.shape != buffers.shape or success.shape != buffers.shape:
        raise ValueError("buffer, completion and delivered must be matching vectors")
    if not np.isfinite(end_s) or end_s < 0 or not np.isfinite(segment_s) or segment_s <= 0:
        raise ValueError("invalid round or segment duration")
    if (not np.all(np.isfinite(buffers)) or not np.all(np.isfinite(arrivals))
            or np.any(buffers < 0) or np.any(arrivals < 0) or np.any(arrivals > end_s + 1e-9)):
        raise ValueError("invalid buffer or completion timestamp")
    arrivals = np.minimum(arrivals, end_s)
    before_stall = np.maximum(arrivals - buffers, 0)
    after_arrival = np.maximum(buffers - arrivals, 0) + segment_s * success
    waiting = end_s - arrivals
    after_stall = np.maximum(waiting - after_arrival, 0)
    return PlaybackStep(
        np.maximum(after_arrival - waiting, 0),
        before_stall + after_stall,
        float(end_s),
    )


def advance_idle(buffer_s: np.ndarray, elapsed_s: float) -> PlaybackStep:
    """Account for controller/logging/setup time without inserting a segment."""
    buffers = np.asarray(buffer_s, dtype=float)
    return advance_round(buffers, np.full(buffers.shape, elapsed_s), elapsed_s,
                         delivered=np.zeros(buffers.shape, dtype=bool))
