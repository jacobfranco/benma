"""Read only the three frozen WAVs; retain full-utterance evidence, including gaps."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services/api/src"))

from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer  # noqa: E402
from benma_api.pronunciation.pitch_evidence import (  # noqa: E402
    build_pitch_track,
    display_from_track,
)
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence  # noqa: E402


def main(folder):
    import parselmouth

    manifest = json.loads((folder / "freeze-manifest.json").read_text())
    results, cross_correlation = {}, {}
    for tid in manifest["take_order"]:
        take = folder / "frozen" / tid
        report = json.loads((take / "report.json").read_text())
        analyzer = PraatAcousticAnalyzer()
        start = time.perf_counter()
        raw = analyzer.analyze(take / "canonical.wav")
        track = build_pitch_track(
            raw,
            audio_sha256=report["audio_sha256"],
            tracker_source=analyzer.algorithm_name,
            tracker_version=analyzer.algorithm_version,
            parameters=analyzer.parameters,
        )
        graph = sentence_pitch_evidence(
            raw["f0"], display_from_track(track), [], track=track
        ).model_dump(mode="json")
        results[tid] = {
            "raw": raw,
            "graph": graph,
            "parameters": analyzer.parameters,
            "seconds": time.perf_counter() - start,
            "audio_sha256": report["audio_sha256"],
        }
        # Independent estimator check, same physical range/costs; never replaces F0.
        parameters = {
            k: v for k, v in analyzer.parameters.items() if k not in {"energy_gate", "quality_gate"}
        }
        cc = parselmouth.Sound(str(take / "canonical.wav")).to_pitch_cc(**parameters)
        cross_correlation[tid] = {
            "method": "Praat raw cross-correlation; same range/costs as AC; never substituted",
            "parameters": parameters,
            "frames": [
                {"t": float(t), "hz": float(hz) if hz else None}
                for t, hz in zip(cc.xs(), cc.selected_array["frequency"], strict=True)
            ],
        }
    (folder / "full-acoustics.json").write_text(
        json.dumps(results, ensure_ascii=False, allow_nan=False) + "\n"
    )
    (folder / "cross-correlation-check.json").write_text(
        json.dumps(cross_correlation, indent=2, allow_nan=False) + "\n"
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
