"""Tests for the frozen two-condition journal campaign orchestrator."""

import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_journal_gate_campaign as campaign
from run_journal_gate_campaign import (
    CONTROLLERS,
    analysis_commands,
    experiment_command,
)
from run_mininet_experiment import (
    IMPAIRED_RATE_MBPS,
    LADDER_BPS,
    PROCESS_TIMEOUT_S,
    SEGMENT_DURATION_S,
    TRANSFER_TIMEOUT_S,
    parse_curl_measurement,
)


def test_frozen_command_contains_both_pairing_and_analysis_parameters():
    command = experiment_command(
        Path("run_mininet_experiment.py"),
        Path("model.json"),
        Path("Segments"),
        Path("results"),
        "non_actionable",
    )
    assert command[0] == sys.executable
    assert command[command.index("--controllers") + 1 : command.index("--users")] == (
        CONTROLLERS
    )
    assert command[command.index("--seeds") + 1] == "30"
    assert command[command.index("--epochs") + 1] == "8"
    assert command[command.index("--warmup-epochs") + 1] == "1"
    assert command[command.index("--seed") + 1] == "20260730"
    assert command[command.index("--impairment") + 1] == "non_actionable"
    assert command[command.index("--max-new-pairs") + 1] == "1"
    assert "--resume" in command


def test_analysis_commands_consume_both_frozen_conditions():
    commands = analysis_commands(
        Path("/venv/python"),
        Path("live_testbed"),
        Path("results"),
    )
    assert len(commands) == 2
    analysis = commands[0]
    assert (
        f"capacity_only={Path('results') / 'journal_gate_capacity_30seed' / 'live_measurements.csv'}"
        in analysis
    )
    assert (
        f"non_actionable={Path('results') / 'journal_gate_nonactionable_30seed' / 'live_measurements.csv'}"
        in analysis
    )
    assert commands[1][-1] == str(Path("results") / "journal_gate_analysis" / "gate_primary_outcomes.png")


def test_transfer_watchdog_covers_largest_segment_at_impaired_ceiling():
    worst_case_s = (
        SEGMENT_DURATION_S
        * max(LADDER_BPS)
        / (IMPAIRED_RATE_MBPS * 1_000_000)
    )
    assert TRANSFER_TIMEOUT_S >= 2 * worst_case_s
    assert PROCESS_TIMEOUT_S > TRANSFER_TIMEOUT_S


def test_impaired_timeout_is_recorded_as_right_censored():
    measurement = parse_curl_measurement(
        "1024,426.0,0.2,2.4,200",
        "curl: (28) Operation timed out",
        28,
        allow_censoring=True,
    )
    assert measurement == (
        1024.0,
        float(TRANSFER_TIMEOUT_S),
        0.2,
        2.4,
        True,
        28,
    )


def test_unimpaired_timeout_remains_an_infrastructure_failure():
    import pytest

    with pytest.raises(RuntimeError, match="curl failed"):
        parse_curl_measurement(
            "",
            "curl: (28) Operation timed out",
            28,
            allow_censoring=False,
        )


def test_campaign_retries_failed_subprocess_and_completes(tmp_path, monkeypatch):
    monkeypatch.setattr(campaign.os, "geteuid", lambda: 0, raising=False)
    experiment_attempts = {"non_actionable": 0, "capacity_only": 0}
    completed_pairs = {"non_actionable": 0, "capacity_only": 0}

    def fake_run(command, check):
        if any(str(part).endswith("run_mininet_experiment.py") for part in command):
            condition = command[command.index("--impairment") + 1]
            experiment_attempts[condition] += 1
            if condition == "non_actionable" and experiment_attempts[condition] == 1:
                raise subprocess.CalledProcessError(28, command)
            completed_pairs[condition] += 1
        return subprocess.CompletedProcess(command, 0)

    def fake_complete_pair_count(path):
        condition = (
            "non_actionable"
            if "nonactionable" in str(path)
            else "capacity_only"
        )
        return completed_pairs[condition]

    monkeypatch.setattr(campaign.subprocess, "run", fake_run)
    monkeypatch.setattr(campaign.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(campaign, "complete_pair_count", fake_complete_pair_count)
    monkeypatch.setattr(campaign, "EXPECTED_PAIRS_PER_CONDITION", 2)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_journal_gate_campaign.py",
            "--model",
            str(tmp_path / "model.json"),
            "--media-root",
            str(tmp_path / "Segments"),
            "--output-root",
            str(tmp_path / "results"),
            "--analysis-python",
            sys.executable,
        ],
    )

    campaign.main()

    status = json.loads(
        (tmp_path / "results" / "journal_gate_orchestration.json").read_text()
    )
    assert experiment_attempts == {
        "non_actionable": 3,
        "capacity_only": 2,
    }
    assert status["conditions"]["non_actionable"]["infrastructure_retries"] == 1
    assert status["conditions"]["non_actionable"]["status"] == "complete"
    assert status["analysis"]["status"] == "complete"
