"""Conservative presence checks, never a speech recognizer or pitch selector.

Low stationary background plus isolated clicks is confidently absent only when
neither sustained activity nor periodic evidence exists. Quiet periodic speech,
short recordings and louder/uncertain material pass the audio-only pre-check.
Post-ASR corroboration uses only Han count and independent acoustic support.
Neither stage accepts intended target text or supplies measured pitch geometry.
"""

from __future__ import annotations

import io
import re
import wave
from dataclasses import dataclass

import numpy as np
import parselmouth
from parselmouth.praat import call

from benma_api.errors import InvalidAudioError, NoSpeechError

VERSION = "conservative-audio-presence-v2-corroboration"


@dataclass(frozen=True)
class SpeechPresence:
    no_speech: bool
    reason: str
    background_rms: float
    activity_seconds: float
    periodic_seconds: float
    corroborated_seconds: float = 0
    corroborated_run_seconds: float = 0
    corroboration_checked: bool = False


def _longest_run(mask: list[bool], hop: float = 0.01) -> float:
    longest = current = 0
    for value in mask:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest * hop


def speech_presence(canonical: bytes) -> SpeechPresence:
    try:
        with wave.open(io.BytesIO(canonical), "rb") as stream:
            if stream.getnchannels() != 1 or stream.getsampwidth() != 2:
                raise InvalidAudioError("speech presence requires mono PCM16 WAV")
            rate = stream.getframerate()
            values = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
    except (wave.Error, EOFError) as exc:
        raise InvalidAudioError("canonical audio is not readable PCM WAV") from exc
    samples = values.astype(np.float64) / 32768
    if not len(samples):
        raise InvalidAudioError("canonical audio has no samples")
    # Only quantization-level absence is decided by amplitude alone.
    if float(np.max(np.abs(samples))) <= 1 / 32768:
        return SpeechPresence(True, "quantization_level_silence", 0, 0, 0)
    if len(samples) / rate < 0.08:
        return SpeechPresence(False, "short_uncertain", 0, 0, 0)
    width, hop = round(rate * 0.02), round(rate * 0.01)
    frames = [samples[i : i + width] for i in range(0, len(samples) - width + 1, hop)]
    energies = np.array([np.sqrt(np.mean((f - f.mean()) ** 2)) for f in frames])
    positive = energies[energies > 1 / 32768]
    background = float(np.quantile(positive, 0.2)) if len(positive) else 0.0
    # Five overlapping 20-ms windows span 60 ms. A click must not count as speech.
    activity = _longest_run((energies > max(3 * background, 3 / 32768)).tolist())
    # Praat's voicing decision is stronger evidence than a raw ACF maximum:
    # colored stationary noise can have high correlation without a stable F0.
    # This broad, amplitude-relative track has NO production energy/quality gate.
    pitch = parselmouth.Sound(samples, sampling_frequency=rate).to_pitch_ac(
        time_step=0.01,
        pitch_floor=40,
        pitch_ceiling=550,
        voicing_threshold=0.45,
    )
    periodic_duration = _longest_run((pitch.selected_array["frequency"] > 0).tolist())
    absent = background < 0.01 and activity < 0.05 and periodic_duration == 0
    # Only the ambiguous periodic-background path needs a second acoustic view.
    # Agreement after removing low-frequency background is corroboration, never
    # replacement F0. Keep the pre-ASR decision permissive for short/quiet speech.
    checked = not absent and background < 0.01 and activity < 0.05
    corroborated = np.zeros(len(pitch.xs()), dtype=bool)
    if checked:
        band = call(
            parselmouth.Sound(samples, sampling_frequency=rate),
            "Filter (pass Hann band)",
            100,
            4000,
            20,
        ).to_pitch_ac(time_step=0.01, pitch_floor=40, pitch_ceiling=550, voicing_threshold=0.45)
        original_hz, band_hz = pitch.selected_array["frequency"], band.selected_array["frequency"]
        difference = np.abs(12 * np.log2(np.maximum(1, original_hz) / np.maximum(1, band_hz)))
        corroborated = (original_hz > 0) & (band_hz > 0) & (difference <= 2)
    return SpeechPresence(
        absent,
        "stationary_background_without_sustained_activity" if absent else "speech_or_uncertain",
        background,
        activity,
        periodic_duration,
        float(np.count_nonzero(corroborated)) * 0.01,
        _longest_run(corroborated.tolist()),
        checked,
    )


def corroborate_transcript(presence: SpeechPresence, transcript: str) -> None:
    """Reject only extreme multi-unit claims with no sustained acoustic support.

    No target, semantics, reference tone or lexical identity is used. Twenty ms
    per Han unit (capped at 200 ms) is a deliberately broad impossibility check,
    not a speaking-rate rule. A 50-ms corroborated run independently rescues it.
    Single/two-unit and short-uncertain turns retain the permissive pre-check.
    """
    units = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", transcript))
    if presence.no_speech or (
        units >= 3
        and presence.corroboration_checked
        and presence.corroborated_seconds + 1e-9 < min(units, 10) * 0.02
        and presence.corroborated_run_seconds < 0.05
    ):
        raise NoSpeechError("Didn't catch any speech. Try again.")


def require_speech(canonical: bytes, *, transcript: str | None = None) -> SpeechPresence:
    presence = speech_presence(canonical)
    corroborate_transcript(presence, transcript or "")
    return presence
