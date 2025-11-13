#!/usr/bin/env python
"""
Simple demo video builder for the UAV deconfliction project.

- Uses the existing animation.mp4 as the main visual.
- If docs/voiceover.wav exists, it will be muxed in as the audio track.
- Output: deliverables/uav_deconflict_demo.mp4

Requires: ffmpeg installed and on PATH.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path


def run_ffmpeg(cmd: str) -> None:
    """Run an ffmpeg command with basic logging."""
    print(f"[ffmpeg] {cmd}")
    try:
        subprocess.run(shlex.split(cmd), check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] ffmpeg failed with code {exc.returncode}")
        sys.exit(1)


def main() -> None:
    # Project root = two levels up from this script: scripts/make_demo_video.py
    root = Path(__file__).resolve().parents[1]

    # Input assets
    anim_mp4 = root / "animation.mp4"           # from your CLI/visualize pipeline
    voiceover_wav = root / "docs" / "voiceover.wav"  # optional

    if not anim_mp4.is_file():
        print(f"[ERROR] Animation file not found: {anim_mp4}")
        print("Run the CLI with --animate first, e.g.:")
        print(
            "  python src/cli.py "
            "--primary data/sample_primary_mission.json "
            "--sim data/sample_simulated_flights.json "
            "--buffer 50 --dt 1.0 --out report.json --animate"
        )
        sys.exit(1)

    # Output folder
    deliverables_dir = root / "deliverables"
    deliverables_dir.mkdir(parents=True, exist_ok=True)

    out_video = deliverables_dir / "uav_deconflict_demo.mp4"

    if voiceover_wav.is_file():
        # Combine animation video + external voiceover
        cmd = (
            f'ffmpeg -y '
            f'-i "{anim_mp4}" '
            f'-i "{voiceover_wav}" '
            f'-c:v copy -c:a aac -shortest '
            f'"{out_video}"'
        )
        print("[INFO] Using animation.mp4 + docs/voiceover.wav")
    else:
        # No voiceover yet: just re-encode animation.mp4 into deliverables
        cmd = (
            f'ffmpeg -y '
            f'-i "{anim_mp4}" '
            f'-c:v libx264 -pix_fmt yuv420p -an '
            f'"{out_video}"'
        )
        print("[INFO] No docs/voiceover.wav found. Creating silent demo video.")

    run_ffmpeg(cmd)
    print(f"[OK] Demo video written to: {out_video}")


if __name__ == "__main__":
    main()
