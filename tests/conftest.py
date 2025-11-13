# tests/conftest.py
import sys
from pathlib import Path

# Project root = the directory that contains "src"
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

# Add src/ to sys.path so `import deconflict` works in tests
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
