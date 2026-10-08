# Shipping decision

**Do not promote a presence change or advance to physical smoke/checkpoint.** The bounded DSP audit did not identify a safe fix. Production remains byte-for-byte unchanged. The user-labelled accidental silence still passes, so the requested rejection outcome is **not achieved**.

## Six explicit decisions

1. **OVERLY PERMISSIVE ACOUSTIC GATE** — dominant software cause. Above-background activity makes the guard skip its post-ASR corroboration path; independent periodicity also defeats the absence predicate. This describes the branch, not the unproven physical source. ASR text/confidence did not cause this particular accept, although the existing fallback depends on Han count.
2. **NO SAFE RULE FOUND** — five generic, language-free acoustic policies over a frozen corpus and ±20% neighborhoods all accept the newest negative. Policies that reduce other negatives reject real short voice. No safe production threshold is supported by this experiment.
3. **FIX RELIES TOO HEAVILY ON ASR/LANGUAGE** — the negative shipping criterion applies to the retained legacy fallback, not a new fix. There is no new fix to ship. All 37 real positive waveforms/excerpts accept without transcript, so valid Mandarin/lexical coherence is not required for those positives; however changing the periodic negative's Han count changes its decision. We cannot truthfully choose whole-detector language independence while this remains.
4. **LOW-F0 SPEECH PRESERVED** — three protected 54–70-Hz whole-recording controls plus two excerpts remain accepted; immutable acoustic files, F0 selection, floor, projections, and eligibility remain untouched. Stricter candidates that lose the excerpts are rejected, not shipped.
5. **TRUST BLOCKERS REMAIN** — newest negative and several existing/padding controls still pass. The original and periodic silence cases reject with saved text. Four newest-negative integration cases prove the active gates still leak. Existing comparison restrictions remain in effect; no tone-graph or reference change is made.
6. **EVALUATE ONE BOUNDED LANGUAGE-INDEPENDENT VAD** — the single permitted next pass, described below. No physical smoke/checkpoint is recommended yet.

## Pre-ASR versus post-ASR responsibility

The evidence does not justify replacing the current detector with any tested acoustic-only rule. It also does not support adding a confidence-only post-ASR veto: the newest negative has near-zero negative token logprobs, while nonsense/quiet speech can be poorly recognized. Transcript presence, Mandarin validity, expected text, and lexical identity cannot be acceptance requirements.

A future validated acoustic detector should own the **same language-free presence decision** at upload and before every interpretation path, with its structured evidence persisted internally. Optional ASR diagnostics can be retained separately, but cannot rescue clear non-speech or veto speech merely for being nonlexical. This is a responsibility boundary, not an implementation claim. Existing two-stage behavior remains unchanged because no safe replacement passed.

No `SpeechPresence` contract, mobile schema or diagnostic API is changed. Its existing frozen dataclass, reasons, durations, and corroboration fields are traced in the report; the larger research feature bundle stays outside production. Raw pitch evidence remains valid debug evidence even for a rejected utterance.

## One future experiment, not performed

Evaluate **one frozen Silero VAD model** locally on CPU, with language/target/text absent and the same 48 hash-checked cases. Pin implementation/weights and provenance before execution. Evaluate only a small predeclared threshold neighborhood, record speech intervals and latency, and require newest/prior-negative rejection **and** retention of short, quiet, low-F0, native/phone and sparse controls. No alternate F0 tracker or pitch eligibility change belongs in this experiment.

The corpus contains correlated captures, excerpts, and incomplete category coverage. A passing replay would support a later physical validation, not universal detector accuracy. In particular a VAD may accept background speech/playback: the accidental file's physical source remains unknown, and a language-independent detector cannot be assumed to identify the intended speaker. Retain its negative label and report any unresolved conflict; do not optimize away speech-like gibberish or legitimate TTS controls to force a pass.

This pass did **not** download or execute a neural VAD, make provider/API requests, gather new recordings, change any protected architecture, or commit/push/deploy.
