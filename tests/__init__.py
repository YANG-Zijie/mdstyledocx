from __future__ import annotations

import sys
from pathlib import Path

# Allow `python -m unittest` to import the package from the local `src/` layout.
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
