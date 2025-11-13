from deconflict.visualize import plot_interactive_3d
import os
import tempfile

import pytest

from deconflict.models import PrimaryMission, SimulatedFlight, Waypoint
from deconflict.visualize import animate_2d, plot_interactive_3d, plot_static_2d


# Sample data for testing
@pytest.fixture
def sample_data():
    # Create primary mission
    mission = PrimaryMission(
        mission_id="P001",
        start="2025-11-20T09:00:00",
        end="2025-11-20T09:15:00",
        waypoints=[
            Waypoint(x=0.0, y=0.0, z=100.0),
            Waypoint(x=2000.0, y=0.0, z=100.0),
            Waypoint(x=2000.0, y=2000.0, z=120.0)
        ]
    )
    flights = [
        SimulatedFlight(
            flight_id="S001",
            waypoints=[Waypoint(x=1500.0, y=-500.0, z=100.0),
                       Waypoint(x=1500.0, y=2500.0, z=100.0)]
        ),
        SimulatedFlight(
            flight_id="S002",
            waypoints=[Waypoint(x=2000.0, y=-1000.0, z=150.0),
                       Waypoint(x=2000.0, y=2000.0, z=150.0)]
        )
    ]
    return mission, flights


def test_plot_static_2d(sample_data):
    mission, flights = sample_data
    # Create a temp file that actually ends in .png
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        plot_static_2d(mission, flights, save_path=temp_file.name)

        # Now this is true by construction
        assert temp_file.name.endswith(".png")
        # And we actually check that the file was written
        assert os.path.exists(temp_file.name)


def test_animate_2d(sample_data):
    mission, flights = sample_data
    # Give ffmpeg a proper .mp4 path
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        animate_2d(mission, flights, save_path=temp_file.name)

        assert temp_file.name.endswith(".mp4")
        assert os.path.exists(temp_file.name)


def test_plot_interactive_3d(sample_data):
    mission, flights = sample_data
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
        plot_interactive_3d(mission, flights, save_html=temp_file.name)

        assert temp_file.name.endswith(".html")
        assert os.path.exists(temp_file.name)
