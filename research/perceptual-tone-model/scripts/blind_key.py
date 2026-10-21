"""Attach frozen results to an already sealed private key; never evaluate."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.blind_key import attach_key

if __name__ == "__main__":
    print(json.dumps(attach_key(), indent=2))
