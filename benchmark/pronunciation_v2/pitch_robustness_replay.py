"""Offline re-selection of frozen physical evidence; optional private WAV verification.

Never writes the database or invokes providers. Raw F0/candidates and alignment
are asserted equal. Saved history remains immutable; outputs are new projections.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.contours import classify_contour, syllable_contour
from benma_api.pronunciation.pitch_evidence import (
    build_pitch_track,
    display_from_track,
    gate_observation,
    interpretation_eligibility,
    project_pitch,
)
from benma_api.pronunciation.pitch_rejection import (
    reject_ambiguous_branches,
    reject_background_pitch,
)
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence
from benma_api.schemas import PerceivedAnalysisData

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "services/api/tests/fixtures/pitch_robustness_physical.json"


def replay(saved: dict, *, audio_root: Path | None = None) -> dict:
    result = copy.deepcopy(saved["acoustic"]["result"])
    analyzer = PraatAcousticAnalyzer()
    if audio_root:
        path = audio_root / saved["audio"]["storage_key"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == saved["audio"]["sha256"]
        result = analyzer.analyze(path)
    else:
        # Background spectra are frozen from a verified local audio replay, not
        # inferred from F0 or target text. Without them, no new background waiver.
        if background := saved.get("background_periodicity"):
            reject_background_pitch(result["f0"], background)
            result["background_periodicity"] = background
        reject_ambiguous_branches(result["f0"])
    for before, after in zip(saved["acoustic"]["result"]["f0"], result["f0"], strict=True):
        for key in (
            "timestamp_seconds",
            "tracker_f0_hz",
            "f0_hz",
            "pitch_candidates",
            "voicing_probability",
        ):
            assert before[key] == after[key], key
    track = build_pitch_track(
        result,
        audio_sha256=saved["audio"]["sha256"],
        tracker_source=analyzer.algorithm_name,
        tracker_version=analyzer.algorithm_version,
        parameters=analyzer.parameters,
    )
    display = display_from_track(track)
    data = PerceivedAnalysisData.model_validate(saved["data"])
    data.pitch_track_evidence_id = track.evidence_id
    data.display_contour = display
    for s in data.syllables:
        s.pitch_projection = project_pitch(
            track,
            s.start_seconds,
            s.end_seconds,
            timing_source=s.timing_source,
            timing_evidence_id=s.timing_evidence_id,
        )
        s.pitch_eligibility = interpretation_eligibility(track, s.pitch_projection)
        s.display_contour = syllable_contour(display, s.start_seconds, s.end_seconds)
        s.observed_contour = gate_observation(
            classify_contour(
                s.display_contour,
                s.start_seconds,
                s.end_seconds,
                raw=result["f0"],
                pitch_track=track,
            ),
            s.pitch_eligibility,
        )
    data.tone_graph = sentence_pitch_evidence(
        result["f0"], display, data.syllables, data.timing_groups, track=track
    )
    output = {
        k: copy.deepcopy(v)
        for k, v in saved.items()
        if k not in {"acoustic", "audio", "background_periodicity"}
    }
    output["data"] = data.model_dump(mode="json")
    for before, after in zip(saved["data"]["syllables"], output["data"]["syllables"], strict=True):
        for key in (
            "characters",
            "start_seconds",
            "end_seconds",
            "timing_source",
            "lexical_tone",
            "expected_surface_tone",
        ):
            assert before[key] == after[key]
    return {
        "analysis": output,
        "track": track.model_dump(mode="json"),
        "background": result.get("background_periodicity"),
        "selection": result.get("selection"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [replay(s, audio_root=args.audio_root) for s in json.loads(FIXTURE.read_text())]
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
