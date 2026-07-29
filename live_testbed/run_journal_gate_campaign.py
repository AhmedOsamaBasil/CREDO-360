"""Run both frozen TMM gate-identification conditions sequentially."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


CONTROLLERS = [
    "conformal_nash",
    "resource_debt_ungated",
    "risk_debt",
]
CONDITIONS = ["non_actionable", "capacity_only"]


def experiment_command(
    script: Path,
    model: Path,
    media_root: Path,
    output: Path,
    condition: str,
) -> list[str]:
    return [
        sys.executable,
        str(script),
        "--model",
        str(model),
        "--media-root",
        str(media_root),
        "--output",
        str(output),
        "--controllers",
        *CONTROLLERS,
        "--users",
        "5",
        "--epochs",
        "8",
        "--warmup-epochs",
        "1",
        "--seed",
        "20260730",
        "--seeds",
        "30",
        "--regimes",
        "stable",
        "bursty",
        "shift",
        "--target-qoe",
        "4.0",
        "--debt-weight",
        "1.0",
        "--debt-decay",
        "0.90",
        "--switch-weight",
        "0.08",
        "--impairment",
        condition,
        "--resume",
    ]


def analysis_commands(
    analysis_python: Path,
    script_root: Path,
    output_root: Path,
) -> list[list[str]]:
    analysis_output = output_root / "journal_gate_analysis"
    capacity = output_root / "journal_gate_capacity_30seed" / "live_measurements.csv"
    non_actionable = (
        output_root
        / "journal_gate_nonactionable_30seed"
        / "live_measurements.csv"
    )
    return [
        [
            str(analysis_python),
            str(script_root / "analyze_gate_campaign.py"),
            "--condition",
            f"capacity_only={capacity}",
            "--condition",
            f"non_actionable={non_actionable}",
            "--output",
            str(analysis_output),
        ],
        [
            str(analysis_python),
            str(script_root / "plot_gate_campaign.py"),
            "--metrics",
            str(analysis_output / "gate_seed_metrics.csv"),
            "--tests",
            str(analysis_output / "gate_primary_tests.csv"),
            "--output",
            str(analysis_output / "gate_primary_outcomes.png"),
        ],
    ]


def write_status(path: Path, status: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2), encoding="utf-8")


def main() -> None:
    if os.geteuid() != 0:
        raise SystemExit("Run as root; Mininet requires root.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--media-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--analysis-python",
        type=Path,
        default=Path(sys.executable),
        help="Python interpreter containing pandas, SciPy, and Matplotlib.",
    )
    args = parser.parse_args()

    script_root = Path(__file__).resolve().parent
    script = script_root / "run_mininet_experiment.py"
    status_path = args.output_root / "journal_gate_orchestration.json"
    status = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "completed_utc": None,
        "condition_order": CONDITIONS,
        "controllers": CONTROLLERS,
        "parameters": {
            "users": 5,
            "warmup_epochs": 1,
            "analysed_epochs": 8,
            "first_seed": 20260730,
            "seeds": 30,
            "regimes": ["stable", "bursty", "shift"],
            "target_qoe": 4.0,
            "debt_weight": 1.0,
            "debt_decay": 0.90,
            "switch_weight": 0.08,
        },
        "conditions": {},
    }
    write_status(status_path, status)

    output_names = {
        "non_actionable": "journal_gate_nonactionable_30seed",
        "capacity_only": "journal_gate_capacity_30seed",
    }
    for condition in CONDITIONS:
        output = args.output_root / output_names[condition]
        status["conditions"][condition] = {
            "status": "running",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "output": str(output),
        }
        write_status(status_path, status)
        subprocess.run(["mn", "-c"], check=True)
        try:
            subprocess.run(
                experiment_command(
                    script,
                    args.model,
                    args.media_root,
                    output,
                    condition,
                ),
                check=True,
            )
        except BaseException:
            status["conditions"][condition]["status"] = "failed_or_interrupted"
            status["conditions"][condition][
                "stopped_utc"
            ] = datetime.now(timezone.utc).isoformat()
            write_status(status_path, status)
            raise
        status["conditions"][condition]["status"] = "complete"
        status["conditions"][condition][
            "completed_utc"
        ] = datetime.now(timezone.utc).isoformat()
        write_status(status_path, status)

    status["analysis"] = {
        "status": "running",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": str(args.analysis_python),
    }
    write_status(status_path, status)
    try:
        for command in analysis_commands(
            args.analysis_python,
            script_root,
            args.output_root,
        ):
            subprocess.run(command, check=True)
    except BaseException:
        status["analysis"]["status"] = "failed_or_interrupted"
        status["analysis"]["stopped_utc"] = datetime.now(timezone.utc).isoformat()
        write_status(status_path, status)
        raise
    status["analysis"]["status"] = "complete"
    status["analysis"]["completed_utc"] = datetime.now(timezone.utc).isoformat()
    status["completed_utc"] = datetime.now(timezone.utc).isoformat()
    write_status(status_path, status)
    print(status_path)


if __name__ == "__main__":
    main()
