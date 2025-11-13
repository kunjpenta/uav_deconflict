from datetime import datetime, timedelta

from deconflict.models import Waypoint
from deconflict.spatial import check_spatial_conflict
from deconflict.temporal import check_spatiotemporal_conflicts
from deconflict.traject import interpolate_from_waypoints


def test_clear_temporal_overlap() -> None:
    """
    Two flights cross in space but not in time, expecting "clear".
    """
    # Primary mission (horizontal path)
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=10)
    waypoints_A = [
        Waypoint(x=0.0, y=0.0, z=0.0),
        Waypoint(x=10.0, y=0.0, z=0.0),
    ]

    # Simulated flight (vertical path)
    waypoints_B = [
        Waypoint(x=5.0, y=-5.0, z=0.0),
        Waypoint(x=5.0, y=5.0, z=0.0),
    ]

    traj_A = interpolate_from_waypoints(
        waypoints_A, mission_window=(start, end))
    traj_B = interpolate_from_waypoints(waypoints_B, mission_window=(
        start + timedelta(seconds=5), end + timedelta(seconds=5)))

    conflict_result = check_spatiotemporal_conflicts(
        traj_A, [traj_B], safety_buffer_m=1.0, dt=1.0
    )

    assert conflict_result["status"] == "clear"


def test_conflict_in_space_and_time() -> None:
    """
    Two flights cross both in space and time, expecting "conflict".
    """
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=10)
    waypoints_A = [
        Waypoint(x=0.0, y=0.0, z=0.0),
        Waypoint(x=10.0, y=0.0, z=0.0),
    ]
    waypoints_B = [
        Waypoint(x=5.0, y=-5.0, z=0.0),
        Waypoint(x=5.0, y=5.0, z=0.0),
    ]

    traj_A = interpolate_from_waypoints(
        waypoints_A, mission_window=(start, end))
    traj_B = interpolate_from_waypoints(
        waypoints_B, mission_window=(start, end))

    conflict_result = check_spatiotemporal_conflicts(
        traj_A, [traj_B], safety_buffer_m=1.0, dt=1.0
    )

    assert conflict_result["status"] == "conflict"
    assert len(conflict_result["conflicts"]) > 0
    assert conflict_result["conflicts"][0]["min_distance_m"] < 1.0


def test_conflict_report_format() -> None:
    """
    Ensure the conflict report is correctly formatted.
    """
    # Use the same setup as test_conflict_in_space_and_time()
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(seconds=10)
    waypoints_A = [
        Waypoint(x=0.0, y=0.0, z=0.0),
        Waypoint(x=10.0, y=0.0, z=0.0),
    ]
    waypoints_B = [
        Waypoint(x=5.0, y=-5.0, z=0.0),
        Waypoint(x=5.0, y=5.0, z=0.0),
    ]

    traj_A = interpolate_from_waypoints(
        waypoints_A, mission_window=(start, end))
    traj_B = interpolate_from_waypoints(
        waypoints_B, mission_window=(start, end))

    conflict_result = check_spatiotemporal_conflicts(
        traj_A, [traj_B], safety_buffer_m=1.0, dt=1.0
    )

    # Check if the report contains the expected conflict explanation
    assert "explanation" in conflict_result["conflicts"][0]
    assert "min_distance_m" in conflict_result["conflicts"][0]
