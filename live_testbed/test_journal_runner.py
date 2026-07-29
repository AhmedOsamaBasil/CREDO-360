"""Tests for the frozen two-condition journal campaign orchestrator."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_journal_gate_campaign import (
    CONTROLLERS,
    analysis_commands,
    experiment_command,
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
        "capacity_only=results/journal_gate_capacity_30seed/live_measurements.csv"
        in analysis
    )
    assert (
        "non_actionable=results/journal_gate_nonactionable_30seed/live_measurements.csv"
        in analysis
    )
    assert commands[1][-1] == "results/journal_gate_analysis/gate_primary_outcomes.png"
