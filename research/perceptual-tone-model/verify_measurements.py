"""Replay existing measurement audits into temporary files, never saved history.

Run from repository root with PYTHONPATH=. services/api/.venv/bin/python
research/perceptual-tone-model/verify_measurements.py
"""
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from benchmark.pronunciation_v2 import gesture_readability_audit as historical
from benchmark.pronunciation_v2.pitch_robustness_replay import FIXTURE, ROOT, replay


def main():
    original = historical.OUT
    fixture = ROOT / "services/api/tests/fixtures/pitch_projection_89cee47e.json"
    write_text = Path.write_text
    with tempfile.TemporaryDirectory(prefix="benma-baseline-") as directory:
        out = Path(directory)
        shutil.copyfile(original / "calibration-corpus.json", out / "calibration-corpus.json")

        def isolated_write(p, *args, **kwargs):
            destination = out / p.name if p == fixture else p
            assert destination.parent == out, f"Unexpected audit write: {destination}"
            return write_text(destination, *args, **kwargs)

        with patch.object(historical, "OUT", out), patch.object(Path, "write_text", isolated_write):
            historical.run()
        for name in ("calibration-corpus.json", "projection-replay.json"):
            assert (out / name).read_bytes() == (original / name).read_bytes(), name
        assert (out / fixture.name).read_bytes() == fixture.read_bytes()
    published = json.loads((ROOT / "apps/mobile/src/__tests__/fixtures/pitchRobustnessPhysical.json").read_text())
    for saved, expected in zip(json.loads(FIXTURE.read_text()), published, strict=True):
        for audio_root in (None, ROOT / "services/api/var/audio"):
            result = replay(saved, audio_root=audio_root)
            assert result["analysis"] == expected
            assert all(f["selected_f0_hz"] == f["raw_f0_hz"]
                       for f in result["track"]["frames"] if f["selected_f0_hz"] is not None)
    print("PASS: 13 recordings / 53 units, historical projection and corpus byte-identical; "
          "two newest physical fixtures equal after saved-evidence and canonical-WAV replay; "
          "selected F0 equals raw F0.")


if __name__ == "__main__":
    main()
