# Measurement fidelity investigation — October 12, 2026

The reproduced problem is upstream of syllable ownership: **Praat's selected
raw pitch path is already fragmented and mostly unvoiced over 买**. The app has
not transferred a good 买 contour to 想. No production change was justified.
This is a take-specific estimator limitation in the compared evidence, not a
demonstrated regression in the dominant-gesture pass or audio preprocessing.

The matching analysis is `430fcc2e-1975-4773-b6be-fe1176349237`, recorded at
2026-10-12 01:29:16 UTC (October 11, 21:29:16 New York). Audio SHA-256:
`488e95d6012120b19e55c8c7d975d3283dc932a89c0aa9ea7e88ea394910c84b`.
It reproduces the reported three 我 fragments, two 想 fragments, three-point 买
and coherent 这个. No new provider requests or physical recordings were made.

## Proven findings and limits

- The exact canonical WAV reproduces **all 322 saved F0 frames and every field
  in those frame dictionaries** with the current tracker. Every one of the 15
  compared recordings also reproduces its complete saved F0 array.
- The problematic 买 interval has 27 tracker frames: **3 voiced, 24 unvoiced**.
  All 3 voiced outputs survive Benma's filters and ownership projection.
- Positive-frequency candidates exist in **all 27** frames. “Raw unvoiced” is
  not synonymous with “no candidates” or “the speaker was silent.”
- The displayed values, source indices, intervals, gaps and line coordinates
  match saved evidence. No coherent gesture disappears during unit slicing.
- Historical September 18 and September 28 analyzer implementations produce the
  same raw F0, strength, timestamps, energy, comparison F0 and quality flags on
  this exact problematic recording.
- No measurements, ownership rules, display transforms, classifier thresholds,
  grading policies or saved analyses were changed.

We have not established the true vocal-fold F0 of the ambiguous regions. The
data do not identify a microphone/device cause, prove genuinely unvoiced speech,
or independently certify phonetic boundaries. Provider boundaries match the
stored and rendered intervals exactly; that is a timebase check, not human
phonetic ground truth. The earlier cross-syllable-leakage hypothesis is rejected
as an explanation for the missing gesture in this take.

## Exact pipeline and the meaning of “raw”

1. `apps/mobile/src/audio/useAudioCapture.ts` uses Expo's `HIGH_QUALITY` preset.
   Installed preset: M4A/AAC on native, requested 44.1 kHz, two channels and
   128 kb/s; web requests WebM at 128 kb/s and browser audio constraints.
   All 15 actual compared originals are AAC/M4A, 44.1 kHz, two channels. Their
   decoded channels are identical (correlation 1.0), excluding stereo
   cancellation on downmix for these recordings. Actual bitrates vary with
   recording duration/encoding; they are recorded in the comparison artifact.
   Hardware processing or gain settings were not persisted.
2. `audio/service.py::canonicalize` decodes the preserved original with FFmpeg,
   `-ac 1 -ar 16000 -c:a pcm_s16le`. There is no trim, gain normalization,
   denoising, loudness filter or time stretch. Current re-decoding reproduces
   all 15 canonical WAV files byte-for-byte, with source hashes verified.
   `require_speech` inspects bytes and returns a decision; it does not rewrite
   audio. Its separate silence/ASR behavior remains out of scope.
3. `pronunciation/acoustics.py::_pcm16_mono` reads PCM16 and divides by 32768.
   `PraatAcousticAnalyzer.analyze` reads that same WAV into Parselmouth, with no
   additional resampling or amplitude adjustment. Versions are Parselmouth 0.4.7
   / Praat 6.1.38; analyzer version is 1.2.0.
4. `sound.to_pitch_ac(...)` performs autocorrelation and candidate-path selection.
   Parameters: floor 50 Hz, ceiling 550 Hz, hop 10 ms, 15 candidates, ordinary
   Hanning analysis (`very_accurate=false`), silence threshold .03, voicing
   threshold .45, octave cost .01, octave-jump cost .5 and voiced/unvoiced
   transition cost .14. The pitch window is nominally **60 ms** (3 periods at
   the floor), not the separate 40 ms RMS window. Frame centers are fitted to
   the full recording; this take runs from .032 to 3.242 s in 10 ms steps.
5. `tracker_f0_hz` is Praat's **already-selected path** frequency, or null for an
   unvoiced decision. `voicing_probability` stores its autocorrelation strength;
   it is not a calibrated probability. An unvoiced winner has strength zero
   even when other candidates have nonzero strength. `pitch_candidates` saves
   the positive candidates at/below the ceiling. Frequency/strength/timestamps
   are rounded to 3/4/4 decimals when persisted. No median smoothing or octave
   unwrapping is applied to this raw field.
6. Benma computes RMS over 40 ms; its additional energy threshold is
   `max(.003, min(3 * 10th-percentile RMS, .15 * peak RMS))`. It also compares a
   second track after a 70 Hz high-pass filter and measures 40–80 Hz spectral
   energy in a 100 ms window. These can reject selected evidence but never
   replace `tracker_f0_hz`. The bounded terminal-octave exclusion also leaves
   raw F0 and candidates intact. It rejects **zero** frames in this take.
7. `build_pitch_track → contours._reliable_pitch_contour` records retention and
   reasons (periodicity, quality, short islands, local outliers). The track's
   `raw_f0_hz` copies `tracker_f0_hz`; `selected_f0_hz` describes retention.
   `sentence_pitch_evidence.filtered` recovers unsmoothed retained Hz as
   recording-relative semitones. Smoothed/simplified `mine` is a separate
   technical display. Learner units consume `filtered`.
8. `azure_grapheme_units` converts provider recording-global 100 ns ticks to
   seconds; it does not add the word or utterance offset again. `unitPitch`
   selects owned points, `chunkPitch` unions constituents, and `shapeDisplay`
   scales their display coordinates. `unitShape → classifyPitchShape →
   classifyToneLikeness` subsequently extracts classification-only features.

Praat's local score and continuity behavior were checked against the exact
[6.1.38 path-finder source](https://github.com/praat/praat/blob/v6.1.38/fon/Pitch.cpp#L493)
and [pitch-window implementation](https://github.com/praat/praat/blob/v6.1.38/fon/Sound_to_Pitch.cpp#L289).
Its [raw-autocorrelation manual](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html)
also distinguishes candidate extraction from path selection. These references
explain the installed algorithm; no newer pitch method was substituted.

## Why 买 has only three voiced frames

The provider interval is **[1.20, 1.47)**. See the complete
[27-frame diagnostic](mai-frames.csv) and the
[saved candidates and replay scores](../../../../services/api/tests/fixtures/raw_tracker_mai_430fcc2e.json).

| Frames | Selected raw F0 | Candidate/path evidence | Benma action |
| --- | --- | --- | --- |
| 1.202, 1.212, 1.222 | 278.689, 271.166, 264.444 Hz | Strength .7372, .6739, .6416 | All retained |
| 1.232 | Unvoiced | Best 534.690 Hz, strength .5405; locally above voicing score | No voiced output to reject |
| 1.242–1.252 | Unvoiced | Strongest candidate below local voicing score | No voiced output to reject |
| 1.262, 1.272 | Unvoiced | Best 542.455 / 539.826 Hz, strength .4992 / .5153; locally above score | No voiced output to reject |
| 1.282–1.462 | Unvoiced | Every candidate below local voicing score | No voiced output to reject |

For all 买 frames, Praat's measured relative intensity is .08361–.84176, so
its silence penalty does not raise the unvoiced local score above .45. Positive
candidate local score is strength minus the configured octave penalty. Of the
24 unvoiced frames, **21 have no candidate beating .45**; the remaining three
are isolated candidates near the ceiling. The complete path prefers unvoiced
through them after transition costs.

A diagnostic-only replay disabling the two transition costs, leaving voicing
and all other settings intact, returns six voiced frames: the original first
three timestamps plus 1.232, 1.262 and 1.272. It also switches 1.212/1.222 onto
the higher branch (~546/~535 Hz). That does not recover a coherent missing
gesture and is not a proposed repair. See [experiment results](history-replay.json).

RMS across 买 is .005796–.048085; 21 of 27 frames exceed Benma's .009883961
energy gate. All 24 missing raw outputs have `energy_gated=false`: that flag
means a *voiced* estimator output was actually rejected, which did not happen
here. Some saved `selection_reason` strings misleadingly say `praat_selected`
or `below_energy_gate` even with null raw F0. The diagnostic now distinguishes
the actual stage from those fallback strings. Production persistence is intact.

Thus this is **estimator unvoicing despite candidates**, rather than absent
candidate generation or Benma removing a reliable selected contour. There is
energy in the waveform; energy alone does not prove periodic speech. We do not
claim the audio is silent, that these candidates are true F0, or that the
speaker failed to voice 买. The remaining problem is robust estimation on
ambiguous/weak-periodicity audio, with independent F0 ground truth needed before
changing selection policy.

The high 我 fragments are also already on the raw path (roughly 386–396 Hz).
Their small visual gaps at .822/.862 s come from the existing .45 periodicity
filter. 想's gap at 1.092/1.102 s has the same cause; its later arc is already
raw evidence within its span. These facts explain the appearance without
borrowing any points from neighboring intervals.

## Older good vs current problematic recordings

The same diagnostic/retracker was run on 15 saved recordings: three earlier
October 8–9 controls, three October 10 takes, and nine October 12 takes of this
phrase or its three-character prefix. “Good” here means retained coherent
pitch in the earlier replay, not a claim that every phonetic/tone label was
human-verified. The full [comparison](recording-comparison.json) includes
energy, pitch/confidence ranges, fragmentation, gaps, jumps, codec and all
syllable counts. All 15 share the same saved estimator configuration and version.

| Analysis (UTC) | Frames; raw voiced | RMS | Median voiced strength | Raw / retained fragments | 买 raw voiced / interval frames |
| --- | ---: | ---: | ---: | ---: | ---: |
| `aa12a29b`, Oct 8 21:42 | 289; 177 | .021749 | .9298 | 8 / 3 | 55 / 67 |
| `44075f37`, Oct 9 02:22 | 322; 201 | .024842 | .9416 | 7 / 3 | 66 / 89 |
| `874ae05a`, Oct 9 03:03 | 320; 162 | .024650 | .9454 | 6 / 4 | 49 / 61 |
| `0edf7789`, Oct 12 01:26 | 322; 153 | .021204 | .9173 | 7 / 3 | 54 / 66 |
| `7177c2c0`, Oct 12 01:27 | 248; 98 | .041281 | .9430 | 4 / 3 | 28 / 29 |
| `ace81b5f`, Oct 12 01:28 | 108; 60 | .025516 | .8852 | 3 / 4 | 20 / 21 |
| **`430fcc2e`, Oct 12 01:29** | **322; 117** | **.017201** | **.7041** | **9 / 7** | **3 / 27** |

Global fragments count interruptions in raw/retained voicing, not syllable
boundaries; global unvoiced runs include recording margins. The latest take's
raw range is 63.391–423.951 Hz (median 278.689), versus e.g. 52.268–138.591 Hz
(median 101.969) in `44075f37`. This is a materially different measured signal;
it does not by itself distinguish genuinely higher phonation from harmonic
mistracking. The latest take has the lowest whole-recording RMS and median
voiced strength in this comparison. Provider SNR is 10.55 dB, but a well-tracked
recent take has lower SNR (10.29 dB), so SNR or amplitude alone is not a causal
explanation. There is no systematic collapse across the newer recordings.

Device model, OS, input route and automatic gain/noise processing are absent
from the saved metadata. No hardware or speaker-condition explanation is asserted.

## Relevant history and dominant-gesture separation

| Commit / period | Material change | Evidence for this investigation |
| --- | --- | --- |
| `2499cfd`, Aug 3 | Original-preserving FFmpeg canonical ingest | Mono 16 kHz PCM conversion remains unchanged |
| `a8bdfab`, Sep 18 | Praat 1.1.0 path, energy and filter-disagreement gates; recording lifecycle work | Same problematic take reproduces all compared measurement fields with this implementation |
| `68057aa`, Sep 28 | Praat wrapper 1.2.0, explicit existing defaults, candidate retention, bounded terminal ambiguity rejection | Same raw path; zero terminal exclusions in this take; historical replay identical |
| `79b68e8`, Oct 8 | Immutable utterance-track packaging; speech-presence check at ingest | Packaging follows analyzer output; presence check does not modify WAV bytes |
| `56f6fec`, Oct 8 | Workspace/evidence UI | No analyzer or recording-format change |
| October 10 dominant-gesture work, present as uncommitted files | Feature extraction, target-independent family classification, learner policy | Frontend-only consumers of already persisted evidence; no path to PCM, `to_pitch_ac`, voiced decisions or raw persistence |

Current dirty work in `perceived.py` derives chunk presentation metadata;
schemas carry that metadata. It does not alter acoustic extraction. No current
diff touches recording capture, canonicalization, Praat parameters or raw-frame
generation. The same installed Praat build was used when testing historical
Python implementations; saved metadata also records that build for all 15 takes.
This tests historical code/config effects without claiming to reconstruct an
unrecorded older device/OS environment.

**The dominant-gesture grading/classification pass did not produce the missing
raw measurements.** Its smoothing, perturbations and dominant excursion are
private feature computations; deep-frozen input tests retain the actual late
counter-movement in the graph. No destructive classifier/UI coupling was found.

## Ownership, graph fidelity and before/after architecture

The production architecture is unchanged. Read-only audits now expose each
transition instead of relying on the final UI:

```text
original AAC → canonical PCM → Praat candidates + selected raw path
→ existing retention gates → immutable global evidence
→ accepted unit ownership → chunk union
                       ↘ learner graph (display coordinates only)
                       ↘ classification-only features → learner grade
```

| Unit | Aligned interval | Raw frames / voiced | Retained | Segments | Owned pitch extent |
| --- | --- | ---: | ---: | ---: | --- |
| 我 | [.58, .91) | 33 / 24 | 21 | 3 | .682–.902 |
| 想 | [.92, 1.19) | 27 / 25 | 22 | 2 | .952–1.182 |
| 买 | [1.20, 1.47) | 27 / 3 | 3 | 1 | 1.202–1.222 |
| 这 | [1.48, 1.79) | 31 / 16 | 15 | 1 | 1.522–1.662 |
| 个 | [1.80, 2.25) | 45 / 21 | 18 | 1 | 1.812–1.982 |

All intervals use `[start, end)`, **including the final unit**. The accepted
tiny-overlap policy gives ownership to the later start, then the later perceived
index for equal starts. No duplicate individual ownership, padding, rounded
millisecond slicing or local/global offset addition is introduced. Unaligned
gaps stay global-only: the single retained point at **1.192 s** is in the
provider's 10 ms gap and is not arbitrarily donated to either syllable.
这个 is a union of its two constituent projections (15 + 18 points), preserving
the gap and separate segments. See [ownership summary](ownership-summary.json).

Display maps source time affinely into the accepted span and pitch into the
local domain; it does not move timestamps or change evidence. Source order,
every retained extremum and segment boundary are retained. The new regression
inverts projected coordinates to verify source geometry at different widths and
durations. Browser checks also reconstruct rendered line endpoints from actual
DOM transforms; they match the production source projection within .1 px.

No production behavior was “restored” because no misassignment or projection
regression was demonstrated. The same fragmented evidence remains visible;
there is **no claim that the missing pitch has been recovered**.

## Diagnostics and regression coverage

- `measurement_audit.cjs`: per-unit raw/retained timestamps, original segment and
  frame identities, provider word/chunk bounds, exclusion reasons, counts,
  owned extent, classification inputs/results and normalized graph coordinates.
  Checks containment, unique ownership, ordering, loss, provenance and immutability.
  Existing `workspace_projection.cjs` accepts optional `audit: true` without
  changing its default result or PCM-crop replay behavior.
- `raw_tracker_audit.py`: one or many saved snapshots; estimator vs downstream
  rejection states, candidate lists, confidence/energy/range/fragment/gap/jump
  summaries and per-syllable counts. Optional local retracking verifies the
  audio hash and full F0 equality and exposes Praat's local scores/intensity.
  Missing legacy candidate history is reported as unavailable, not fabricated.
- `pitchMeasurement.test.ts`: five synthetic adjacent gestures at zero and
  nonzero recording offsets, shared/fractional boundaries, short gaps and pauses,
  accepted overlaps, chunk union, unequal duration, rise/fall/valley/disconnected/
  sparse projection, and deep-frozen dominant-gesture/classifier separation.
- Backend projection tests verify fractional boundaries and provider global
  tick conversion on the actual take. Raw-audit tests preserve the 27-frame
  candidate/path distinction and separate real Benma rejection from estimator
  unvoicing. The new browser script exercises repeated switches and all four
  visible chunks at 320/390/412 px.

The 53-unit historical corpus and existing physical fixture retain their hashes:
`7f20f855e5059687907d1a28b4064c7b630bbe16b48633ec1e5fde70607397b3` and
`2dacaf05518f262b63293da3969cac0ae59881af329ce6eef890789cf94d56ee`.
**No historical acoustic shape/family labels changed (0 of 53)**. The newest
take is an additional fixture, not a relabeling: 我 RISING/T2, 想 UNCLEAR,
买 UNCLEAR, 这 FALLING/T4, 个 FALLING/T4 as an acoustic observation; neutral
context remains applied downstream. All prior grading and corruption safeguards
remain intact.

## Validation and continuation state

Initial dirty state was preserved in `/tmp/benma-measurement-before.diff` and
`/tmp/benma-measurement-before-untracked.tar.gz`; continuation state and all logs
are in `/tmp/benma-measurement/`. Existing tracked diff is byte-identical to
arrival. Among pre-existing untracked files, only `workspace_projection.cjs`
and `test_pitch_projection_contract.py` changed in this pass. All other prior
work and frozen artifacts were preserved.

The [working-tree record](working-tree.txt) contains the exact final
`git diff --stat` and `git status --short`, plus the files specific to this pass.
Git's tracked diff stat excludes the pre-existing and newly created untracked
files; its unchanged 14-file/653-insertion/60-deletion total is not this pass's
change count.

| Check | Final result |
| --- | --- |
| Focused graph/workspace/shape/family/grading/chunk native and web | 319 tests / 14 suites pass |
| New raw candidate audit | 8 tests pass (also in broader result below) |
| Acoustic frontend, canonical audio, pitch evidence/projection, graph, chunk and research Python | 192 tests pass |
| Production tone replay | 2 tests pass; existing numeric report unchanged |
| Measurement replay | 2 tests pass |
| Saved gesture/PCM audit | 53 units replay; frozen corpus unchanged |
| `npm run validate` | Lint, typecheck and 653 tests / 41 suites pass |
| Expo web export | Pass; identical production bundle hash to previous export |
| New physical measurement browser | 320/390/412 px pass, rendered coordinates match, no overflow/page errors |
| Existing tone-feedback browser | 320/390/412 px pass including playback, chunks, grading, history, focus and details |
| Numeric source checks | 15/15 complete F0 replays and 15/15 canonical WAV re-decodes identical |
| Python Ruff / whitespace | Pass |

Initial checks caught a missing `mine` field in the synthetic test's TypeScript
fixture, cross-VM array prototypes in a Node assertion, and Python formatting.
These were corrected in the tests/tooling. A browser test initially used client
width instead of React Native Web's border-box `onLayout` width; correcting the
test made its rendered-coordinate check pass. No production graph change was
needed. Local database reads used read-only transactions; loopback/Chromium
execution required sandbox escalation and completed. Existing React test-renderer
warnings remain in logs. No validation is left blocked.

Exact repeatable commands are in [commands.md](commands.md). Screenshots were
visually inspected for 我/想 fragments, sparse 买 and the combined 这个 at the
existing mobile widths; they remain local under `/tmp/benma-measurement/browser/`.

## Remaining work

If better measurement coverage is required on recordings like this one, the next
task is estimator robustness with independently checked F0/audio and varied
capture conditions. It needs evidence beyond a plausible Tone 3 template or a
lowered threshold. This investigation supplies the trace and comparison controls.

The separate near-silence/background-audio ghost-transcript issue remains
unresolved and **untouched**. No VAD, ASR provider, silence threshold or transcript
corroboration behavior changed. No commit, push or deployment occurred.
