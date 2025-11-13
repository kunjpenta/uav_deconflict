from datetime import datetime, timedelta

import pytest

from deconflict.models import Waypoint
from deconflict.spatial import check_spatial_conflict, closest_approach
from deconflict.traject import interpolate_from_waypoints


def test_perpendicular_path_conflict() -> None:
    """
    Two perpendicular paths should conflict at the intersection (min_dist ~ 0).
    """
    # Primary mission waypoints (straight path horizontally)
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=10)
    waypoints_A = [
        Waypoint(x=0.0, y=0.0, z=0.0),
        Waypoint(x=10.0, y=0.0, z=0.0),
    ]

    # Intruder path (straight path vertically)
    waypoints_B = [
        Waypoint(x=5.0, y=-5.0, z=0.0),
        Waypoint(x=5.0, y=5.0, z=0.0),
    ]

    traj_A = interpolate_from_waypoints(
        waypoints_A, mission_window=(start, end))
    traj_B = interpolate_from_waypoints(
        waypoints_B, mission_window=(start, end))

    conflict, details = check_spatial_conflict(traj_A, traj_B, buffer_m=1.0)

    assert conflict
    assert details["min_distance_m"] == 0.0
    assert details["min_position_A"] == [5.0, 0.0]
    assert details["min_position_B"] == [5.0, 0.0]


def test_parallel_tracks_no_conflict() -> None:
    """
    Parallel tracks with sufficient separation (> buffer) should have no conflict.
    """
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=10)

    # Primary path (horizontal)
    waypoints_A = [
        Waypoint(x=0.0, y=0.0, z=0.0),
        Waypoint(x=10.0, y=0.0, z=0.0),
    ]

    # Intruder path (parallel, offset by > buffer)
    waypoints_B = [
        Waypoint(x=0.0, y=2.0, z=0.0),
        Waypoint(x=10.0, y=2.0, z=0.0),
    ]

    traj_A = interpolate_from_waypoints(
        waypoints_A, mission_window=(start, end))
    traj_B = interpolate_from_waypoints(
        waypoints_B, mission_window=(start, end))

    conflict, details = check_spatial_conflict(traj_A, traj_B, buffer_m=1.0)

    assert not conflict
    assert details["min_distance_m"] > 1.0  # Must be > buffer


def test_closest_approach() -> None:
    """
    Test closest_approach between two trajectories.
    """
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=10)

    # Primary path (horizontal)
    waypoints_A = [
        Waypoint(x=0.0, y=0.0, z=0.0),
        Waypoint(x=10.0, y=0.0, z=0.0),
    ]

    # Intruder path (vertical)
    waypoints_B = [
        Waypoint(x=5.0, y=-5.0, z=0.0),
        Waypoint(x=5.0, y=5.0, z=0.0),
    ]

    traj_A = interpolate_from_waypoints(
        waypoints_A, mission_window=(start, end))
    traj_B = interpolate_from_waypoints(
        waypoints_B, mission_window=(start, end))

    min_dist, tA_at_min, tB_at_min, posA, posB = closest_approach(
        traj_A, traj_B)

    assert min_dist == 0.0
    assert posA == (5.0, 0.0)
    assert posB == (5.0, 0.0)
    assert tA_at_min == tB_at_min
