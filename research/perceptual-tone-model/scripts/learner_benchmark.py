"""Offline learner benchmark CLI. Default actions stop before human QA and prediction."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.learner_benchmark import DEFAULT, build, prepare, release, verify_inputs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "build", "verify", "release"])
    parser.add_argument("--root", type=Path, default=DEFAULT)
    parser.add_argument("--answers", type=Path)
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.action == "release":
        if not args.answers or not args.version:
            parser.error("release requires --answers and --version after real human QA")
        result = release(args.root, args.answers, args.version)
    elif args.action == "verify":
        verify_inputs(args.root)
        result = {"preservation": "passed"}
    else:
        result = {"prepare": prepare, "build": build}[args.action](args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
