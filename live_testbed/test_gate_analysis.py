"""Tests for the frozen Experiment A metric and inference implementation."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_gate_campaign import (
    BASELINE,
    PRIMARY_METRICS,
    PROPOSED,
    audit_condition,
    holm_adjust,
    primary_tests,
    seed_metrics,
)


def synthetic_audit_condition(condition: str) -> pd.DataFrame:
    rows = []
    for controller in ("conformal_nash", BASELINE, PROPOSED):
        for epoch in range(8):
            for user in range(1, 6):
                rows.append(
                    {
                        "condition": condition,
                        "seed": 1,
                        "controller": controller,
                        "run_epoch": epoch,
                        "user": user,
                        "warmup": 0,
                        "capacity_mbps": 3.0,
                        "segment_number": epoch + 1,
                        "impaired_user": int(
                            condition == "non_actionable" and user == 3
                        ),
                        "capacity_slack_mbps": 0.1,
                        "transfer_censored": 0,
                    }
                )
    return pd.DataFrame(rows)


def synthetic_raw() -> pd.DataFrame:
    rows = []
    for controller, allocation, qoe, stall in [
        (BASELINE, 0.98, 3.0, 4.0),
        (PROPOSED, 0.25, 4.0, 1.0),
    ]:
        for epoch in range(8):
            for user in range(1, 6):
                impaired = int(user == 3)
                rows.append(
                    {
                        "condition": "non_actionable",
                        "seed": 1,
                        "regime": "stable",
                        "controller": controller,
                        "user": user,
                        "warmup": 0,
                        "impaired_user": impaired,
                        "service_ceiling_mbps": 0.18 if impaired else 100.0,
                        "allocated_mbps": allocation if impaired else 0.25,
                        "operational_qoe": qoe if not impaired else 2.0,
                        "debt_before": 2.0,
                        "opportunity_gain": 1.0 if controller == PROPOSED else 0.0,
                        "stall_s": stall if impaired else 0.0,
                        "throughput_mbps": 0.17 if impaired else 0.8,
                        "transfer_censored": 0,
                        "switched": 0,
                        "decision_ms": 50.0,
                    }
                )
    return pd.DataFrame(rows)


def test_seed_metric_definitions():
    metrics = seed_metrics(synthetic_raw()).set_index("controller")
    assert np.isclose(
        metrics.loc[BASELINE, "mean_wasted_allocation_mbps"], 0.80
    )
    assert np.isclose(
        metrics.loc[PROPOSED, "mean_wasted_allocation_mbps"], 0.07
    )
    assert metrics.loc[PROPOSED, "worst_unimpaired_user_mean_operational_qoe"] == 4
    assert metrics.loc[BASELINE, "total_stall_s"] == 32
    assert metrics.loc[PROPOSED, "debt_weighted_opportunity_activation"] == 1


def test_audit_uses_condition_specific_impaired_user_count():
    capacity_audit = audit_condition(
        synthetic_audit_condition("capacity_only")
    )
    non_actionable_audit = audit_condition(
        synthetic_audit_condition("non_actionable")
    )
    assert capacity_audit["passed"]
    assert capacity_audit["expected_impaired_users_per_epoch"] == 0
    assert non_actionable_audit["passed"]
    assert non_actionable_audit["expected_impaired_users_per_epoch"] == 1


def test_capacity_only_seed_metrics_do_not_require_impaired_rows():
    raw = synthetic_raw().copy()
    raw["condition"] = "capacity_only"
    raw["impaired_user"] = 0
    raw["service_ceiling_mbps"] = 100.0
    metrics = seed_metrics(raw)
    assert (metrics["mean_wasted_allocation_mbps"] == 0).all()
    assert metrics["mean_impaired_allocation_mbps"].isna().all()


def test_holm_is_monotone_in_sorted_p_order():
    raw = np.array([0.04, 0.001, 0.02, 0.20])
    adjusted = holm_adjust(raw)
    order = np.argsort(raw)
    assert np.all(np.diff(adjusted[order]) >= -1e-12)
    assert np.all((adjusted >= raw) & (adjusted <= 1))


def test_primary_family_has_exactly_four_paired_tests():
    records = []
    for seed in range(30):
        for controller in (BASELINE, PROPOSED):
            row = {
                "condition": "non_actionable",
                "seed": seed,
                "controller": controller,
            }
            for index, metric in enumerate(PRIMARY_METRICS):
                row[metric] = (
                    float(seed + index)
                    if controller == BASELINE
                    else float(seed + index + 0.25 + 0.01 * seed)
                )
            records.append(row)
    tests = primary_tests(pd.DataFrame(records))
    assert list(tests["metric"]) == PRIMARY_METRICS
    assert (tests["n_pairs"] == 30).all()
    assert tests["p_holm"].between(0, 1).all()
