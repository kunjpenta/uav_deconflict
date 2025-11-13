from datetime import datetime, timedelta

import numpy as np
import pytest

from deconflict.models import Waypoint
from deconflict.traject import Trajectory, interpolate_from_waypoints


def test_linear_midpoint_primary_mission() -> None:
    """
    2-waypoint mission, 10s window, 10m distance -> 1 m/s.
    Mid-time should be at the geometric midpoint.
    """
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=10)

    waypoints = [
        Waypoint(x=0.0, y=0.0, z=100.0),
        Waypoint(x=10.0, y=0.0, z=100.0),
    ]

    traj = interpolate_from_waypoints(
        waypoints,
        mission_window=(start, end),
        max_speed_mps=5.0,  # 1 m/s required <= 5 m/s
    )

    t0, t1 = traj.time_range()
    t_mid = 0.5 * (t0 + t1)

    x, y, z = traj.sample_position_at(t_mid)

    assert abs(x - 5.0) < 1e-6
    assert abs(y - 0.0) < 1e-6
    assert abs(z - 100.0) < 1e-6


def test_max_speed_constraint_violation() -> None:
    """
    1000m in 10s requires 100 m/s; if max_speed_mps=50, this should fail.
    """
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=10)

    waypoints = [
        Waypoint(x=0.0, y=0.0, z=0.0),
        Waypoint(x=1000.0, y=0.0, z=0.0),
    ]

    with pytest.raises(ValueError):
        interpolate_from_waypoints(
            waypoints,
            mission_window=(start, end),
            max_speed_mps=50.0,
        )


def test_waypoint_times_used_for_simulated_flight() -> None:
    """
    If waypoints have absolute times, they must be used as-is.
    """
    t0 = datetime(2025, 1, 1, 10, 0, 0)
    t1 = datetime(2025, 1, 1, 10, 0, 10)

    waypoints = [
        Waypoint(x=0.0, y=0.0, z=0.0, t=t0),
        Waypoint(x=10.0, y=0.0, z=0.0, t=t1),
    ]

    traj = interpolate_from_waypoints(waypoints)

    tt0, tt1 = traj.time_range()
    assert abs(tt0 - t0.timestamp()) < 1e-6
    assert abs(tt1 - t1.timestamp()) < 1e-6


def test_sample_uniform_grid() -> None:
    """
    Uniform sampling should give equally spaced positions for a straight line.
    """
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=4)

    waypoints = [
        Waypoint(x=0.0, y=0.0, z=0.0),
        Waypoint(x=4.0, y=0.0, z=0.0),
    ]

    traj = interpolate_from_waypoints(waypoints, mission_window=(start, end))

    times_out, positions_out = traj.sample_uniform(dt_s=1.0)

    assert times_out.shape[0] == 5  # 0,1,2,3,4 seconds
    assert positions_out.shape == (5, 3)

    xs = positions_out[:, 0]
    assert np.allclose(xs, np.array([0.0, 1.0, 2.0, 3.0, 4.0]))
