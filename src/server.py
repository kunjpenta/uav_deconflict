import os
from datetime import datetime
from typing import Any, Dict, List, Optional  # <-- Import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# Define the Pydantic models for validation


class Waypoint(BaseModel):
    x: float
    y: float
    z: Optional[float] = None  # <-- Optional is now recognized
    t: Optional[datetime] = None
    id: Optional[str] = None


class PrimaryMission(BaseModel):
    mission_id: str
    waypoints: List[Waypoint]
    start: datetime
    end: datetime
    constraints: Dict[str, Any] = {}

    @property
    def duration_s(self) -> float:
        return (self.end - self.start).total_seconds()


class SimulatedFlight(BaseModel):
    flight_id: str
    waypoints: List[Waypoint]
    metadata: Dict[str, Any] = {}

    def time_bounds(self) -> tuple[datetime, datetime]:
        times = [wp.t for wp in self.waypoints if wp.t is not None]
        if not times:
            raise ValueError(
                f"SimulatedFlight {self.flight_id} has no waypoint times")
        return min(times), max(times)

# This model is used to validate the entire incoming request body


class MissionRequest(BaseModel):
    mission: PrimaryMission
    flights: List[SimulatedFlight]

# POST endpoint to check for mission conflict


@app.post("/check")
async def check_mission(mission_data: MissionRequest):
    # Process the mission_data and simulate flight conflict checking
    # You can use your existing logic to check for conflicts here
    conflicts = []  # Example conflict result
    status = "clear"  # Or "conflict" if conflicts are found

    # Return the status and the report (could be detailed conflict report)
    return {
        "status": status,
        "report": conflicts  # Add detailed conflict report here
    }

# Simple health check


@app.get("/health")
async def health_check():
    return {"status": "OK"}

# Endpoint to serve visual artifacts (e.g., images, HTML)


@app.get("/static/visual/{name}")
async def get_visual(name: str):
    # Ensure the path to the visual examples is correct
    visual_path = f"visual_examples/{name}"

    # Check if the file exists before returning it
    if os.path.exists(visual_path):
        return FileResponse(visual_path)
    else:
        return {"error": "File not found"}
