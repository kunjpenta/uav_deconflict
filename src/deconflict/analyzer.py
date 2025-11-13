# src/deconflict/analyzer.py

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .io import load_primary, load_simulated_flights
from .models import PrimaryMission, SimulatedFlight
from .temporal import check_spatiotemporal_conflicts
from .traject import Trajectory, interpolate_from_waypoints


def naive_conflict_score(distance_m: float, threshold_m: float = 50.0) -> float:
    """
    Simple helper to turn a separation distance into a [0,1] "risk" score.

    Currently not used in the main pipeline, but kept for possible extensions
    (e.g. prioritizing conflicts).
    """
    if distance_m >= threshold_m:
        return 0.0
    if distance_m <= 0.0:
        return 1.0
    return (threshold_m - distance_m) / threshold_m


def analyze_mission(
    primary_mission_json: str,
    simulated_flights_json: str,
    safety_buffer: float,
    dt: float = 1.0,
    use_3d: bool = False,
) -> Tuple[str, Dict[str, Any]]:
    """
    Analyze the primary mission (from JSON file path) against simulated flight
    paths (also from JSON file path).

    Args:
        primary_mission_json: Path to primary mission JSON file.
        simulated_flights_json: Path to simulated flights JSON file.
        safety_buffer: Safety distance threshold in meters.
        dt: Sampling step in seconds for spatio-temporal conflict checking.
        use_3d: If True, use (x, y, z); if False, use (x, y) only.

    Returns:
        (status, report) where:
          - status: "clear" or "conflict"
          - report: dict with "status" and "conflicts" list.
    """

    # 1) Load mission and flights from JSON
    primary_mission: PrimaryMission = load_primary(primary_mission_json)
    simulated_flights: List[SimulatedFlight] = load_simulated_flights(
        simulated_flights_json
    )

    # 2) Interpolate trajectories

    # Primary trajectory uses its mission window explicitly
    primary_traj = interpolate_from_waypoints(
        primary_mission.waypoints,
        mission_window=(primary_mission.start, primary_mission.end),
        max_speed_mps=primary_mission.constraints.get("max_speed_mps", None),
    )

    # Simulated flights: derive their time window from waypoint times
    sim_trajs: List[Trajectory] = []
    for flight in simulated_flights:
        start, end = flight.time_bounds()  # <- use the helper, no direct .start/.end
        sim_traj = interpolate_from_waypoints(
            flight.waypoints,
            mission_window=(start, end),
        )
        sim_trajs.append(sim_traj)

    # Attach flight_id to each simulated trajectory so temporal.py
    # can include it in conflict explanations.
    sim_trajs_with_ids: List[Trajectory] = [
        Trajectory(
            times=traj.times,
            positions=traj.positions,
            flight_id=flight.flight_id,
        )
        for traj, flight in zip(sim_trajs, simulated_flights)
    ]

    # 3) Run spatio-temporal conflict analysis
    conflict_result = check_spatiotemporal_conflicts(
        primary_traj,
        sim_trajs_with_ids,
        safety_buffer_m=safety_buffer,
        dt=dt,
        use_3d=use_3d,
    )

    # 4) Normalize status to a simple string + full report
    status = conflict_result.get("status", "clear")
    if status == "clear":
        return "clear", conflict_result
    else:
        return "conflict", conflict_result
