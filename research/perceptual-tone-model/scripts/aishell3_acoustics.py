"""Run the unchanged production analyzer on research WAVs, without text inputs."""
# ruff: noqa: E402 -- load the existing service package without installing/mutating it

import argparse
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.pitch_evidence import (
    build_pitch_track,
    display_from_track,
    interpretation_eligibility,
    project_pitch,
)
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence


def run(spec, output):
    analyzer = PraatAcousticAnalyzer()
    result = []
    for u in spec:
        raw = analyzer.analyze(Path(u["audio_path"]))
        track = build_pitch_track(
            raw,
            audio_sha256=u["audio_sha256"],
            tracker_source=analyzer.algorithm_name,
            tracker_version=analyzer.algorithm_version,
            parameters=analyzer.parameters,
        )
        graph = sentence_pitch_evidence(
            raw["f0"], display_from_track(track), [], track=track
        ).model_dump(mode="json")
        for unit in u["units"]:
            a, b = unit["start"], unit["end"]
            segments = [
                [p for p in seg if a <= p["timestamp_seconds"] < b]
                for seg in graph["filtered"]["segments"]
            ]
            segments = [s for s in segments if s]
            projection = project_pitch(track, a, b, timing_source="saved_alignment")
            eligibility = interpretation_eligibility(track, projection).model_dump(mode="json")
            result.append(
                {
                    "example_id": unit["example_id"],
                    "start": a,
                    "end": b,
                    "segments": segments,
                    "raw": [p for p in graph["raw"] if a <= p["timestamp_seconds"] < b],
                    "eligibility": eligibility,
                    "tracker": analyzer.algorithm_version,
                    "track_evidence_id": track.evidence_id,
                    "baseline_hz": track.baseline_hz,
                }
            )
    Path(output).write_text(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("output")
    a = p.parse_args()
    run(json.loads(Path(a.input).read_text()), a.output)
