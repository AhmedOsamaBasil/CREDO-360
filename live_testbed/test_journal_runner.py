"""Tests for the frozen two-condition journal campaign orchestrator."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_journal_gate_campaign import CONTROLLERS, experiment_command


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
