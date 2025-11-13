#!/usr/bin/env python
"""
Small bootstrap demo to prove the project skeleton + I/O work.

- Loads sample mission + simulated flights from data/
- Prints a summary
- Saves a simple 2D plot of all paths to demo_paths.png
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from deconflict import io, visualize  # type: ignore
from deconflict.models import PrimaryMission, SimulatedFlight  # type: ignore
from src.deconflict.traject import interpolate_from_waypoints
from src.deconflict.visualize import animate_2d, plot_interactive_3d, plot_static_2d

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def main() -> None:
    mission: PrimaryMission = io.load_sample_primary_mission()
    flights: list[SimulatedFlight] = io.load_sample_simulated_flights()

    print("[run_demo] Loaded primary mission:")
    print(f"  mission_id     = {mission.mission_id}")
    print(f"  window         = {mission.start}  ->  {mission.end}")
    print(f"  num waypoints  = {len(mission.waypoints)}")

    print("\n[run_demo] Loaded simulated flights:")
    print(f"  num flights = {len(flights)}")
    for f in flights:
        t0, t1 = f.time_bounds()  # Get the time bounds of each simulated flight
        print(f"    {f.flight_id}: {len(f.waypoints)} wps, [{t0} -> {t1}]")

    # Convert PrimaryMission and SimulatedFlights to Trajectory objects
    primary_traj = interpolate_from_waypoints(
        mission.waypoints, mission_window=(mission.start, mission.end))

    # For simulated flights, use the first and last waypoint timestamps as the time window
    sim_trajs = [interpolate_from_waypoints(
        f.waypoints,
        # Use the first and last waypoint times
        mission_window=(f.waypoints[0].t, f.waypoints[-1].t)
    ) for f in flights]

    # Plot static 2D
    print("\n[run_demo] Saving simple 2D plot to demo_paths.png...")
    plot_static_2d(primary_traj, sim_trajs, buffer_m=100,
                   save_path="demo_paths.png")
    print("[run_demo] Plot saved. Open demo_paths.png to view.")


if __name__ == "__main__":
    main()
