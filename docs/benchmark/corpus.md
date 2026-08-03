# Corpus specification

Corpus ID: `benma-mandarin-truthfulness`; schema `1.0.0`; pilot version `0.1.0`.

The full target is 384 recorded utterances. The checked-in manifest materializes 114 prompt/case
definitions so recording can begin without pretending audio exists. `status=planned` and
`audio=null` are truthful states. New samples are data entries, not code changes.

## Target allocation

| Stratum | Eventual target | Pilot definition |
|---|---:|---|
| Isolated tones, correct/wrong/repetitions | 48 | all four tones, three controls plus wrong realization |
| 16 tone pairs | 64 | all combinations represented by real words |
| Tone-sensitive lexical items | 40 | includes 买/卖, 水/睡, 生活, 后面, 睡觉 |
| Sandhi/neutral/weak syllables | 48 | T3 contexts, 一, 不, neutral tone |
| Initial/final/aspiration contrasts | 64 | English-speaker priority inventory |
| Exact-one-error sentences | 72 | tone, initial, final, syllable/word substitution, omission, Americanization, prosody, control |
| Adversarial context base audio | 24 | identical audio reused in A/B/C provider probes |
| Negative/noise/delivery/native controls | 24 | silence, nonsense, clipping, level, mild noise, rate, exaggeration |
| **Total** | **384** | strata expand by speakers and repetitions |

The counts intentionally reserve multiple speakers/repetitions rather than multiplying text prompts
prematurely. Recruit at least six native controls and twelve learners across levels for the first
credible subset. Pseudonymous speaker IDs must not encode name, email, or exact birth date.

## Blind metadata boundary

`BenchmarkSample` contains research ground truth because corpus curation needs it. Providers never
receive that object. `sample.perception_request()` constructs a separate closed model containing
only sample ID, audio, Mandarin language hint, and timeout. Human blind tooling loads audio before
displaying any target; target reveal is a separate command after a hashed blind commit.

## Recording rules

- Quiet, close-mic is the central condition. Noise examples are a bounded control, not the focus.
- Preserve original capture bytes under `recordings/original/`.
- Generate, never overwrite, canonical mono 16 kHz 16-bit PCM WAV under `recordings/canonical/`.
- Record microphone/device/software/environment when known.
- For an intentional error, specify exactly one primary error and rehearse it before recording.
- Fill `produced_form` after the speaker/researcher confirms what was attempted; do not derive it
  from ASR output.
- Native controls should be natural Standard Mandarin, not exaggerated textbook contours.

## Context probes

A single recording is identified once and run under three experimental conditions:

- A: raw audio and language hint only — the only production-compatible condition.
- B: a congruent prompt supplied through the research-only context-probe contract.
- C: a misleading but plausible prompt through the same research-only contract.

The B/C runner must be implemented per provider outside `UnknownTargetPerceptionProvider`; prompt
support must never be added to `UnknownTargetPerceptionRequest`.

## Versioning

Correcting pinyin/tones in a released manifest requires a new corpus version and a migration note.
Adding recordings to planned entries does not change the semantic corpus version, but it changes
the asset manifest and hashes. Never reuse a sample ID for different audio. Corpus releases should
publish manifest hash, asset hashes, consent/usage scope, and annotation snapshot ID.

