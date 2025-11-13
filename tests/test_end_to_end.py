import os
import subprocess

import pytest


@pytest.fixture
def run_cli():
    # Replace with the actual command to run the CLI
    command = [
        "python", "src/cli.py",
        "--primary", "data/sample_primary_mission.json",
        "--sim", "data/sample_simulated_flights.json",
        "--buffer", "50",
        "--dt", "1.0",
        "--out", "report.json",
        "--animate"
    ]
    return subprocess.run(command, capture_output=True, text=True)

    # Accept either clear or conflict, case-insensitive


def test_cli_run(run_cli):
    assert run_cli.returncode == 0
    stdout = run_cli.stdout.lower()
    assert "clear" in stdout or "conflict" in stdout
    assert os.path.exists("report.json")

    # Check if visual output files exist
    assert os.path.exists("demo_paths.png")
    assert os.path.exists("animation.mp4")
