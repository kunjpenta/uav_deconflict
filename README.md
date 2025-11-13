UAV Strategic Deconfliction

This repository implements a strategic deconfliction system that determines whether a primary drone’s planned waypoint mission is safe to execute in shared airspace.
It compares the mission trajectory against simulated flight paths of other drones in space and time, identifying potential conflicts before flight.

The system includes:

A modular spatio-temporal deconfliction engine
Trajectory interpolation from waypoints
Static 2D, animated 2D, and interactive 3D visualizations
A command-line interface (CLI) for running analyses and generating outputs
A complete pytest test suite

1. Quick Start

Clone and Set Up
git clone https://github.com/kunjpenta/uav_deconflict.git
cd uav_deconflict
python -m venv .venv


Activate the virtual environment:

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run a Demo Analysis
python src/cli.py --primary data/sample_primary_mission.json \
                  --sim data/sample_simulated_flights.json \
                  --buffer 50 \
                  --dt 1.0 \
                  --animate

2. Repository Structure

src/deconflict/
  models.py        # Data models for waypoints and missions
  io.py            # JSON input/output helpers
  traject.py       # Trajectory interpolation
  temporal.py      # Conflict detection logic
  analyzer.py      # High-level orchestration
  visualize.py     # Plotting and animation utilities
src/cli.py         # Command-line interface
data/              # Example missions and simulated flights
tests/             # pytest test suite
docs/              # Reflection and design documentation



Generated Files:

report.json
demo_paths.png
demo_anim.mp4

3. Visualization Samples

Type:	        Description	Output
Static 2D:	    XY plot of mission and simulated paths	demo_paths.png
Animated 2D:    Time-evolving paths with conflict highlights	demo_anim.mp4
Interactive 3D:	Rotatable Plotly view with time slider	demo_3d.html (optional)

4. Testing

Run the test suite:

pytest

5. Documentation

docs/reflection.md
 — Architecture overview, design rationale, AI usage, testing strategy, and scalability notes.

docs/demo_script.md
 — Suggested flow for a 3–4 minute demo video walkthrough.

6. License

MIT License © 2025 Kunj Patel