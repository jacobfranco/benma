"""Release and evaluation-only learner workflow. No train/adapt command."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["freeze", "verify", "infer", "reproduce", "compare"])
    parser.add_argument("--phase", choices=["primary", "diagnostic", "unknown"], default="primary")
    args = parser.parse_args()
    if args.action in ("freeze", "verify"):
        from perceptual_tone.learner_release import freeze, verify_release

        result = freeze() if args.action == "freeze" else verify_release()
    else:
        from perceptual_tone.learner_transfer import infer, representation_comparison, reproduce

        result = (
            representation_comparison()
            if args.action == "compare"
            else (infer if args.action == "infer" else reproduce)(args.phase)
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
