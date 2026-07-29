"""Frozen seed-level analysis for the TMM opportunity-gate experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, wilcoxon


PRIMARY_METRICS = [
    "mean_wasted_allocation_mbps",
    "worst_unimpaired_user_mean_operational_qoe",
    "debt_weighted_opportunity_activation",
    "total_stall_s",
]
PROPOSED = "risk_debt"
BASELINE = "resource_debt_ungated"
EXPECTED_CONTROLLERS = {"conformal_nash", BASELINE, PROPOSED}
EXPECTED_USERS = 5
EXPECTED_ANALYSED_EPOCHS = 8


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    total = len(p_values)
    for rank, index in enumerate(order):
        running = max(running, (total - rank) * p_values[index])
        adjusted[index] = min(running, 1.0)
    return adjusted


def matched_rank_biserial(delta: np.ndarray) -> float:
    nonzero = delta[~np.isclose(delta, 0)]
    if not len(nonzero):
        return 0.0
    ranks = rankdata(np.abs(nonzero))
    return float(
        (ranks[nonzero > 0].sum() - ranks[nonzero < 0].sum()) / ranks.sum()
    )


def paired_bootstrap(
    delta: np.ndarray,
    rng: np.random.Generator,
    draws: int = 10_000,
) -> tuple[float, float]:
    indices = rng.integers(0, len(delta), size=(draws, len(delta)))
    means = delta[indices].mean(axis=1)
    return tuple(float(value) for value in np.quantile(means, [0.025, 0.975]))


def load_condition(specification: str) -> pd.DataFrame:
    try:
        condition, raw_path = specification.split("=", 1)
    except ValueError as error:
        raise ValueError(
            "--condition must use NAME=/path/to/live_measurements.csv"
        ) from error
    frame = pd.read_csv(Path(raw_path))
    frame["condition"] = condition
    required = {
        "seed",
        "regime",
        "impairment",
        "impaired_user",
        "service_ceiling_mbps",
        "controller",
        "run_epoch",
        "epoch",
        "warmup",
        "segment_number",
        "user",
        "capacity_mbps",
        "allocated_mbps",
        "capacity_slack_mbps",
        "throughput_mbps",
        "transfer_censored",
        "stall_s",
        "operational_qoe",
        "debt_before",
        "opportunity_gain",
        "decision_ms",
    }
    missing = sorted(required - set(frame))
    if missing:
        raise ValueError(f"{condition} is missing columns: {missing}")
    if set(frame["impairment"].unique()) != {condition}:
        raise ValueError(
            f"Condition label {condition!r} does not match impairment column"
        )
    return frame


def audit_condition(raw: pd.DataFrame) -> dict:
    condition = str(raw["condition"].iloc[0])
    analysed = raw[raw["warmup"].astype(int) == 0].copy()
    pair_counts = analysed.groupby(["seed", "controller"]).size()
    expected_rows = EXPECTED_USERS * EXPECTED_ANALYSED_EPOCHS
    duplicate_key = [
        "seed",
        "controller",
        "run_epoch",
        "user",
    ]
    profile_capacity = raw.groupby(["seed", "run_epoch"])[
        "capacity_mbps"
    ].nunique()
    profile_segment = raw.groupby(["seed", "run_epoch"])[
        "segment_number"
    ].nunique()
    impaired_per_epoch = analysed.groupby(
        ["seed", "controller", "run_epoch"]
    )["impaired_user"].sum()
    controllers = set(raw["controller"].unique())
    failures = []
    if controllers != EXPECTED_CONTROLLERS:
        failures.append(
            f"controllers={sorted(controllers)}, expected={sorted(EXPECTED_CONTROLLERS)}"
        )
    if not (pair_counts == expected_rows).all():
        failures.append("incomplete seed-controller pair")
    if raw.duplicated(duplicate_key).any():
        failures.append("duplicate seed-controller-epoch-user row")
    if not (profile_capacity == 1).all():
        failures.append("controller capacity-profile mismatch")
    if not (profile_segment == 1).all():
        failures.append("controller segment-profile mismatch")
    if not (impaired_per_epoch == 1).all():
        failures.append("each epoch must identify exactly one impaired user")
    if (analysed["capacity_slack_mbps"] < -1e-9).any():
        failures.append("positive allocation-capacity excess")
    censored = analysed["transfer_censored"].astype(int)
    invalid_censoring = analysed[
        (censored == 1) & (analysed["impaired_user"].astype(int) != 1)
    ]
    if len(invalid_censoring):
        failures.append("censoring observed outside the impaired client")
    return {
        "condition": condition,
        "rows": int(len(raw)),
        "analysed_rows": int(len(analysed)),
        "seeds": int(raw["seed"].nunique()),
        "controllers": sorted(controllers),
        "seed_controller_pairs": int(len(pair_counts)),
        "minimum_analysed_rows_per_pair": int(pair_counts.min()),
        "maximum_analysed_rows_per_pair": int(pair_counts.max()),
        "duplicate_rows": int(raw.duplicated(duplicate_key).sum()),
        "capacity_profile_mismatch_cells": int((profile_capacity != 1).sum()),
        "segment_profile_mismatch_cells": int((profile_segment != 1).sum()),
        "impaired_identity_mismatch_cells": int((impaired_per_epoch != 1).sum()),
        "maximum_capacity_excess_mbps": float(
            max(0.0, -analysed["capacity_slack_mbps"].min())
        ),
        "censored_transfers": int(censored.sum()),
        "censored_unimpaired_transfers": int(len(invalid_censoring)),
        "failures": failures,
        "passed": not failures,
    }


def seed_metrics(raw: pd.DataFrame) -> pd.DataFrame:
    analysed = raw[raw["warmup"].astype(int) == 0].copy()
    records = []
    for (condition, seed, regime, controller), group in analysed.groupby(
        ["condition", "seed", "regime", "controller"],
        sort=True,
    ):
        impaired = group[group["impaired_user"].astype(int) == 1]
        unimpaired = group[group["impaired_user"].astype(int) == 0]
        if len(impaired) != EXPECTED_ANALYSED_EPOCHS:
            raise ValueError(
                f"{condition}/{seed}/{controller}: impaired rows={len(impaired)}"
            )
        user_means = unimpaired.groupby("user")["operational_qoe"].mean()
        debt = group["debt_before"].to_numpy(float)
        active = (group["opportunity_gain"].to_numpy(float) > 1e-9).astype(float)
        impaired_debt = impaired["debt_before"].to_numpy(float)
        impaired_active = (
            impaired["opportunity_gain"].to_numpy(float) > 1e-9
        ).astype(float)
        ceiling = impaired["service_ceiling_mbps"].to_numpy(float)
        allocation = impaired["allocated_mbps"].to_numpy(float)
        records.append(
            {
                "condition": condition,
                "seed": int(seed),
                "regime": regime,
                "controller": controller,
                "mean_wasted_allocation_mbps": float(
                    np.maximum(allocation - ceiling, 0).mean()
                ),
                "worst_unimpaired_user_mean_operational_qoe": float(
                    user_means.min()
                ),
                "debt_weighted_opportunity_activation": float(
                    np.dot(debt, active) / debt.sum() if debt.sum() > 0 else 0.0
                ),
                "total_stall_s": float(group["stall_s"].sum()),
                "impaired_total_stall_s": float(impaired["stall_s"].sum()),
                "censored_transfers": int(
                    group["transfer_censored"].astype(int).sum()
                ),
                "mean_impaired_allocation_mbps": float(allocation.mean()),
                "mean_impaired_throughput_mbps": float(
                    impaired["throughput_mbps"].mean()
                ),
                "mean_unimpaired_operational_qoe": float(
                    unimpaired["operational_qoe"].mean()
                ),
                "impaired_debt_weighted_opportunity_activation": float(
                    np.dot(impaired_debt, impaired_active) / impaired_debt.sum()
                    if impaired_debt.sum() > 0
                    else 0.0
                ),
                "switch_rate": float(group["switched"].mean()),
                "mean_decision_ms": float(group["decision_ms"].mean()),
            }
        )
    return pd.DataFrame.from_records(records)


def aggregate_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    identifiers = {"seed"}
    numeric = [
        column
        for column in metrics.select_dtypes(include=[np.number]).columns
        if column not in identifiers
    ]
    records = []
    for (condition, controller), group in metrics.groupby(
        ["condition", "controller"], sort=True
    ):
        for metric in numeric:
            values = group[metric].to_numpy(float)
            standard_error = (
                values.std(ddof=1) / np.sqrt(len(values))
                if len(values) > 1
                else np.nan
            )
            records.append(
                {
                    "condition": condition,
                    "controller": controller,
                    "metric": metric,
                    "n": len(values),
                    "mean": values.mean(),
                    "std": values.std(ddof=1) if len(values) > 1 else np.nan,
                    "ci95_low": values.mean() - 1.96 * standard_error,
                    "ci95_high": values.mean() + 1.96 * standard_error,
                }
            )
    return pd.DataFrame.from_records(records)


def primary_tests(metrics: pd.DataFrame) -> pd.DataFrame:
    target = metrics[metrics["condition"] == "non_actionable"]
    proposed = target[target["controller"] == PROPOSED].set_index("seed")
    baseline = target[target["controller"] == BASELINE].set_index("seed")
    common = proposed.index.intersection(baseline.index).sort_values()
    if len(common) != 30:
        raise ValueError(f"Primary analysis requires 30 paired seeds, found {len(common)}")
    rng = np.random.default_rng(20260729)
    records = []
    for metric in PRIMARY_METRICS:
        proposed_values = proposed.loc[common, metric].to_numpy(float)
        baseline_values = baseline.loc[common, metric].to_numpy(float)
        delta = proposed_values - baseline_values
        if np.allclose(delta, 0):
            statistic, p_value = 0.0, 1.0
        else:
            result = wilcoxon(
                proposed_values,
                baseline_values,
                alternative="two-sided",
                zero_method="wilcox",
            )
            statistic, p_value = float(result.statistic), float(result.pvalue)
        interval = paired_bootstrap(delta, rng)
        records.append(
            {
                "condition": "non_actionable",
                "metric": metric,
                "n_pairs": len(common),
                "proposed": PROPOSED,
                "baseline": BASELINE,
                "proposed_mean": proposed_values.mean(),
                "baseline_mean": baseline_values.mean(),
                "mean_paired_delta": delta.mean(),
                "median_paired_delta": np.median(delta),
                "bootstrap_ci95_low": interval[0],
                "bootstrap_ci95_high": interval[1],
                "wilcoxon_statistic": statistic,
                "p_raw": p_value,
                "rank_biserial": matched_rank_biserial(delta),
            }
        )
    frame = pd.DataFrame.from_records(records)
    frame["p_holm"] = holm_adjust(frame["p_raw"].to_numpy(float))
    return frame


def condition_interactions(metrics: pd.DataFrame) -> pd.DataFrame:
    if set(metrics["condition"].unique()) != {"capacity_only", "non_actionable"}:
        return pd.DataFrame()
    rng = np.random.default_rng(20260730)
    records = []
    for metric in PRIMARY_METRICS:
        pivot = metrics[metrics["controller"].isin([PROPOSED, BASELINE])].pivot(
            index="seed",
            columns=["condition", "controller"],
            values=metric,
        )
        required = [
            ("non_actionable", PROPOSED),
            ("non_actionable", BASELINE),
            ("capacity_only", PROPOSED),
            ("capacity_only", BASELINE),
        ]
        complete = pivot.dropna(subset=required)
        interaction = (
            complete[("non_actionable", PROPOSED)]
            - complete[("non_actionable", BASELINE)]
            - complete[("capacity_only", PROPOSED)]
            + complete[("capacity_only", BASELINE)]
        ).to_numpy(float)
        interval = paired_bootstrap(interaction, rng)
        records.append(
            {
                "metric": metric,
                "n_pairs": len(interaction),
                "mean_difference_in_differences": interaction.mean(),
                "bootstrap_ci95_low": interval[0],
                "bootstrap_ci95_high": interval[1],
                "rank_biserial": matched_rank_biserial(interaction),
            }
        )
    return pd.DataFrame.from_records(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--condition",
        action="append",
        required=True,
        help="Condition and CSV as NAME=/path/to/live_measurements.csv",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    conditions = [load_condition(specification) for specification in args.condition]
    audits = [audit_condition(frame) for frame in conditions]
    if any(not audit["passed"] for audit in audits):
        raise RuntimeError(f"Campaign audit failed: {audits}")
    raw = pd.concat(conditions, ignore_index=True)
    metrics = seed_metrics(raw)
    aggregate = aggregate_metrics(metrics)
    tests = primary_tests(metrics)
    interactions = condition_interactions(metrics)

    args.output.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.output / "gate_seed_metrics.csv", index=False)
    aggregate.to_csv(args.output / "gate_aggregate_metrics.csv", index=False)
    tests.to_csv(args.output / "gate_primary_tests.csv", index=False)
    if not interactions.empty:
        interactions.to_csv(
            args.output / "gate_condition_interactions.csv", index=False
        )
    (args.output / "gate_campaign_audit.json").write_text(
        json.dumps(audits, indent=2),
        encoding="utf-8",
    )
    (args.output / "gate_analysis_metadata.json").write_text(
        json.dumps(
            {
                "primary_metrics": PRIMARY_METRICS,
                "proposed": PROPOSED,
                "baseline": BASELINE,
                "warmup_excluded": True,
                "bootstrap_draws": 10_000,
                "bootstrap_seed": 20260729,
                "multiple_testing": "Holm across exactly four primary outcomes",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(tests.to_string(index=False))


if __name__ == "__main__":
    main()
