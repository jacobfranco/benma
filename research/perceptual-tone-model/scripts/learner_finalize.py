"""Finalize existing learner construction; this CLI cannot release, train or score."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.common import read_json
from perceptual_tone.learner_finalization import DEFAULT, build, validate_reviews, verify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "verify", "validate-review"])
    parser.add_argument("--root", type=Path, default=DEFAULT)
    parser.add_argument("--answers", type=Path)
    args = parser.parse_args()
    if args.action == "validate-review":
        if not args.answers:
            parser.error("--answers is required")
        verify(args.root)
        result = validate_reviews(read_json(args.root / "qa/packet.json"), read_json(args.answers))
    else:
        result = {"build": build, "verify": verify}[args.action](args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
