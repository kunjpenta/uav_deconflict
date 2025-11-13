# src/deconflict/traject.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from .models import Waypoint


@dataclass
class Trajectory:
    """
    Time-parameterized trajectory.

    times: 1D array of float seconds (e.g. Unix timestamps).
    positions: Nx3 array of [x, y, z] in meters.
    flight_id: ID of the flight to which this trajectory corresponds (optional for primary mission).
    """
    times: np.ndarray  # shape (N,)
    positions: np.ndarray  # shape (N, 3)
    flight_id: str = "primary"  # Default to "primary" for primary missions

    def __post_init__(self) -> None:
        self.times = np.asarray(self.times, dtype=float)
        self.positions = np.asarray(self.positions, dtype=float)

        if self.times.ndim != 1:
            raise ValueError("times must be a 1D array")
        if self.positions.ndim != 2 or self.positions.shape[1] != 3:
            raise ValueError("positions must be of shape (N, 3)")
        if self.times.shape[0] != self.positions.shape[0]:
            raise ValueError("times and positions length mismatch")
        if np.any(np.diff(self.times) <= 0):
            raise ValueError("times must be strictly increasing")

    # ----------------- Basic helpers -----------------

    def time_range(self) -> Tuple[float, float]:
        """Return (t0, t1) in float seconds."""
        return float(self.times[0]), float(self.times[-1])

    def sample_position_at(self, t: float | datetime) -> Tuple[float, float, float]:
        """
        Sample position at time t via linear interpolation.

        - If t is datetime: converted to seconds via datetime.timestamp().
        - If t is float: assumed to be in the same time base as self.times.
        - Outside the range: clamp to first / last position.
        """
        if isinstance(t, datetime):
            t_val = t.timestamp()
        else:
            t_val = float(t)

        if t_val <= self.times[0]:
            pos = self.positions[0]
        elif t_val >= self.times[-1]:
            pos = self.positions[-1]
        else:
            x = np.interp(t_val, self.times, self.positions[:, 0])
            y = np.interp(t_val, self.times, self.positions[:, 1])
            z = np.interp(t_val, self.times, self.positions[:, 2])
            pos = np.array([x, y, z], dtype=float)

        return float(pos[0]), float(pos[1]), float(pos[2])

    def sample_uniform(self, dt_s: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Sample trajectory on a uniform time grid with step dt_s (seconds).

        Returns:
          times_out: 1D array of times
          positions_out: Nx3 array of positions
        """
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")

        t0, t1 = self.time_range()
        if t1 <= t0:
            raise ValueError("Invalid time range")

        n_steps = int(np.floor((t1 - t0) / dt_s)) + 1
        times_out = np.linspace(t0, t1, n_steps)

        xs = np.interp(times_out, self.times, self.positions[:, 0])
        ys = np.interp(times_out, self.times, self.positions[:, 1])
        zs = np.interp(times_out, self.times, self.positions[:, 2])
        positions_out = np.stack([xs, ys, zs], axis=1)

        return times_out, positions_out


# ---------------------------------------------------------------------------
# Interpolation from waypoints
# ---------------------------------------------------------------------------

def _waypoints_to_positions(waypoints: Sequence[Waypoint]) -> np.ndarray:
    """
    Convert a list of Waypoints to an (N,3) positions array.
    Missing z is treated as 0.0.
    """
    positions = np.zeros((len(waypoints), 3), dtype=float)
    for i, wp in enumerate(waypoints):
        positions[i, 0] = float(wp.x)
        positions[i, 1] = float(wp.y)
        positions[i, 2] = 0.0 if wp.z is None else float(wp.z)
    return positions


def _compute_times_from_window(
    positions: np.ndarray,
    mission_window: Tuple[datetime, datetime],
    max_speed_mps: float | None,
) -> np.ndarray:
    """
    For a primary mission with no per-waypoint times:

    - Use mission_window (start, end) as the overall duration.
    - Distribute times along the path proportional to distance.
    - Enforce that required average speed <= max_speed_mps (if provided).
    """
    start_dt, end_dt = mission_window
    duration_s = (end_dt - start_dt).total_seconds()
    if duration_s <= 0:
        raise ValueError("mission_window duration must be positive")

    # Distances between consecutive points
    seg_lengths = np.linalg.norm(np.diff(positions, axis=0), axis=1)
    total_dist = float(seg_lengths.sum())

    if total_dist <= 0:
        # All waypoints at same position -> just distribute times evenly
        times = np.linspace(start_dt.timestamp(),
                            end_dt.timestamp(), positions.shape[0])
        return times

    required_speed = total_dist / duration_s  # m/s

    if max_speed_mps is not None and required_speed > max_speed_mps + 1e-6:
        raise ValueError(
            f"Required speed {required_speed:.3f} m/s exceeds max_speed_mps {max_speed_mps:.3f} m/s"
        )

    # Time at each waypoint proportional to cumulative distance
    cum_dist = np.concatenate([[0.0], np.cumsum(seg_lengths)])
    fractions = cum_dist / total_dist  # from 0 to 1
    times = start_dt.timestamp() + fractions * duration_s
    return times


def interpolate_from_waypoints(
    waypoints: Sequence[Waypoint],
    method: str = "linear",
    mission_window: Tuple[datetime, datetime] | None = None,
    max_speed_mps: float | None = None,
    flight_id: str = "primary",  # Default to "primary" for primary missions
) -> Trajectory:
    """
    Build a Trajectory from a sequence of Waypoints.

    Modes:

    1) Simulated flights:
       - Waypoints carry absolute times in wp.t (datetime).
       - mission_window can be None.
       - All waypoints must have t set.

    2) Primary mission:
       - Waypoints have no per-waypoint times (wp.t is None).
       - mission_window=(start_dt, end_dt) is required.
       - We infer times based on path length and total duration.
       - If max_speed_mps is provided, we enforce that required average
         speed over the whole mission does not exceed it.

    For now only 'linear' interpolation is supported.
    """
    if method != "linear":
        raise NotImplementedError(
            "Only linear interpolation is supported at this stage")

    if len(waypoints) < 2:
        raise ValueError("Need at least 2 waypoints to build a trajectory")

    positions = _waypoints_to_positions(waypoints)

    # Case 1: per-waypoint absolute times present
    if any(wp.t is not None for wp in waypoints):
        if not all(wp.t is not None for wp in waypoints):
            raise ValueError(
                "Either all or none of the waypoints must have t set")
        times = np.array([wp.t.timestamp() for wp in waypoints], dtype=float)

    # Case 2: mission_window-based timing for primary mission
    else:
        if mission_window is None:
            raise ValueError(
                "mission_window is required when waypoints have no times")
        times = _compute_times_from_window(
            positions, mission_window, max_speed_mps)

    return Trajectory(times=times, positions=positions, flight_id=flight_id)
