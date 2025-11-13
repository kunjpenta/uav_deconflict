from datetime import datetime

from deconflict.io import (
    DATA_DIR,
    load_primary,
    load_simulated_flights,
)
from deconflict.models import PrimaryMission, SimulatedFlight, Waypoint


def test_load_primary_basic() -> None:
    path = DATA_DIR / "sample_primary_mission.json"
    mission = load_primary(path)

    assert isinstance(mission, PrimaryMission)
    assert mission.mission_id == "P001"
    assert isinstance(mission.start, datetime)
    assert isinstance(mission.end, datetime)
    assert mission.start < mission.end
    assert mission.duration_s > 0

    assert len(mission.waypoints) >= 2
    first_wp = mission.waypoints[0]
    assert isinstance(first_wp, Waypoint)
    assert first_wp.x == 0.0
    assert first_wp.y == 0.0
    assert first_wp.z == 100.0
    # Primary mission waypoints don't have per-waypoint times yet
    assert first_wp.t is None


def test_load_simulated_flights_basic() -> None:
    path = DATA_DIR / "sample_simulated_flights.json"
    flights = load_simulated_flights(path)

    assert len(flights) >= 1
    first = flights[0]
    assert isinstance(first, SimulatedFlight)
    assert isinstance(first.flight_id, str)
    assert len(first.waypoints) >= 2

    for wp in first.waypoints:
        assert isinstance(wp, Waypoint)
        assert isinstance(wp.x, float)
        assert isinstance(wp.y, float)
        assert wp.t is not None
        assert isinstance(wp.t, datetime)

    # Check time_bounds utility
    t0, t1 = first.time_bounds()
    assert isinstance(t0, datetime)
    assert isinstance(t1, datetime)
    assert t0 <= t1
