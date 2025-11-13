from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from deconflict.traject import Trajectory


def check_spatial_conflict(
    traj_A: Trajectory,
    traj_B: Trajectory,
    buffer_m: float,
    use_3d: bool = False
) -> Tuple[bool, Dict[str, float]]:
    """
    Check if two trajectories (A and B) come within the specified safety buffer distance.
    Uses a numeric approach: samples the positions and computes Euclidean distance.

    Args:
        traj_A, traj_B: Two trajectory objects to compare.
        buffer_m: Minimum safety distance (in meters).
        use_3d: If True, considers altitude (z) in the distance check.

    Returns:
        A tuple (conflict_detected: bool, details: dict).
        - conflict_detected: True if the minimum distance < buffer_m.
        - details: dictionary with the conflict details.
    """
    times_A, positions_A = traj_A.sample_uniform(dt_s=1.0)
    times_B, positions_B = traj_B.sample_uniform(dt_s=1.0)

    # Resample if the time grids are not the same length
    common_times = np.union1d(times_A, times_B)
    pos_A_resampled = np.array(
        [traj_A.sample_position_at(t)[0:2] for t in common_times])
    pos_B_resampled = np.array(
        [traj_B.sample_position_at(t)[0:2] for t in common_times])

    # Compute pairwise distances
    distances = np.linalg.norm(pos_A_resampled - pos_B_resampled, axis=1)

    min_dist = np.min(distances)
    min_dist_idx = np.argmin(distances)
    t_A_at_min = common_times[min_dist_idx]
    t_B_at_min = common_times[min_dist_idx]

    conflict_detected = min_dist < buffer_m

    details = {
        "min_distance_m": min_dist,
        "min_position_A": pos_A_resampled[min_dist_idx].tolist(),
        "min_position_B": pos_B_resampled[min_dist_idx].tolist(),
        "t_A_at_min": t_A_at_min,
        "t_B_at_min": t_B_at_min,
        "conflict_detected": conflict_detected,
    }

    return conflict_detected, details


def closest_approach(
    traj_A: Trajectory,
    traj_B: Trajectory
) -> Tuple[float, float, float, Tuple[float, float], Tuple[float, float]]:
    """
    Compute the closest approach between two trajectories.

    Returns:
        min_dist: The minimum distance between the two trajectories.
        tA_at_min: The time at which this minimum distance occurs for trajectory A.
        tB_at_min: The time at which this minimum distance occurs for trajectory B.
        posA: The position at the minimum distance for trajectory A.
        posB: The position at the minimum distance for trajectory B.
    """
    times_A, positions_A = traj_A.sample_uniform(dt_s=1.0)
    times_B, positions_B = traj_B.sample_uniform(dt_s=1.0)

    # Resample to common time grid
    common_times = np.union1d(times_A, times_B)
    pos_A_resampled = np.array(
        [traj_A.sample_position_at(t)[0:2] for t in common_times])
    pos_B_resampled = np.array(
        [traj_B.sample_position_at(t)[0:2] for t in common_times])

    # Calculate pairwise distances
    distances = np.linalg.norm(pos_A_resampled - pos_B_resampled, axis=1)

    min_dist = np.min(distances)
    min_dist_idx = np.argmin(distances)

    t_A_at_min = common_times[min_dist_idx]
    t_B_at_min = common_times[min_dist_idx]

    posA = pos_A_resampled[min_dist_idx]
    posB = pos_B_resampled[min_dist_idx]

    return min_dist, t_A_at_min, t_B_at_min, tuple(posA), tuple(posB)
