import json
import os
import subprocess
from pathlib import Path

import pandas as pd

SCENARIOS_DIR = Path("scenarios")
OUTPUT_DIR = Path("outputs")
SUMMARY_FILE = OUTPUT_DIR / "summary.csv"


def run_scenario(scenario_file):
    with open(SCENARIOS_DIR / scenario_file) as f:
        scenario = json.load(f)

    # Run CLI analysis for each scenario
    output_dir = OUTPUT_DIR / scenario_file.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "report.json"

    command = [
        "python", "src/cli.py",
        "--primary", scenario["primary_mission_file"],
        "--sim", scenario["simulated_flights_file"],
        "--buffer", str(scenario.get("buffer", 50)),
        "--dt", str(scenario.get("dt", 1.0)),
        "--out", str(report_file),
        "--animate"
    ]

    subprocess.run(command, check=True)

    # Add the results to the summary CSV
    return {
        "scenario": scenario_file.stem,
        "status": scenario.get("status", "UNKNOWN"),
        "min_distance": scenario.get("min_distance", 0),
        "time_of_min": scenario.get("time_of_min", ""),
        "visuals_exist": os.path.exists(output_dir / "demo_paths.png")
    }


def run_all_scenarios():
    summary_data = []

    # Create a summary DataFrame to collect all results
    for scenario_file in SCENARIOS_DIR.glob("*.json"):
        scenario_result = run_scenario(scenario_file)
        summary_data.append(scenario_result)

    df = pd.DataFrame(summary_data)
    df.to_csv(SUMMARY_FILE, index=False)


if __name__ == "__main__":
    run_all_scenarios()
