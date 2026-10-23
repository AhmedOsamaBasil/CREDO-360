"""Paired trace-driven multimedia generalization experiment for CREDO-360."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "live_testbed"))
from portable_qoe import (  # noqa: E402
    PortableEnsemble,
    conformal_radius,
    select_action,
)
from playback_clock import advance_round  # noqa: E402

CONTROLLERS = [
    "mean_nash",
    "conformal_nash",
    "mean_debt_ungated",
    "mean_debt_gated",
    "conformal_debt_ungated",
    "risk_debt",
    "fair_edge_nsw_proxy",
    "aci_nash",
]
LADDER = np.array(
    [0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491]
)
FIELDS = [
    "seed",
    "regime",
    "controller",
    "controller_position",
    "epoch",
    "user",
    "content",
    "subject",
    "split",
    "capacity_mbps",
    "allocated_mbps",
    "segment_bytes",
    "download_s",
    "round_duration_s",
    "throughput_mbps",
    "buffer_before_s",
    "buffer_after_s",
    "stall_s",
    "vw_psnr_db",
    "vw_ssim",
    "viewport_quality_index",
    "decision_predicted_quality",
    "decision_lower_quality",
    "aci_alpha_before",
    "aci_alpha_after",
    "debt_before",
    "debt_after",
    "switched",
]


def capacity_profile(
    regime: str, epochs: int, rng: np.random.Generator
) -> np.ndarray:
    if regime == "stable":
        values = rng.normal(3.0, 0.15, epochs)
    elif regime == "bursty":
        values = np.asarray(
            [
                rng.uniform(1.35, 1.8) if index % 2 else rng.uniform(3.2, 4.2)
                for index in range(epochs)
            ]
        )
    elif regime == "shift":
        midpoint = epochs // 2
        values = np.concatenate(
            [rng.normal(3.6, 0.18, midpoint), rng.normal(1.55, 0.12, epochs - midpoint)]
        )
    else:
        raise ValueError(regime)
    return np.round(np.clip(values, 1.2, 4.5), 3)


def counterbalanced_order(index: int) -> list[str]:
    shift = index % len(CONTROLLERS)
    return CONTROLLERS[shift:] + CONTROLLERS[:shift]


def processor_sharing_completion(
    bits: np.ndarray, capacity_mbps: float
) -> np.ndarray:
    """Exact completion times for simultaneous flows under equal sharing."""
    remaining = np.asarray(bits, dtype=float).copy()
    completion = np.zeros(len(remaining), dtype=float)
    active = np.ones(len(remaining), dtype=bool)
    elapsed = 0.0
    while active.any():
        count = int(active.sum())
        rate_bps = capacity_mbps * 1e6 / count
        delta = float(np.min(remaining[active]) / rate_bps)
        elapsed += delta
        remaining[active] -= rate_bps * delta
        finished = active & (remaining <= 1e-6)
        completion[finished] = elapsed
        active[finished] = False
    return completion


def quality_index(psnr_db: np.ndarray) -> np.ndarray:
    """Declared objective 1--5 index; it is not a subjective MOS mapping."""
    return 1.0 + 4.0 * np.clip((psnr_db - 18.0) / 24.0, 0.0, 1.0)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=Path("multimedia_testbed/artifacts/qoevave"),
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("live_testbed/artifacts/qoe_ensemble.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("multimedia_testbed/results/legacy_transfer_clock_v3"),
    )
    parser.add_argument("--seed", type=int, default=20260760)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--users", type=int, default=5)
    parser.add_argument("--target-quality-index", type=float, default=4.0)
    parser.add_argument("--debt-weight", type=float, default=1.0)
    parser.add_argument("--debt-decay", type=float, default=0.90)
    parser.add_argument("--switch-weight", type=float, default=0.08)
    parser.add_argument("--aci-gamma", type=float, default=0.02)
    parser.add_argument(
        "--allow-legacy-subjective-transfer", action="store_true",
        help="Explicitly run the diagnostic legacy model, whose residuals do not calibrate objective PSNR. Prefer python -m recovery_pilot.run.",
    )
    args = parser.parse_args()
    if not args.allow_legacy_subjective_transfer:
        parser.error("Legacy subjective residuals do not calibrate objective quality. Use python -m recovery_pilot.run, or explicitly opt into this legacy diagnostic.")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Output is nonempty; frozen results must not be overwritten.")

    quality_rows = read_rows(args.artifacts / "viewport_quality.csv")
    size_rows = read_rows(args.artifacts / "segment_sizes.csv")
    quality: dict[tuple[str, int, int, int], tuple[float, float]] = {}
    test_subjects: dict[str, list[int]] = {}
    for row in quality_rows:
        if row["split"] != "test":
            continue
        content = row["content"]
        subject = int(row["subject"])
        test_subjects.setdefault(content, []).append(subject)
        quality[
            (
                content,
                subject,
                int(row["segment"]),
                int(row["ladder_index"]),
            )
        ] = (float(row["vw_psnr_db"]), float(row["vw_ssim"]))
    for content in test_subjects:
        test_subjects[content] = sorted(set(test_subjects[content]))
    sizes = {
        (row["content"], int(row["segment"]), int(row["ladder_index"])): int(
            row["bytes"]
        )
        for row in size_rows
    }
    contents = sorted(test_subjects)
    epochs = 6
    if len(contents) < 6 or any(
        len(value) < args.users for value in test_subjects.values()
    ):
        parser.error("Need six contents and at least one test trace per user")

    model = PortableEnsemble(args.model)
    model_error = model.verify_export()
    payload = model.payload
    template = np.asarray(payload["template_median"], dtype=float)
    radius = conformal_radius(
        payload["calibration"]["one_sided_residuals"],
        float(payload["calibration"]["alpha"]),
    )
    target_alpha = float(payload["calibration"]["alpha"])
    residuals = payload["calibration"]["one_sided_residuals"]
    args.output.mkdir(parents=True, exist_ok=True)
    measurements: list[dict] = []
    plans: list[dict] = []
    regimes = ["stable", "bursty", "shift"]
    for seed_index in range(args.seeds):
        seed = args.seed + seed_index
        rng = np.random.default_rng(seed)
        regime = regimes[seed_index % len(regimes)]
        capacities = capacity_profile(regime, epochs, rng)
        assignments = []
        for user in range(args.users):
            content = contents[(seed_index + user) % len(contents)]
            candidates = test_subjects[content]
            subject = candidates[(seed_index * args.users + user) % len(candidates)]
            assignments.append((content, subject))
        order = counterbalanced_order(seed_index)
        plans.append(
            {
                "seed": seed,
                "regime": regime,
                "capacity_profile_mbps": capacities.tolist(),
                "assignments": [
                    {"user": index + 1, "content": item[0], "subject": item[1]}
                    for index, item in enumerate(assignments)
                ],
                "controller_order": order,
            }
        )
        for position, controller in enumerate(order):
            buffer_s = np.full(args.users, 4.0)
            throughput = np.full(args.users, capacities[0] / args.users)
            previous = np.full(args.users, LADDER[1])
            latency = np.linspace(0.010, 0.034, args.users)
            debt = np.zeros(args.users)
            aci_alpha = np.full(args.users, target_alpha)
            for epoch, capacity in enumerate(capacities):
                alpha_before = aci_alpha.copy()
                controller_radius: float | np.ndarray = radius
                if controller == "aci_nash":
                    controller_radius = np.asarray(
                        [
                            conformal_radius(residuals, float(alpha))
                            for alpha in aci_alpha
                        ]
                    )
                action, decision = select_action(
                    controller,
                    model,
                    template,
                    LADDER,
                    float(capacity),
                    throughput,
                    buffer_s,
                    previous,
                    latency,
                    debt,
                    controller_radius,
                    debt_weight=args.debt_weight,
                    switch_weight=args.switch_weight,
                )
                ladder_indices = np.abs(
                    action[:, None] - LADDER[None, :]
                ).argmin(axis=1)
                segment_bytes = np.asarray(
                    [
                        sizes[(content, epoch, int(ladder_index))]
                        for (content, _), ladder_index in zip(
                            assignments, ladder_indices
                        )
                    ],
                    dtype=float,
                )
                download_s = processor_sharing_completion(
                    8.0 * segment_bytes, float(capacity)
                )
                throughput = 8.0 * segment_bytes / np.maximum(download_s, 1e-9) / 1e6
                buffer_before = buffer_s.copy()
                clock = advance_round(buffer_s, download_s, float(download_s.max()))
                stall, buffer_s = clock.stall_s, clock.buffer_s
                scores = [
                    quality[(content, subject, epoch, int(ladder_index))]
                    for (content, subject), ladder_index in zip(
                        assignments, ladder_indices
                    )
                ]
                psnr = np.asarray([score[0] for score in scores])
                ssim = np.asarray([score[1] for score in scores])
                objective_index = quality_index(psnr)
                selected_mean = np.asarray(
                    decision["selected_mean"], dtype=float
                )
                selected_lower = np.asarray(
                    decision["selected_lower"], dtype=float
                )
                if controller == "aci_nash":
                    miss = (objective_index < selected_lower).astype(float)
                    aci_alpha = np.clip(
                        aci_alpha
                        + args.aci_gamma * (target_alpha - miss),
                        0.01,
                        0.50,
                    )
                debt_before = debt.copy()
                debt = np.maximum(
                    args.debt_decay * debt
                    + args.target_quality_index
                    - objective_index,
                    0.0,
                )
                for user, ((content, subject), ladder_index) in enumerate(
                    zip(assignments, ladder_indices)
                ):
                    measurements.append(
                        {
                            "seed": seed,
                            "regime": regime,
                            "controller": controller,
                            "controller_position": position,
                            "epoch": epoch,
                            "user": user + 1,
                            "content": content,
                            "subject": subject,
                            "split": "test",
                            "capacity_mbps": capacity,
                            "allocated_mbps": action[user],
                            "segment_bytes": int(segment_bytes[user]),
                            "download_s": download_s[user],
                            "round_duration_s": clock.elapsed_s,
                            "throughput_mbps": throughput[user],
                            "buffer_before_s": buffer_before[user],
                            "buffer_after_s": buffer_s[user],
                            "stall_s": stall[user],
                            "vw_psnr_db": psnr[user],
                            "vw_ssim": ssim[user],
                            "viewport_quality_index": objective_index[user],
                            "decision_predicted_quality": selected_mean[user],
                            "decision_lower_quality": selected_lower[user],
                            "aci_alpha_before": alpha_before[user],
                            "aci_alpha_after": aci_alpha[user],
                            "debt_before": debt_before[user],
                            "debt_after": debt[user],
                            "switched": int(action[user] != previous[user]),
                        }
                    )
                previous = action
    with (args.output / "measurements.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(measurements)
    (args.output / "campaign_plan.json").write_text(
        json.dumps(plans, indent=2), encoding="utf-8"
    )
    metadata = {
        "format": "credo360-legacy-subjective-transfer-clock-v3",
        "calibration_warning": "Subjective residuals are not calibrated for the objective target. No objective coverage guarantee.",
        "playback_clock": "Common synchronized clock, including waiting after own completion; no buffer truncation.",
        "seeds": args.seeds,
        "first_seed": args.seed,
        "users": args.users,
        "epochs": epochs,
        "controllers": CONTROLLERS,
        "paired_within_seed": True,
        "user_disjoint_split": "only split=test traces enter outcomes",
        "transport": (
            "exact equal processor-sharing completion times for simultaneous "
            "flows, using measured VBR representation segment sizes"
        ),
        "outcomes": [
            "viewport-weighted luma PSNR from measured held-out HMD traces",
            "viewport-weighted luma SSIM from measured held-out HMD traces",
        ],
        "quality_index": "1 + 4*clip((VW-PSNR-18)/24,0,1); objective, not MOS",
        "component_ablation": {
            "mean_nash": [0, 0, 0],
            "conformal_nash": [1, 0, 0],
            "mean_debt_ungated": [0, 1, 0],
            "mean_debt_gated": [0, 1, 1],
            "conformal_debt_ungated": [1, 1, 0],
            "risk_debt": [1, 1, 1],
            "factor_order": ["calibration", "debt", "opportunity_gate"],
            "structural_aliases_omitted": (
                "gate-on/debt-off cells equal their gate-off counterparts"
            ),
        },
        "recent_method_adaptations": {
            "fair_edge_nsw_proxy": (
                "uncertainty-adjusted Nash-welfare objective aligned with the "
                "FairEdge360 edge reward; not its trained MARL/GNN policy"
            ),
            "aci_nash": (
                "per-user adaptive conformal alpha feedback with Nash welfare; "
                "an executable risk-control comparator, not a reproduction of "
                "the single-user Risk-as-a-Resource viewport model"
            ),
        },
        "portable_model_max_abs_error": model_error,
        "target_quality_index": args.target_quality_index,
        "debt_weight": args.debt_weight,
        "debt_decay": args.debt_decay,
        "switch_weight": args.switch_weight,
        "aci_gamma": args.aci_gamma,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(measurements)} paired measurements to {args.output}")


if __name__ == "__main__":
    main()
