"""Read-only local audio recomputation. No provider/service analyze calls or DB writes.

Run from services/api with --output DIR. Optional --before is a saved diagnostic
snapshot and --baseline-analyzer is a local historical acoustics.py for timing.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import time
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select, text

from benma_api.config import Settings
from benma_api.db.models import AcousticRun, AudioAsset, PerceivedSpeechAnalysis, Utterance
from benma_api.db.session import get_session_factory
from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer, _pcm16_mono
from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.diagnostic import diagnostic

PHONE = [
    "2ce6de8e-d61d-4d83-be64-41abcf764572",
    "1243aa80-bf81-4a52-b0e8-248ca15e2039",
    "618b19d5-8039-46bc-9a32-fe157cd025f3",
    "a6246719-be84-410c-99ee-f020ce566858",
    "12df6d8f-3be8-4754-86d2-70bc19f0152d",
]
CONTROLS = [
    "c75f00c8-a680-4cf8-a37a-93455a9a14b6",
    "9957925d-83ba-4502-84d7-8adca750b81d",
    "4fbf587d-4960-4f6f-a5db-f15fd883292f",
    "0a512317-7e6d-4a25-bff0-8a7718ecdc44",
    "e7a4c6c9-d081-4590-95eb-b426c169e5ed",
    "2a6fc058-86c9-415a-ac35-8c333bf9d7dd",
    "c7b73e45-f474-4955-9a68-3f59ad032dfc",
    "b7bfdb6a-8d07-4fe1-82ea-132a18afac9a",
]


def plot(path: Path, raw: list[dict[str, Any]], start: float, end: float, output: Path) -> None:
    """Standalone SVG with measured axes and samples; no audio copied to docs."""
    rate, samples = _pcm16_mono(path)
    duration = len(samples) / rate
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620">',
        '<rect width="1100" height="620" fill="white"/>',
        "<style>text{font:14px sans-serif} .axis{stroke:#999;stroke-width:1}</style>",
        '<text x="60" y="25">Phone Tone 3 — raw waveform, measured F0 and rejected evidence</text>',
    ]

    def x(t: float) -> float:
        return 60 + t / duration * 1000

    def line(coords: list[tuple[float, float]], color: str) -> None:
        points = " ".join(f"{a:.2f},{b:.2f}" for a, b in coords)
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="1" points="{points}"/>')

    for i in range(9):
        t = i * 0.2
        parts.append(f'<path class="axis" d="M{x(t):.2f},40 V550"/>')
        parts.append(f'<text x="{x(t):.2f}" y="575">{t:.1f}s</text>')
    for bound in [start, end]:
        parts.append(f'<path stroke="#925" stroke-dasharray="4" d="M{x(bound)},40 V550"/>')
    line([(x(i / rate), 155 - samples[i] * 650) for i in range(0, len(samples), 8)], "#456")
    parts.append('<text x="60" y="55">Waveform (PCM amplitude); dashed = aligned span</text>')
    parts.append(
        '<text x="60" y="295">F0 Hz: gray raw; blue retained; red rejected; green comparison</text>'
    )
    for hz in [50, 100, 150, 200]:
        y = 550 - hz
        parts.append(f'<path class="axis" d="M60,{y} H1060"/><text x="15" y="{y}">{hz}</text>')
    retained = {p.timestamp_seconds for seg in display_contour(raw).segments for p in seg}
    for p in raw:
        t = p["timestamp_seconds"]
        for key, color in [
            ("tracker_f0_hz", "#aaa"),
            ("comparison_f0_hz", "#5a5"),
            ("f0_hz", "#167" if t in retained else "#d22"),
        ]:
            hz = p.get(key)
            if hz and hz < 240:
                parts.append(f'<circle cx="{x(t):.2f}" cy="{550 - hz:.2f}" r="2" fill="{color}"/>')
    parts.append(
        '<text x="60" y="605">No interpolation or repair. Raw F0 preserved.</text></svg>'
    )
    output.write_text("\n".join(parts))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--baseline-analyzer", type=Path)
    args = parser.parse_args()
    settings = Settings()
    if settings.environment == "production":
        parser.error("Local development only")
    args.output.mkdir(parents=True, exist_ok=True)
    before = (
        {r["id"]: r["diagnostic"] for r in json.loads(args.before.read_text())}
        if args.before
        else {}
    )
    baseline = None
    if args.baseline_analyzer:
        spec = importlib.util.spec_from_file_location("baseline_acoustics", args.baseline_analyzer)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        baseline = module.PraatAcousticAnalyzer()
    analyzer = PraatAcousticAnalyzer()
    rows = []
    with get_session_factory()() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        for identifier in PHONE + CONTROLS:
            uid = uuid.UUID(identifier)
            u = db.get(Utterance, uid)
            assert u
            asset = db.get(AudioAsset, u.canonical_audio_asset_id)
            assert asset
            path = settings.audio_storage_dir / asset.storage_key
            diag = diagnostic(db, uid)
            acoustic = db.get(AcousticRun, uuid.UUID(diag["acoustic_run_id"]))
            assert acoustic and acoustic.normalized_result
            new = analyzer.analyze(path)  # Warm imports/caches before measured repetitions.
            timings: dict[str, Any] = {"persisted_ms": acoustic.latency_ms}
            for name, engine in [("old", baseline), ("new", analyzer)]:
                if engine is None:
                    continue
                times = []
                for _ in range(7):
                    started = time.perf_counter()
                    engine.analyze(path)
                    times.append((time.perf_counter() - started) * 1000)
                timings[name] = {
                    "median_ms": round(statistics.median(times), 3),
                    "maximum_ms": round(max(times), 3),
                }
            analysis = db.scalar(
                select(PerceivedSpeechAnalysis)
                .where(PerceivedSpeechAnalysis.utterance_id == uid)
                .order_by(PerceivedSpeechAnalysis.created_at.desc())
            )
            spans = (
                diag["syllables"]
                if diag["practice_mode"] == "known_target"
                else analysis.result["syllables"]
            )
            measured = []
            for unit in spans:
                a, b = unit["start_seconds"], unit["end_seconds"]
                old_raw = acoustic.normalized_result["f0"]
                measured.append(
                    {
                        "start_seconds": a,
                        "end_seconds": b,
                        "previous_raw_recomputed": classify_contour(
                            display_contour(old_raw), a, b, raw=old_raw
                        ).model_dump(),
                        "new_audio_recomputed": classify_contour(
                            display_contour(new["f0"]), a, b, raw=new["f0"]
                        ).model_dump(),
                    }
                )
                if identifier == PHONE[2]:
                    plot(path, new["f0"], a, b, args.output / "phone-tone3.svg")
            rows.append(
                {
                    "utterance_id": identifier,
                    "before": before.get(identifier),
                    "production_result_from_persisted_evidence": diag,
                    "local_audio_recomputation": measured,
                    "selection": new.get("selection"),
                    "acoustic_parameters": analyzer.parameters,
                    "timings": timings,
                }
            )
    (args.output / "recomputation.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    for row in rows:
        print(
            row["utterance_id"],
            [
                (
                    s["previous_raw_recomputed"]["classification"],
                    s["new_audio_recomputed"]["classification"],
                    s["new_audio_recomputed"]["reason"],
                )
                for s in row["local_audio_recomputation"]
            ],
            row["timings"],
        )


if __name__ == "__main__":
    main()
