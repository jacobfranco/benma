# Pronunciation evidence architecture

```text
PronunciationTarget (lexical reading + surface expectation)
     ├── ReferenceSpeechAsset ── AudioAsset ── reference acoustic contour
     └── PronunciationAttempt ── Utterance (original + canonical audio)
                                  ├── AssessmentRun
                                  ├── AcousticRun
                                  ├── AlignmentRun
                                  └── PronunciationInterpretationRun
```

Every run is append-only. A normal refresh reuses the current algorithm/provider/version run.
Explicit rerun flags append evidence. Interpretation stores its input run IDs, interpreter version,
and configuration. `scripts/replay_interpreter.py` replays those immutable inputs and emits a stable
observation diff without changing assessment, acoustics, alignment, or paying a provider again.

Capability maturity is `unavailable`, `raw_evidence`, `experimental`, or `calibrated`. Current
provider scores, F0, and boundaries are raw evidence. Deterministic surface-tone expectations and
tone-mismatch interpretations are experimental. Categorical tone judgment and intelligibility
inference are unavailable. Backend `pronunciation_capability_policy` centralizes wording maturity;
React receives structured policy rather than inventing verdict language. Calibration scope is a
separate `NONE/PERSONAL/PILOT_POPULATION/GENERAL` axis.

Result precedence is invalid recording → suppress interpretation; invalid alignment → suppress syllable pitch slicing; missing provider tone → acoustic/phone observations only; provider/acoustic disagreement → show conflict; agreement → stronger experimental wording, never a calibrated verdict.

The stable mobile DTO merges evidence for display but not persistence. Raw provider schemas never enter React components. No dimensions are averaged into a Benma score. Reference speech sends target text only; assessment sends canonical learner audio and the known target; no analytics SDK receives audio.

Pitch persistence retains full resolution. The DTO includes a min/max-bucket series capped at 240 points, preserving gaps and extrema. Reference and learner F0 are separately normalized to utterance-relative semitones. Neither one-syllable baseline claims a speaker pitch range.

`benchmark/` and `services/api/` share no domain models. A deliberate export copies audio and metadata; production audio cannot silently become research data.
