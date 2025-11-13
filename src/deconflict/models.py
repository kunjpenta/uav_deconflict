# src/deconflict/models.py

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class Waypoint(BaseModel):
    """
    Single waypoint in space (and optionally time).
    x, y: horizontal coordinates (meters or any consistent unit)
    z:   optional altitude
    t:   optional timestamp
    id:  optional label/name
    """
    x: float
    y: float
    z: Optional[float] = None
    t: Optional[datetime] = None
    id: Optional[str] = None


class PrimaryMission(BaseModel):
    """
    Primary drone mission:
    - mission_id: identifier
    - waypoints:  route to be flown
    - start/end: overall time window for the mission
    - constraints: optional mission-level parameters
    """
    mission_id: str
    waypoints: List[Waypoint]
    start: datetime
    end: datetime
    constraints: Dict[str, Any] = Field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        """Mission duration in seconds."""
        return (self.end - self.start).total_seconds()

    @property
    def positions(self) -> List[Tuple[float, float, float]]:
        """
        Convenience view of all waypoint positions as (x, y, z).
        If z is missing, default to 0.0.
        Used by visualization functions.
        """
        return [
            (wp.x, wp.y, wp.z if wp.z is not None else 0.0)
            for wp in self.waypoints
        ]


class SimulatedFlight(BaseModel):
    """
    Other drones' flights used for deconfliction.
    - flight_id: identifier
    - waypoints: full spatio-temporal path
    - metadata:  optional extra info (e.g., type, priority)
    """
    flight_id: str
    waypoints: List[Waypoint]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def positions(self) -> List[Tuple[float, float, float]]:
        """
        Convenience view of all waypoint positions as (x, y, z).
        If z is missing, default to 0.0.
        Used by visualization functions.
        """
        return [
            (wp.x, wp.y, wp.z if wp.z is not None else 0.0)
            for wp in self.waypoints
        ]

    def time_bounds(self) -> Tuple[datetime, datetime]:
        """
        Infer start/end times from waypoint timestamps.
        Raises if no waypoint has time information.
        """
        times = [wp.t for wp in self.waypoints if wp.t is not None]
        if not times:
            raise ValueError(
                f"SimulatedFlight {self.flight_id} has no waypoint times"
            )
        return min(times), max(times)


class MissionRequest(BaseModel):
    """
    Request model for APIs:
    - mission: primary mission to check
    - flights: list of simulated flights in the shared airspace
    """
    mission: PrimaryMission
    flights: List[SimulatedFlight]
