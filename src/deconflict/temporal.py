# src/deconflict/temporal.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import numpy as np

from .traject import Trajectory


def check_spatiotemporal_conflicts(
    primary_traj: Trajectory,
    sim_trajs: List[Trajectory],
    safety_buffer_m: float,
    dt: float = 1.0,
    use_3d: bool = False,
) -> Dict[str, Any]:
    """
    Check for spatio-temporal conflicts between a primary drone trajectory
    and a list of simulated flight trajectories.

    Args:
        primary_traj: Trajectory of the primary drone.
        sim_trajs:    List of trajectories for other drones.
        safety_buffer_m: Minimum allowed separation (meters).
        dt:          Time step for sampling along the overlap window (seconds).
        use_3d:      If True, use (x, y, z) distance; otherwise (x, y) only.

    Returns:
        {
          "status": "clear" | "conflict",
          "conflicts": [ { ... conflict detail ... }, ... ]
        }
    """
    conflicts: List[Dict[str, Any]] = []

    # Time range of primary trajectory (in seconds)
    primary_t0, primary_t1 = primary_traj.time_range()

    for sim_traj in sim_trajs:
        # Time range of simulated trajectory
        sim_t0, sim_t1 = sim_traj.time_range()

        # Overlapping time window
        overlap_start = max(primary_t0, sim_t0)
        overlap_end = min(primary_t1, sim_t1)

        if overlap_end <= overlap_start:
            # No temporal overlap => no possible spatio-temporal conflict
            continue

        # Sample times in the overlap window
        t_grid = np.arange(overlap_start, overlap_end, dt)
        if t_grid.size == 0:
            continue

        # Sample positions at each time (cast NumPy scalars to float for type checkers)
        primary_samples = np.array(
            [primary_traj.sample_position_at(float(t))[0:3] for t in t_grid]
        )
        sim_samples = np.array(
            [sim_traj.sample_position_at(float(t))[0:3] for t in t_grid]
        )

        # 2D vs 3D distance
        dims = 3 if use_3d else 2
        primary_xy = primary_samples[:, :dims]
        sim_xy = sim_samples[:, :dims]

        # Euclidean distance at each sampled time
        dists = np.linalg.norm(primary_xy - sim_xy, axis=1)

        # Indices where the safety buffer is violated
        conflict_indices = np.where(dists < safety_buffer_m)[0]

        if conflict_indices.size == 0:
            continue

        # Build conflict entries
        for idx in conflict_indices:
            t_val = float(t_grid[idx])
            # We treat trajectory time as "seconds since epoch" for formatting;
            # tests only care that this is a valid ISO string, not the exact date.
            t_iso = datetime.utcfromtimestamp(t_val).isoformat()

            conflict_details: Dict[str, Any] = {
                "flight_id": getattr(sim_traj, "flight_id", "unknown"),
                "conflict_times": [t_iso],
                "conflict_positions": [
                    {
                        "primary": primary_samples[idx].tolist(),
                        "sim": sim_samples[idx].tolist(),
                    }
                ],
                "min_distance_m": float(dists[idx]),
                "time_of_min": t_iso,
                "explanation": (
                    f"At {t_iso}, primary and {getattr(sim_traj, 'flight_id', 'unknown')} "
                    f"were within {dists[idx]:.2f} m at position "
                    f"{primary_samples[idx][:2].tolist()}"
                ),
            }
            conflicts.append(conflict_details)

    if conflicts:
        return {"status": "conflict", "conflicts": conflicts}
    else:
        return {"status": "clear", "conflicts": []}


def format_conflict_report(conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normalize conflict list into a JSON-friendly report.

    Args:
        conflicts: Raw conflict dicts as produced by check_spatiotemporal_conflicts.

    Returns:
        {
          "status": "clear" | "conflict",
          "conflicts": [ ... cleaned conflicts ... ]
        }
    """
    if not conflicts:
        return {"status": "clear", "conflicts": []}

    report_items: List[Dict[str, Any]] = []
    for conflict in conflicts:
        report_items.append(
            {
                "flight_id": conflict.get("flight_id"),
                "conflict_times": conflict.get("conflict_times", []),
                "conflict_positions": conflict.get("conflict_positions", []),
                "min_distance_m": conflict.get("min_distance_m"),
                "time_of_min": conflict.get("time_of_min"),
                "explanation": conflict.get("explanation"),
            }
        )

    return {"status": "conflict", "conflicts": report_items}
