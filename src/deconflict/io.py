# src/deconflict/io.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List

from .models import PrimaryMission, SimulatedFlight, Waypoint

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


def load_json(filename: str) -> Any:
    """
    Load a JSON file from the repo's data/ directory.
    """
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Time parsing helpers
# ---------------------------------------------------------------------------

def parse_iso8601(value: str) -> datetime:
    """
    Parse an ISO-8601-like timestamp string into a datetime.

    Supports:
      - "2025-11-20T09:00:00"
      - "2025-11-20T09:00:00Z"
      - "2025-11-20T09:00:00+05:30"
    """
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError as exc:
        raise ValueError(
            f"Invalid ISO-8601 datetime string: {value!r}"
        ) from exc


def _ensure_float(name: str, val: Any) -> float:
    try:
        return float(val)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Field {name!r} must be numeric, got {val!r}"
        ) from exc


# ---------------------------------------------------------------------------
# Primary mission loading
# ---------------------------------------------------------------------------

def load_primary(path: str | Path) -> PrimaryMission:
    """
    Load a primary mission JSON into a PrimaryMission object.

    Expected JSON format:

    {
      "mission_id": "P001",
      "time_window": {
        "start": "2025-11-20T09:00:00",
        "end": "2025-11-20T09:15:00"
      },
      "waypoints": [
        {"id":"wp1","x":0.0,"y":0.0,"z":100.0},
        {"id":"wp2","x":2000.0,"y":0.0,"z":100.0},
        {"id":"wp3","x":2000.0,"y":2000.0,"z":120.0}
      ],
      "constraints": { "max_speed_mps": 20.0 }
    }
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Primary mission file not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    mission_id = raw.get("mission_id")
    if not mission_id:
        raise ValueError("Primary mission JSON must contain 'mission_id'")

    tw = raw.get("time_window") or {}
    start_raw = tw.get("start")
    end_raw = tw.get("end")
    if not start_raw or not end_raw:
        raise ValueError(
            "Primary mission JSON must contain time_window.start and time_window.end"
        )

    start = parse_iso8601(start_raw)
    end = parse_iso8601(end_raw)

    if not start < end:
        raise ValueError(
            f"Primary mission time_window.start must be before end (got {start} >= {end})"
        )

    waypoints_raw = raw.get("waypoints") or []
    if len(waypoints_raw) < 2:
        raise ValueError("Primary mission must contain at least 2 waypoints")

    waypoints: List[Waypoint] = []
    for idx, wp in enumerate(waypoints_raw):
        try:
            x = _ensure_float("x", wp["x"])
            y = _ensure_float("y", wp["y"])
        except KeyError as exc:
            raise ValueError(
                f"Waypoint {idx} missing required coordinate keys"
            ) from exc

        z_val = wp.get("z")
        z = _ensure_float("z", z_val) if z_val is not None else None
        wp_id = wp.get("id")
        waypoints.append(Waypoint(x=x, y=y, z=z, id=wp_id))

    constraints = raw.get("constraints") or {}

    return PrimaryMission(
        mission_id=mission_id,
        waypoints=waypoints,
        start=start,
        end=end,
        constraints=constraints,
    )


# ---------------------------------------------------------------------------
# Simulated flights loading
# ---------------------------------------------------------------------------

def load_simulated_flights(path: str | Path) -> List[SimulatedFlight]:
    """
    Load a list of simulated flights into SimulatedFlight objects.

    Expected JSON format (for each flight):

    {
      "flight_id": "S001",
      "waypoints": [
        {"t": "2025-11-20T09:02:00", "x": 1500, "y": -500, "z": 100},
        {"t": "2025-11-20T09:08:00", "x": 1500, "y": 2500, "z": 100}
      ],
      "metadata": { ... },

      # optional; if missing, computed from waypoint times
      "start": "2025-11-20T09:02:00",
      "end":   "2025-11-20T09:08:00"
    }
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Simulated flights file not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        raw_list = json.load(f)

    if not isinstance(raw_list, list):
        raise ValueError("Simulated flights JSON must be a list of flights")

    flights: List[SimulatedFlight] = []

    for i, raw in enumerate(raw_list):
        flight_id = raw.get("flight_id")
        if not flight_id:
            raise ValueError(
                f"Simulated flight at index {i} missing 'flight_id'"
            )

        waypoints_raw = raw.get("waypoints") or []
        if len(waypoints_raw) < 2:
            raise ValueError(
                f"Simulated flight {flight_id} must have at least 2 waypoints"
            )

        wps: List[Waypoint] = []
        times: List[datetime] = []

        for j, wp in enumerate(waypoints_raw):
            try:
                x = _ensure_float("x", wp["x"])
                y = _ensure_float("y", wp["y"])
            except KeyError as exc:
                raise ValueError(
                    f"Waypoint {j} of flight {flight_id} missing 'x' or 'y'"
                ) from exc

            z_val = wp.get("z")
            z = _ensure_float("z", z_val) if z_val is not None else None

            t_raw = wp.get("t")
            if not t_raw:
                raise ValueError(
                    f"Waypoint {j} of flight {flight_id} missing time 't'"
                )
            t = parse_iso8601(t_raw)
            times.append(t)

            wps.append(
                Waypoint(
                    x=x,
                    y=y,
                    z=z,
                    t=t,
                    id=wp.get("id"),
                )
            )

        # Prefer explicit start/end if present; otherwise derive from waypoint times.
        if "start" in raw and "end" in raw:
            start = parse_iso8601(raw["start"])
            end = parse_iso8601(raw["end"])
        else:
            if not times:
                raise ValueError(
                    f"Simulated flight {flight_id} has no valid waypoint times"
                )
            start = min(times)
            end = max(times)

        if not start < end:
            raise ValueError(
                f"Simulated flight {flight_id} start must be before end (got {start} >= {end})"
            )

        metadata = raw.get("metadata") or {}
        flights.append(
            SimulatedFlight(
                flight_id=flight_id,
                waypoints=wps,
                start=start,
                end=end,
                metadata=metadata,
            )
        )

    return flights


# ---------------------------------------------------------------------------
# Conflict report saving
# ---------------------------------------------------------------------------

def _serialize(obj: Any) -> Any:
    """
    Helper for json.dump so we can serialize dataclasses, datetimes, Paths, etc.
    """
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    return obj


def save_conflict_report(report: Any, path: str | Path) -> None:
    """
    Save any JSON-serializable report to disk.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=_serialize)


# ---------------------------------------------------------------------------
# Convenience helpers for sample data (used by CLI + tests)
# ---------------------------------------------------------------------------

def _resolve_sample_path(file_path: str | Path) -> Path:
    """
    Allow calling with either:
      - "data/sample_primary_mission.json"
      - "sample_primary_mission.json"
    """
    p = Path(file_path)
    if p.is_file():
        return p

    # Try under data/ if not found directly
    candidate = DATA_DIR / p.name
    if candidate.is_file():
        return candidate

    # Last resort: treat as relative to DATA_DIR without stripping dirs
    candidate = DATA_DIR / p
    return candidate


def load_sample_primary_mission(file_path: str) -> PrimaryMission:
    """
    Thin wrapper used by tests and CLI for the primary mission sample.
    """
    p = _resolve_sample_path(file_path)
    return load_primary(p)


def load_sample_simulated_flights(file_path: str) -> List[SimulatedFlight]:
    """
    Thin wrapper used by tests and CLI for the simulated flights sample.
    """
    p = _resolve_sample_path(file_path)
    return load_simulated_flights(p)
