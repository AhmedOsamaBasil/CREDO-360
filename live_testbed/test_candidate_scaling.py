"""Journal-extension tests for deterministic scalable action construction."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from portable_qoe import candidate_allocations


LADDER = np.array([0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491])


def test_large_action_cover_is_feasible_and_bounded():
    for users in (5, 10, 20, 30):
        capacity = max(LADDER[0] * users, 0.75 * users)
        actions = candidate_allocations(LADDER, users, capacity)
        assert 1 <= len(actions) <= 384
        assert actions.shape[1] == users
        assert np.all(actions.sum(axis=1) <= capacity + 1e-9)
        assert np.all(np.isin(actions, LADDER))


def test_large_action_cover_is_deterministic():
    first = candidate_allocations(LADDER, 20, 15.0)
    second = candidate_allocations(LADDER, 20, 15.0)
    np.testing.assert_array_equal(first, second)


def test_below_minimum_capacity_is_rejected():
    try:
        candidate_allocations(LADDER, 10, LADDER[0] * 10 - 0.01)
    except ValueError as error:
        assert "minimum feasible allocation" in str(error)
    else:
        raise AssertionError("Expected infeasible capacity to be rejected")
