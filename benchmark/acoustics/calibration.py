"""Generate clearly labeled synthetic calibration audio and diagnostic plots."""

from __future__ import annotations

import math
import struct
import wave
from collections.abc import Callable
from pathlib import Path

from benchmark.acoustics.pitch import AutocorrelationPitchAnalyzer
from benchmark.acoustics.plot import write_diagnostic_svg
from benchmark.storage import write_model


def _write_contour(
    path: Path,
    contour: Callable[[float], float],
    *,
    duration: float,
    amplitude: float = 0.35,
    sample_rate: int = 16000,
) -> None:
    phase = 0.0
    values: list[int] = []
    total = round(duration * sample_rate)
    for index in range(total):
        fraction = index / max(1, total - 1)
        frequency = contour(fraction)
        phase += 2 * math.pi * frequency / sample_rate
        fade = min(1.0, index / (sample_rate * 0.02), (total - index) / (sample_rate * 0.02))
        values.append(round(32767 * amplitude * max(0.0, fade) * math.sin(phase)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(struct.pack(f"<{len(values)}h", *values))


def materialize_acoustic_calibrations(root: Path) -> int:
    """Write synthetic curves used only to sanity-check analysis and plotting."""
    cases: dict[str, tuple[Callable[[float], float], float, float]] = {
        "synthetic_t1_level": (lambda x: 250.0, 0.8, 0.35),
        "synthetic_t2_rising": (lambda x: 150.0 + 120.0 * x, 0.8, 0.35),
        "synthetic_t3_dipping": (
            lambda x: 220.0 - 180.0 * x if x < 0.6 else 112.0 + 170.0 * (x - 0.6),
            0.9,
            0.35,
        ),
        "synthetic_t4_falling": (lambda x: 290.0 - 190.0 * x, 0.7, 0.35),
        "synthetic_wrong_t2_as_t3": (
            lambda x: 220.0 - 170.0 * x if x < 0.6 else 118.0 + 150.0 * (x - 0.6),
            0.8,
            0.35,
        ),
        "synthetic_t3_sandhi_rising": (lambda x: 140.0 + 105.0 * x, 0.65, 0.35),
        "synthetic_neutral_short": (lambda x: 185.0 - 25.0 * x, 0.25, 0.25),
        "synthetic_low_confidence": (lambda x: 200.0, 0.6, 0.001),
    }
    analyzer = AutocorrelationPitchAnalyzer()
    for name, (contour, duration, amplitude) in cases.items():
        audio = root / f"{name}.wav"
        result_path = root / f"{name}.json"
        plot = root / f"{name}.svg"
        _write_contour(audio, contour, duration=duration, amplitude=amplitude)
        result = analyzer.analyze(str(audio))
        write_model(result_path, result)
        write_diagnostic_svg(
            audio,
            result,
            plot,
            title=f"SYNTHETIC CALIBRATION — {name}",
        )
    return len(cases)
