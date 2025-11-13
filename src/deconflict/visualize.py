# src/deconflict/visualize.py

from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objs as go
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle

# Define types for clarity
Point2D = Tuple[float, float]
Path2D = List[Point2D]

# Function to plot 2D paths


def plot_2d_paths(paths: List[Path2D]) -> None:
    """
    Plot one or more 2D paths on the same axes.
    Each path = sequence of (x, y) pairs.
    """
    for path in paths:
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        plt.plot(xs, ys, marker="o")

    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.axis("equal")
    plt.title("Sample UAV & intruder paths (bootstrap demo)")
    plt.tight_layout()
    plt.show()

# Static 2D plot for UAV trajectories and potential conflicts


def plot_static_2d(primary_traj, sim_trajs, buffer_m: Optional[float] = None, show: bool = True, save_path: Optional[str] = None) -> None:
    """
    Plot static 2D paths for the primary drone and simulated flights. If buffer_m or conflicts are given,
    highlight conflict positions.

    Args:
        primary_traj: Trajectory of the primary drone.
        sim_trajs: List of Trajectories for simulated drones.
        buffer_m: Optional buffer radius to show conflict areas.
        show: Whether to display the plot.
        save_path: If given, save the plot as an image.
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    # Plot primary drone trajectory
    ax.plot(
        [pos[0] for pos in primary_traj.positions],
        [pos[1] for pos in primary_traj.positions],
        label="Primary Mission",
        linewidth=2,
        color="b",
    )

    # Plot simulated flights
    for traj in sim_trajs:
        ax.plot(
            [pos[0] for pos in traj.positions],
            [pos[1] for pos in traj.positions],
            label=f"Simulated {traj.flight_id}",
            linestyle="--",
            color="r",
        )

    # Plot waypoints for primary and simulated flights
    ax.scatter([pos[0] for pos in primary_traj.positions], [pos[1]
               for pos in primary_traj.positions], color='b', zorder=5, label="Primary Waypoints")
    for traj in sim_trajs:
        ax.scatter([pos[0] for pos in traj.positions], [pos[1] for pos in traj.positions],
                   color='r', zorder=5, label=f"Simulated {traj.flight_id} Waypoints")

    # If buffer is provided, mark the conflict regions
    if buffer_m is not None:
        for traj in sim_trajs:
            for i in range(len(traj.positions)):
                # Draw a buffer circle around each waypoint
                circle = Circle(
                    (traj.positions[i][0], traj.positions[i][1]), buffer_m, color='yellow', fill=True, alpha=0.3)
                ax.add_patch(circle)

    ax.set_xlabel('X (meters)')
    ax.set_ylabel('Y (meters)')
    ax.set_title('UAV Trajectories and Conflicts')
    ax.legend(loc='best')

    # Save or show plot
    if save_path:
        plt.savefig(save_path, dpi=300)
    if show:
        plt.show()

# Animate 2D paths with conflicts


def animate_2d(primary_traj, sim_trajs, conflicts: Optional[List[int]] = None, dt_display: float = 0.5, duration_clip: Optional[float] = None, save_path: Optional[str] = None) -> None:
    """
    Create an animation that shows UAV paths over time with highlighted conflicts.

    Args:
        primary_traj: Trajectory of the primary drone.
        sim_trajs: List of Trajectories for simulated drones.
        conflicts: List of conflict points to highlight.
        dt_display: Time step for the animation in seconds.
        duration_clip: Optional duration to clip the animation.
        save_path: Path to save the animation (MP4 format).
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(np.min([pos[0] for pos in primary_traj.positions]) - 10,
                np.max([pos[0] for pos in primary_traj.positions]) + 10)
    ax.set_ylim(np.min([pos[1] for pos in primary_traj.positions]) - 10,
                np.max([pos[1] for pos in primary_traj.positions]) + 10)

    # Plot the UAV trajectories as lines (will be updated in animation)
    line_primary, = ax.plot(
        [], [], label="Primary Mission", color='b', linewidth=2)
    line_simulated, = ax.plot(
        [], [], label="Simulated Flights", color='r', linestyle='--')

    # Plot waypoints (fixed)
    ax.scatter([pos[0] for pos in primary_traj.positions], [pos[1]
               for pos in primary_traj.positions], color='b', zorder=5)
    for traj in sim_trajs:
        ax.scatter([pos[0] for pos in traj.positions], [pos[1]
                   for pos in traj.positions], color='r', zorder=5)

    def update(frame):
        # Update positions for primary mission
        line_primary.set_data([pos[0] for pos in primary_traj.positions[:frame]], [
                              pos[1] for pos in primary_traj.positions[:frame]])

        # Update positions for simulated drones
        for traj, line in zip(sim_trajs, [line_simulated]):
            line.set_data([pos[0] for pos in traj.positions[:frame]], [
                          pos[1] for pos in traj.positions[:frame]])

        # Highlight conflicts if any
        if conflicts and frame in conflicts:
            ax.scatter(
                primary_traj.positions[frame][0], primary_traj.positions[frame][1], color='r', s=100)
            for traj in sim_trajs:
                ax.scatter(
                    traj.positions[frame][0], traj.positions[frame][1], color='r', s=100)

        return line_primary, line_simulated

    # Create animation
    ani = FuncAnimation(fig, update, frames=len(
        primary_traj.positions), interval=dt_display * 1000, repeat=False)

    # Save or display the animation
    if save_path:
        ani.save(save_path, writer='ffmpeg', dpi=300)
    plt.show()

# Interactive 3D plot for UAV trajectories


def plot_interactive_3d(primary_traj, sim_trajs, conflict_events: Optional[List[int]] = None, save_html: Optional[str] = None) -> None:
    """
    Create an interactive 3D plot using Plotly to show UAV trajectories.

    Args:
        primary_traj: Trajectory of the primary drone.
        sim_trajs: List of Trajectories for simulated drones.
        conflict_events: List of conflicts to highlight.
        save_html: Path to save the interactive 3D plot (HTML).
    """
    # Create traces for each UAV
    trace_primary = go.Scatter3d(
        x=[pos[0] for pos in primary_traj.positions],
        y=[pos[1] for pos in primary_traj.positions],
        z=[pos[2] for pos in primary_traj.positions],
        mode='lines+markers',
        name='Primary Mission',
        line=dict(color='blue', width=4),
        marker=dict(size=5, color='blue')
    )

    traces_simulated = []
    for traj in sim_trajs:
        trace = go.Scatter3d(
            x=[pos[0] for pos in traj.positions],
            y=[pos[1] for pos in traj.positions],
            z=[pos[2] for pos in traj.positions],
            mode='lines+markers',
            name=f'Simulated {traj.flight_id}',
            line=dict(color='red', width=2, dash='dash'),
            marker=dict(size=5, color='red')
        )
        traces_simulated.append(trace)

    # Create the layout with a time slider
    layout = go.Layout(
        title='3D UAV Trajectories',
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
        ),
    )

    # Combine the traces
    data = [trace_primary] + traces_simulated

    fig = go.Figure(data=data, layout=layout)

    if save_html:
        fig.write_html(save_html)
    fig.show()
