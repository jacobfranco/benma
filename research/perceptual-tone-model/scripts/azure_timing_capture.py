"""Research-only replay using the existing Azure transport and exact grapheme mapper."""

import json
import os
import sys
import time
import wave
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services/api/src"))

from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer  # noqa: E402
from benma_api.pronunciation.azure_alignment import (  # noqa: E402
    AZURE_TIMING_CONFIG,
    azure_grapheme_units,
)
from benma_api.pronunciation.evidence_region import select_tone_evidence  # noqa: E402
from benma_api.pronunciation.pitch_evidence import (  # noqa: E402
    build_pitch_track,
    display_from_track,
)
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence  # noqa: E402
from benma_api.speech.providers.azure import request_azure_speech  # noqa: E402
from dotenv import dotenv_values  # noqa: E402

PACKAGE = ROOT / "research/perceptual-tone-model"
OUT = PACKAGE / "data/generated/azure-timing-replay-v1"
REFERENCE = PACKAGE / "data/generated/three-take-stability-v1"
TEXT = "我想买这个"


def save(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def capture():
    credentials = {**dotenv_values(ROOT / "services/api/.env"), **os.environ}
    key, region = (
        credentials["BENMA_AZURE_SPEECH_KEY"],
        credentials["BENMA_AZURE_SPEECH_REGION"],
    )
    manifest = json.loads((OUT / "freeze-manifest.json").read_text())
    for tid in manifest["take_order"]:
        folder = OUT / tid
        folder.mkdir(exist_ok=True)
        audio = REFERENCE / "frozen" / tid / "canonical.wav"
        if (folder / "capture.json").exists():
            print(tid, "already captured; no repeated provider call", flush=True)
            continue
        if (folder / "azure-raw.json").exists():
            raise ValueError("partial_capture_requires_explicit_recovery")
        total = time.perf_counter()
        with wave.open(str(audio)) as stream:
            assert (stream.getframerate(), stream.getnchannels(), stream.getsampwidth()) == (
                16000, 1, 2
            )
            duration = stream.getnframes() / stream.getframerate()
        start = time.perf_counter()
        try:
            raw = request_azure_speech(
                audio=audio.read_bytes(), key=key, region=region,
                config={**AZURE_TIMING_CONFIG, "ReferenceText": TEXT}, timeout_seconds=12,
            )
        except Exception as error:
            save(folder / "provider-failure.json", {
                "error_type": type(error).__name__,
                "request_seconds": time.perf_counter() - start,
            })
            raise
        request_seconds = time.perf_counter() - start
        save(folder / "azure-raw.json", raw)
        start = time.perf_counter()
        units = azure_grapheme_units(raw, TEXT, duration_seconds=duration)
        parsing_seconds = time.perf_counter() - start
        start = time.perf_counter()
        analyzer = PraatAcousticAnalyzer()
        acoustics = analyzer.analyze(audio)
        track = build_pitch_track(
            acoustics, audio_sha256=json.loads(
                (REFERENCE / "frozen" / tid / "report.json").read_text()
            )["audio_sha256"],
            tracker_source=analyzer.algorithm_name,
            tracker_version=analyzer.algorithm_version,
            parameters=analyzer.parameters,
        )
        graph = sentence_pitch_evidence(
            acoustics["f0"], display_from_track(track), [], track=track
        ).model_dump(mode="json")
        f0_seconds = time.perf_counter() - start
        old_graph = json.loads((REFERENCE / "full-acoustics.json").read_text())[tid]["graph"]
        assert graph == old_graph, "fresh_f0_does_not_reproduce_frozen_graph"
        start = time.perf_counter()
        # Existing conservative, audio-only boundary selector. It may leave spans intact.
        regions = {
            str(u["syllable_index"]): asdict(select_tone_evidence(
                acoustics["f0"], u["start_seconds"], u["end_seconds"]
            ))
            for u in units
        }
        derivation_seconds = time.perf_counter() - start
        save(folder / "acoustics.json", {"graph": graph, "raw": acoustics})
        result = {
            "take_id": tid, "reference_text": TEXT, "duration_seconds": duration,
            "units": units, "conservative_regions": regions,
            "latency": {
                "azure_request_seconds_including_transport_json_decode": request_seconds,
                "timestamp_parsing_seconds": parsing_seconds,
                "f0_seconds": f0_seconds,
                "conservative_region_derivation_seconds": derivation_seconds,
                "capture_total_seconds": time.perf_counter() - total,
            },
            "fresh_f0_exactly_matches_frozen": True,
        }
        save(folder / "capture.json", result)
        print(tid, json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    capture()
