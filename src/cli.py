# src/cli.py

from __future__ import annotations

import argparse
import json
from pathlib import Path

from deconflict import analyzer, io, visualize
from deconflict.models import PrimaryMission, SimulatedFlight


def run_analysis(
    primary_mission_file: str,
    simulated_flights_file: str,
    buffer: float,
    dt: float,
    output_file: str | None,
    animate: bool,
) -> None:
    """
    High-level CLI entrypoint:
    - Runs core deconfliction using JSON files via analyzer.analyze_mission
    - Optionally saves a JSON report
    - Optionally generates a 2D animation using the loaded mission objects
    """

    # Load mission objects (for visualization / metadata only)
    primary_mission: PrimaryMission = io.load_sample_primary_mission(
        primary_mission_file)
    simulated_flights: list[SimulatedFlight] = io.load_sample_simulated_flights(
        simulated_flights_file
    )

    # Core conflict analysis still uses filenames (JSON-based)
    status, conflicts = analyzer.analyze_mission(
        primary_mission_file,
        simulated_flights_file,
        buffer,
        dt,
    )

    # Console output
    if status == "clear":
        print("CLEAR")
    else:
        print("CONFLICT DETECTED")

    if status == "CONFLICT DETECTED":
        print(f"Conflicts found: {len(conflicts)}")
        for conflict in conflicts:
            print(conflict)

    # Optional JSON report
    if output_file:
        report_path = Path(output_file)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump({"status": status, "conflicts": conflicts}, f, indent=2)

    # Optional animation using mission objects directly
    if animate:
        visualize.animate_2d(
            primary_traj=primary_mission,
            sim_trajs=simulated_flights,
            conflicts=None,      # you can wire real conflict info later if needed
            dt_display=dt,
            save_path="animation.mp4",
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UAV Deconfliction System CLI",
    )
    parser.add_argument(
        "--primary",
        required=True,
        help="Path to the primary mission JSON file",
    )
    parser.add_argument(
        "--sim",
        required=True,
        help="Path to the simulated flights JSON file",
    )
    parser.add_argument(
        "--buffer",
        type=float,
        default=50.0,
        help="Safety buffer in meters",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=1.0,
        help="Time delta for sampling in seconds",
    )
    parser.add_argument(
        "--out",
        help="Optional path to save the conflict report JSON",
    )
    parser.add_argument(
        "--animate",
        action="store_true",
        help="Generate a simple 2D animation of the mission and flights",
    )

    args = parser.parse_args()

    run_analysis(
        primary_mission_file=args.primary,
        simulated_flights_file=args.sim,
        buffer=args.buffer,
        dt=args.dt,
        output_file=args.out,
        animate=args.animate,
    )


if __name__ == "__main__":
    main()
