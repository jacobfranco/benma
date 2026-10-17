#!/usr/bin/env python3
"""Research entry point; no installation or application import required."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from perceptual_tone.cli import main

if __name__ == "__main__":
    main()
