"""Construct the packet, or verify its preservation; never score annotations."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.blind_packet import build, verify_preservation

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    args = parser.parse_args()
    print(json.dumps(build() if args.command == "build" else verify_preservation(), indent=2))
