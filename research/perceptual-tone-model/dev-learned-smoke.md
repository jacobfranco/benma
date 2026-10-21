# Dev-only learned-tone microphone smoke test

From `/home/jacob/benma`, run this one command:

```sh
benchmark/pronunciation_v2/.venv/bin/python research/perceptual-tone-model/scripts/dev_learned.py --enable-learned-dev
```

Open **http://127.0.0.1:8766** on this computer in a microphone-capable browser.
Keep the server running between takes so it retains the frozen encoder. Stop it
with Ctrl-C. The explicit flag is required; production environment settings are
rejected. The listener binds only to loopback. There is no deployment or change
to the mobile app, production API, dependencies, linguistic rules or grading.

1. Leave the phrase as **我想买这个**. Click **Start recording** and allow the
   microphone. Speak the complete sentence naturally at conversational speed.
2. Click **Stop & inspect**. Do not exaggerate tones or tune anything to pass.
3. Inspect whole-sentence, whole-syllable and nucleus/coda playback **first**.
   Then inspect probabilities, pilot and deterministic results, and the F0 chart.
4. Save an observation: plausible correction, suspicious model behavior,
   alignment failure, or insufficient evidence. Notes are not realized-tone gold.
5. Repeat naturally several times. Use **Previous take** to compare. A single
   surprise, model consensus, or “I thought it sounded fine” is not a tuning target.

Each take is saved in
`research/perceptual-tone-model/data/generated/dev-learned-takes-v1/<take-id>/`:
original audio, canonical WAV, automatic MFA evidence/log, deterministic/F0
evidence, crops, `report.json`, and append-only observation files. The browser
shows the report directly and has a download link; no manual script sequence
is necessary. Reports persist across server restarts. These are private local
research artifacts, independent of production storage/deletion.

ASR is off by default. Append `--asr` to request the existing live provider from
`services/api/.env`/Benma environment configuration; missing or failed ASR is
explicitly reported. The existing audio-only provider receives no phrase prompt.
ASR disagreement with the prompt blocks learned correction pending alignment
review. Without ASR, MFA uses the displayed phrase as an **alignment hypothesis**;
inspect playback for omitted/substituted material. Configured live ASR was not
called during automated validation.

## What the report means

Every syllable shows Hanzi/pinyin, lexical and expected surface tone, expanded
T1–T4 probabilities and raw confidence, pilot confidence, deterministic
family/abstention, whole/pooling/context spans, playback, retained F0 in relative
semitones, evidence state and interpretation. Measured gaps remain gaps in the
chart. Detailed metadata is expandable, not required to read the main report.
The existing `这个` linguistic chunk is also shown; neutral is non-veto.

The unchanged linguistic engine leaves **我/想/买 surface tones unresolved**.
Their learned predictions remain visible, but experimental grading abstains.
这 has resolved T4 expectation; 个 is neutral and has no four-tone correction.
No new sandhi policy is invented. Production `pitchExpectation` also has a
documented lexical-family fallback, but this dev comparator requires resolved
surface tone and does not promote that fallback to resolved sandhi.

`MATCH` means argmax agreement, not verified correctness.
`MODEL_CONCERN_UNTHRESHOLDED` means a numbered mismatch without a learned
confidence operating point. `MODEL_DISAGREEMENT` exposes competing secondary
families. `INSUFFICIENT_EVIDENCE` includes failed inference, invalid/short crops,
no voiced support, unresolved expectations and neutral handling. There is no
`STRONG_CONCERN`/confident-error threshold in this pass.

Tone-marked pinyin is explicitly **tone-realization rendering, not ASR lexical
transcription**. Hanzi is never replaced. A specific movement explanation needs
compatible trustworthy, full-strength deterministic evidence and finite measured
movement. Otherwise the report explicitly withholds a specific diagnosis. A
model prediction never manufactures missing F0 evidence or required T3 recovery.

## Implementation and frozen identity

`scripts/dev_learned.py` → `perceptual_tone/dev_runtime.py` →
`perceptual_tone/dev_inference.py::LearnedRecognizer.infer` → unchanged
`aishell3_embeddings.Encoder.extract` and `learner_transfer.probabilities`.
The separate `scripts/dev_service_bridge.py` calls existing canonicalization,
speech presence, lexical/contextual expectation and optional ASR functions.

The model boundary permits only `audio_reference`, `audio_sha256`, `read_unit`,
`pooling`, and `context`. MFA uses the pinned phone lexicon/acoustic model and
research lexical alignment readings (including ge4); contextual neutral handling
stays separate. No speaker adaptation is enabled. The unchanged strict
`aishell3_alignment.reconstruct` and `aishell3_boundaries.derive` provide exact
phone ownership and nucleus/coda spans with ±250 ms context. Unsupported
structure and the existing under-60 ms review flag abstain; no hand-corrected
or fabricated crops. Short diagnostic crops remain playable and clearly flagged.

Frozen Chinese HuBERT revision `fce0375452b1dd6c080ac3248d423d4d037bc831`, layer 9,
context input, nucleus/coda frame-center mean, balanced logistic regression C=0.1:

| Artifact | SHA-256 |
| --- | --- |
| Expanded `experiment_B.joblib` | `b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b` |
| Pilot `model2_hubert.joblib` | `c20cc46ed715ce5ed1f3a76f405014069f4a98c0b9e6e467ce28635b4df725d9` |
| Native release | `3bb07638eb87fe470e51831bab1e99681bfe01482136ae7f11eb7886ecd1b315` |
| Learner release manifest | `8024a51df91e60b9e336189cd9b04dfbf2d5d8c530fd0656778c731e1306f4ae` |

`configs/dev-learned-lock.json` pins inference sources, models, releases,
alignment resources and encoder weights. The deterministic baseline still runs
through the unchanged Praat and TypeScript research bridges. See
[pre-integration runtime audit](dev-runtime-audit.md) for exact production modules.

## Validation and limitations

Saved-audio E2E: approximately 19.06 s total, 12.60 s MFA, 3.24 s encoder load.
Separate four-unit measurement: 2.88 s encoder load, 54–62 ms per subsequent
uncached unit, 25 ms for four cached units; peak research-process RSS about
799–856 MiB (does not sum subprocess memory). Fresh encoder probabilities
reproduce sealed outputs within `6.67e-16`; no fitting or recalibration.

One repeated full take with the encoder retained and identical audio cached took
**17.12 s**: preparation 0.96 s, MFA 14.26 s, acoustics 1.07 s, learned results
0.025 s, report generation 0.80 s. Encoder load during this take was zero.
New physical takes do not share those cached embeddings; use the separate
54–62 ms per-unit measurement for warm uncached inference. Timing is a small
local sample, not a latency guarantee. Totals end before final JSON serialization.

Automated Chromium fake-microphone replay passed capture/upload/inference,
five syllables plus 这个, all 16 playback clips, saved-report reload, observation
storage, request isolation, and narrow-screen rendering. It is tagged
`automated_browser_replay`; it is not a fresh human take.
Prior relevant checks: 73 research tests, 206 API tests, 757 mobile tests passed.
Only focused integration tests were repeated after final integration edits.
The final focused suite has 25 tests.
Exact final timing/check artifacts are under
`data/generated/dev-learned-integration-v1/`.

MFA dominates latency. Model consensus and solo judgments still do not establish
learner perceptual correctness. Automatic alignment can be wrong despite passing
structural checks. This remains a local research workflow; new microphone takes
and independent listener validation have not been supplied by these tests.
Future presentation/abstention/wording changes remain separate from any model
change. Nothing was trained, tuned, calibrated, committed, pushed or deployed.
