"""Tests for target identity, simultaneous gain envelopes and physical clocks."""

from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pytest

from live_testbed.playback_clock import advance_idle, advance_round
from recovery_pilot.core import (
    CONTROLLERS, Catalogue, ObjectiveModel, finite_quantile, recovery_terms,
    select_action, shortfall, subject_partition,
)
from recovery_pilot.run import longest_run, processor_sharing
from recovery_pilot.audit_results import canonical_text_hash, verify_input_bytes


def test_input_provenance_accepts_only_git_line_ending_changes():
    import hashlib
    original = b"a,b\r\n1,2\r\n"
    expected = hashlib.sha256(original).hexdigest()
    record = {"original_raw_sha256": expected, "canonical_lf_sha256": canonical_text_hash(original)}
    assert verify_input_bytes(original, expected, record) == "byte_exact"
    assert verify_input_bytes(b"a,b\n1,2\n", expected, record) == "git_line_endings_only"
    with pytest.raises(AssertionError):
        verify_input_bytes(b"a,b\n1,3\n", expected, record)


def test_normalized_provenance_must_be_bound_to_original_hash():
    with pytest.raises(AssertionError):
        verify_input_bytes(b"a\n", "unrelated", {"original_raw_sha256": "different", "canonical_lf_sha256": canonical_text_hash(b"a\n")})


def test_waiting_after_own_completion_can_cause_stall():
    step = advance_round(np.array([4., 4.]), np.array([1., 20.]), 20.)
    assert np.allclose(step.buffer_s, [0, 10])
    assert np.allclose(step.stall_s, [6, 16])


def test_time_conservation_including_censoring_and_idle():
    rng = np.random.default_rng(16)
    for _ in range(100):
        before = rng.uniform(0, 40, 5)
        arrivals = rng.uniform(0, 50, 5)
        end = arrivals.max() + 0.1
        success = rng.random(5) > 0.3
        step = advance_round(before, arrivals, end, delivered=success)
        assert np.allclose(before + 10 * success + step.stall_s, end + step.buffer_s)
        idle = advance_idle(step.buffer_s, 0.4)
        assert np.allclose(step.buffer_s + idle.stall_s, 0.4 + idle.buffer_s)


def test_clock_never_discards_buffer_time():
    step = advance_round(np.array([30.]), np.array([1.]), 1.)
    assert step.buffer_s[0] == 39


@pytest.mark.parametrize("completion,end", [([-1], 2), ([3], 2), ([float('nan')], 2), ([1], -1)])
def test_invalid_clock_inputs_rejected(completion, end):
    with pytest.raises(ValueError):
        advance_round(np.array([4.]), np.array(completion), end)


def test_finite_sample_quantile_not_interpolated_or_clipped_to_max_when_invalid():
    radius, rank, trivial = finite_quantile(np.arange(9) / 10)
    assert (radius, rank, trivial) == (0.8, 9, False)
    assert finite_quantile(np.array([0.1, 0.2])) == (6.0, 3, True)


def test_subject_partition_disjoint_stable_and_id_level():
    split = subject_partition(list(range(1, 29)))
    assert split == subject_partition(list(reversed(range(1, 29))))
    assert [len(split[k]) for k in ("train", "calibration", "test")] == [10, 9, 9]
    assert len(set(sum(split.values(), []))) == 28


def test_direct_gain_envelope_covers_every_pair_when_score_is_bounded():
    rng = np.random.default_rng(27)
    for _ in range(30):
        mean, actual = rng.uniform(1, 5, (2, 4, 6))
        errors = shortfall(mean) - shortfall(actual)
        radius = np.ptp(errors, axis=1).max()
        for reference, action in itertools.product(range(6), repeat=2):
            prediction = shortfall(mean[:, reference]) - shortfall(mean[:, action])
            realization = shortfall(actual[:, reference]) - shortfall(actual[:, action])
            assert np.all(realization >= prediction - radius - 1e-12)


def test_difference_of_lower_bounds_is_not_a_gain_bound():
    # Both individual lower bounds are valid, yet their difference is optimistic.
    assert 3.6 >= 3.5 and 4.0 >= 2.5
    assert 3.6 - 4.0 < 3.5 - 2.5


def test_old_gate_is_constant_shift_even_with_plateaus():
    lower = np.array([[1., 2.], [2., 3.], [2., 3.]])
    weights = np.array([2., 1.])
    gated = (weights * np.maximum(lower - lower[0], 0)).sum(axis=1)
    ungated = (weights * lower).sum(axis=1)
    assert np.allclose(ungated - gated, ungated[0])


def test_recovery_is_bounded_by_debt_and_zero_above_service_floor():
    mean = np.array([[1., 2., 3., 4., 4.5, 5.], [4., 4.1, 4.2, 4.3, 4.5, 5.]])
    gain, credit = recovery_terms(mean, 0.2, np.array([0.5, 5.]))
    assert np.all(credit[0] <= 0.5)
    assert np.all(credit[1] == 0)
    assert credit[0, 0] == 0 and gain[0, 0] < 0


def test_new_recovery_score_not_an_absolute_quality_constant_shift():
    mean = np.array([[1., 2., 3., 4., 4.5, 5.]])
    _, credit = recovery_terms(mean, 0.2, np.array([1.]))
    assert np.ptp(mean - credit) > 0.5


def test_optimizer_matches_brute_force_and_permutation_for_unique_optimum():
    rng = np.random.default_rng(155)
    mean = rng.uniform(1.1, 4.9, (3, 6))
    costs = np.tile(np.array([1., 2., 3., 5., 8., 13.]), (3, 1))
    debt, last, previous = np.array([2., 1., 3.]), np.ones(3), np.array([1, 2, 3])
    for controller in CONTROLLERS:
        chosen, info = select_action(controller, mean, 0.2, costs, 15., debt, last, previous)
        assert costs[np.arange(3), chosen].sum() <= 15.
        permutation = np.array([2, 0, 1])
        permuted, _ = select_action(controller, mean[permutation], 0.2, costs[permutation], 15., debt[permutation], last[permutation], previous[permutation])
        assert np.array_equal(chosen[permutation], permuted)
        if controller == "bounded_quality_debt":
            lower = np.maximum(1, mean - 0.2)
            weights = debt / (1 + debt.mean())
            from recovery_pilot.core import LADDER
            best = -np.inf
            for action in itertools.product(range(6), repeat=3):
                action = np.array(action)
                if costs[np.arange(3), action].sum() > 15:
                    continue
                value = np.sum(np.log(lower[np.arange(3), action]) + weights * lower[np.arange(3), action])
                value -= 0.08 * np.mean(np.abs(np.log((LADDER[action] + 0.05) / (LADDER[previous] + 0.05))))
                best = max(best, value)
            assert info["objective"] == pytest.approx(best)


def test_infeasible_admission_is_not_silently_reported_feasible():
    with pytest.raises(ValueError, match="no feasible"):
        select_action("quality_nash", np.full((2, 6), 3.), 0.2, np.ones((2, 6)), 1., np.zeros(2), np.zeros(2), np.zeros(2, int))


def test_fluid_completion_and_time_conservation():
    result = processor_sharing(np.array([1e6, 2e6]), 1.)
    assert np.allclose(result, [2., 3.])
    assert result.max() == pytest.approx(3.)


def test_longest_deprivation_is_temporal_not_just_a_count():
    assert longest_run(np.array([1, 1, 0, 1, 1, 1, 0], bool)) == 3


def test_objective_model_never_fits_test_labels():
    subjects = list(range(1, 29))
    rng = np.random.default_rng(28)
    q = rng.uniform(1, 5, (28, 2, 6))
    cat = Catalogue(subjects, [("a", 0), ("a", 1)], q, q.copy(), q.copy(), np.ones((2, 6)))
    model = ObjectiveModel.fit(cat)
    for sid in model.partition["test"]:
        cat.quality[subjects.index(sid)] = 5
    other = ObjectiveModel.fit(cat)
    assert np.array_equal(other.mean, model.mean)
    assert other.scores == model.scores and other.radius == model.radius


def test_real_artifact_schema_and_split_without_outcome_selection():
    root = Path(__file__).resolve().parents[1] / "multimedia_testbed/artifacts/qoevave"
    catalogue = Catalogue.load(root)
    assert catalogue.quality.shape == (28, 36, 6)
    assert np.all((catalogue.quality >= 1) & (catalogue.quality <= 5))
    assert np.all(catalogue.sizes > 0)
