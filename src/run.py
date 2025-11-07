from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # When executed as a script (python src/run.py), ensure the repository root
    # is on sys.path so we can import the package as src.*
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.main import main
else:
    from .main import main

if __name__ == "__main__":
    main()
