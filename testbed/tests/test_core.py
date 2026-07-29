import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calibration import AdaptiveConformal, conformal_quantile
from run_experiment import cvar


def test_conformal_quantile_is_finite():
    assert conformal_quantile(np.array([0.1, 0.2, 0.3]), 0.1) == 0.3


def test_adaptive_calibrator_updates_window():
    calibrator = AdaptiveConformal.fit(
        np.array([0.1, 0.2]),
        np.array([0, 0]),
        alpha=0.1,
        window=2,
    )
    calibrator.update(np.array([0]), np.array([0.9]))
    assert calibrator.buckets[0] == [0.2, 0.9]


def test_new_regime_inherits_pooled_history():
    calibrator = AdaptiveConformal.fit(
        np.array([0.1, 0.2, 0.3]),
        np.array([0, 0, 0]),
        alpha=0.1,
        window=4,
    )
    calibrator.update(np.array([1]), np.array([0.4]))
    assert calibrator.buckets[1] == [0.1, 0.2, 0.3, 0.4]


def test_cvar_selects_lower_tail():
    assert cvar(np.arange(1, 11), 0.2) == 1.5
