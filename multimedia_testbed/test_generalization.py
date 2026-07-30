from __future__ import annotations

import numpy as np

from prepare_qoevave import (
    subject_split,
    tile_mse,
    tile_ssim,
    viewport_weights,
)
from analyze_generalization import holm, jain, rank_biserial
from run_generalization import processor_sharing_completion, quality_index


def test_subject_split_is_stable_and_nonempty():
    first = [subject_split(value) for value in range(1, 49)]
    second = [subject_split(value) for value in range(1, 49)]
    assert first == second
    assert set(first) == {"calibration", "test"}


def test_viewport_weights_wrap_and_normalize():
    west = viewport_weights(-179.0, 0.0)
    east = viewport_weights(179.0, 0.0)
    assert np.isclose(west.sum(), 1.0)
    assert np.isclose(east.sum(), 1.0)
    assert np.sum(np.minimum(west, east)) > 0.5


def test_tile_mse_preserves_grid():
    reference = np.zeros((2, 480, 960), dtype=np.float32)
    distorted = np.ones_like(reference) * 3
    result = tile_mse(reference, distorted)
    assert result.shape == (2, 6, 12)
    assert np.allclose(result, 9.0)


def test_tile_ssim_is_one_for_identical_frames_and_bounded():
    reference = np.arange(480 * 960, dtype=np.float32).reshape(
        1, 480, 960
    ) % 255
    identical = tile_ssim(reference, reference)
    shifted = tile_ssim(reference, np.clip(reference + 20, 0, 255))
    assert identical.shape == (1, 6, 12)
    assert np.allclose(identical, 1.0)
    assert np.all((-1.0 <= shifted) & (shifted <= 1.0))
    assert np.mean(shifted) < 1.0


def test_processor_sharing_completion():
    result = processor_sharing_completion(
        np.array([1e6, 2e6]), capacity_mbps=1.0
    )
    # Both receive 0.5 Mb/s for 2 s, then the larger flow receives 1 Mb/s.
    assert np.allclose(result, [2.0, 3.0])


def test_quality_index_is_bounded_and_monotonic():
    values = quality_index(np.array([10.0, 18.0, 30.0, 42.0, 60.0]))
    assert np.all(np.diff(values) >= 0)
    assert np.allclose(values[[0, -1]], [1.0, 5.0])


def test_analysis_helpers():
    assert np.isclose(jain(np.array([2.0, 2.0, 2.0])), 1.0)
    assert holm([0.01, 0.04, 0.20]) == [0.03, 0.08, 0.2]
    assert rank_biserial(np.array([1.0, 2.0, 3.0])) == 1.0
    assert np.isclose(
        rank_biserial(np.array([1.0, 1.0, -1.0])), 1.0 / 3.0
    )
