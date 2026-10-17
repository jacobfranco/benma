# AISHELL-3 boundary remediation and Round-2 handoff — 2026-10-17

**Round 2 is ready; training and dataset release remain blocked.** Round 1 has
26 identified reviews: 18 PASS, seven BOUNDARY EARLY and one OTHER. These are
ownership/timing judgments, not tone judgments. No decision has been reversed.

The continuation reused existing audio, MFA TextGrids, dictionaries and speaker
partitions. There was no acquisition, MFA rerun, encoder execution, training,
commit, push or deployment. The earlier development packet remains in `round2/`;
the final developer packet is **`round2-final/index.html`**.

## What was established

All eight failures trace identically through original MFA word/phone tiers,
read-unit reconstruction, stored timestamps and exported source PCM. All 78
original clips match source PCM at their recorded sample bounds. Corpus and
canonical repaired-RIFF PCM are equivalent; stale outer RIFF lengths do not move
samples. Phone sequences agree with the supplied dictionary, ordered speech
phones have one owner, and there is no inserted internal silence or fractional
allocation across read units. Diphthongs such as /ow/ and /aj/ are indivisible
phones here. Original waveform/spectrograms were inspected for all eight failures
and corresponding PASS controls; these are visual acoustic observations, not new
human listening verdicts or independent hand-aligned ground truth.

Browser playback loads a standalone WAV and starts at zero. It does not seek into
an utterance to approximate target start/end. Chromium tests verify every original
clip's decoded frame count and corresponding normalized sample values. Its PCM16
normalization uses negative /32768 and positive /32767; that tiny amplitude
convention is not a temporal displacement. Browser/device behavior in the original
human listening session cannot be reconstructed from the export.

**No clear material MFA error, reconstruction error or extraction error is proven.**
Three cases are provisionally consistent with fuzzy/coarticulatory boundaries;
five remain uncertain. This is not proof that MFA boundaries are acoustically
correct. In particular, the possibly clipped /ow/ final remains unresolved.

## Sample extraction correction

Independent `floor(start * rate)` / `ceil(end * rate)` calls can disagree at an
identical source time because of binary floating-point representation. For example,
`2.2 * 44100` lies just above 97020 in floating point: `ceil` adds an extra sample.
The original full dataset has **82 adjacent overlaps of one sample**.

The new version uses a single nearest-sample function:
`Decimal(str(seconds)) * rate`, rounded half up, and half-open `[start, end)` slices.
Thus `[q(a), q(b))` plus `[q(b), q(c))` reconstructs `[q(a), q(c))` with neither
repetition nor a gap. The fix changes at most one sample per edge in 100/787 whole
unit clips and removes all 82 overlaps. Original second timestamps, audio PCM,
MFA phones, original clips and original read-unit spans remain untouched.

**One sample is 0.022676 ms at 44.1 kHz. This defect does not explain the human
failures and its correction does not establish perceptual improvement.** Of the
original 26 targets, only `SSB00800453:0` (PASS wo2) and `SSB00800453:6` (failed ni3)
lose an extra ending sample. All 26 context clips remain byte-identical to Round 1.

## Eight failures

The structured [failure inventory](data/generated/aishell3/round2-final/failure-inventory.jsonl)
retains reviewer Jacob, original timestamp, decision, verbatim notes, original item
hash and packet hash; speaker/utterance, neighbors, tone, all target phones,
neighbor phone boundaries, stages A–E and derived spans. Original JSON bytes are
archived at `data/generated/aishell3/round2/round1-export.json`; normalized decisions
remain in `continuation/playback-decisions.jsonl`.

| Example ID | Unit / tone | Original s | Candidate s | Note-based category | Root class |
|---|---|---|---|---|---|
| `aishell3:SSB00430370:4` | 狂 kuang2 / T2 | 1.270–1.620 | 1.430–1.620 | UNCLEAR | UNCERTAIN |
| `aishell3:SSB00730202:16` | 同 tong2 / T2 | 4.080–4.320 | 4.190–4.320 | MULTI_EDGE + UNCLEAR | UNCERTAIN |
| `aishell3:SSB01390195:3` | 阳 yang2 / T2 | 0.890–1.190 | 1.000–1.190 | START_TOO_EARLY | COARTICULATORY / FUZZY BOUNDARY |
| `aishell3:SSB00090400:1` | 投 tou2 / T2 | 0.400–0.600 | 0.500–0.600 | END_TOO_EARLY | UNCERTAIN |
| `aishell3:SSB00800453:6` | 你 ni3 / T3 | 1.880–2.200 | 1.980–2.200 | START_TOO_EARLY | COARTICULATORY / FUZZY BOUNDARY |
| `aishell3:SSB00050353:4` | 总 zong3 / T3 | 2.020–2.400 | 2.160–2.400 | START_TOO_EARLY | COARTICULATORY / FUZZY BOUNDARY |
| `aishell3:SSB00570040:6` | 库 ku4 / T4 | 1.590–1.770 | 1.710–1.770 | START_TOO_LATE | UNCERTAIN |
| `aishell3:SSB01120199:3` | 是 shi4 / T4 | 0.520–0.660 | 0.620–0.660 | START_TOO_LATE | UNCERTAIN |

**kuang2 — aishell3:SSB00430370:4**

Human note: "slightly early, gets a little clipping before the consonant"

Slightly early suggests preceding material, but clipping before the consonant does not identify what was clipped. START_TOO_EARLY is possible; edge direction is unconfirmed.
The start is near the decay into the stop interval; periodic energy follows the preceding vowel. The assigned stop, medial, vowel and nasal are complete in the crop. This does not establish their acoustic boundaries.

**tong2 — aishell3:SSB00730202:16**

Human note: "BOUNDARY LATE AND BOUNDARY EARLY.  "

The note explicitly reports both boundary problems but gives neither edge-specific direction nor neighboring sound. Do not turn the enum words into geometric corrections.
The start cuts through a continuing periodic transition before the stop release. The nasal-to-affricate ending is also continuous. Neither edge has a unique boundary established by the plot.

**yang2 — aishell3:SSB01390195:3**

Human note: "Can hear the \"ai\" from \"tai\" at the beginning"

Explicit preceding tai4 diphthong is audible in the target start.
The aj-to-j transition has continuing formants; the target medial is assigned 110 ms before its vowel. The projection removes this transition but must be heard for retained target identity.

**tou2 — aishell3:SSB00090400:1**

Human note: "the syllable \"ou\" gets cut off a little early i think"

The note explicitly reports a clipped ou final, with reviewer uncertainty retained.
The ow phone is a single 100 ms interval. Voicing and formants continue into the following l. The owned-final projection retains exactly the disputed endpoint and cannot repair it.

**ni3 — aishell3:SSB00800453:6**

Human note: "i think its slightly too early, we get some of the \"ai\" "

Explicit preceding ai4 material is heard at the start.
The aj-to-palatal-nasal transition is voiced; the vowel starts 100 ms after the unit boundary. Removing the onset avoids that interval but does not independently prove vowel ownership.

**zong3 — aishell3:SSB00050353:4**

Human note: "slightly too early, we get some of the end of the \"fu\""

Explicit preceding fu4 material is heard at the start.
The unit begins at the preceding vowel's decay before the affricate release. The 140 ms affricate interval may contain transitional voicing; the final projection excludes it.

**ku4 — aishell3:SSB00570040:6**

Human note: "we dont really get all of the \"k\" "

The note reports missing k onset material, regardless of the BOUNDARY EARLY enum.
The crop contains the entire assigned 120 ms labialized stop interval, including visible closure/release evidence. Human clipping may reflect acoustic placement or isolated playback; moving the edge earlier is not justified by this plot alone.

**shi4 — aishell3:SSB01120199:3**

Human note: "lowkey doesn't get get a lot of the \"sh\""

The note reports missing sh frication, regardless of the BOUNDARY EARLY enum.
The crop contains the assigned 100 ms fricative, with high-frequency frication visible after the start. The syllabic nucleus is only 40 ms. A final-only representation makes this short-span limitation more severe.


No enum name was translated into an edge correction. kuang2 remains UNCLEAR;
tong2 is MULTI_EDGE + UNCLEAR because the note does not specify directions.
Root counts: **0 demonstrated clear MFA errors; 0 reconstruction errors;
0 material extraction errors explaining these eight; 3 provisional fuzzy cases;
5 uncertain cases.** The separate one-sample exporter defect is real.

## Controls and candidate effects

Every failure is compared with all 18 original PASS cases using initial class,
final class, nucleus identity, duration within 80 ms and same-speaker evidence;
all scores and best-three matches are in
[control-comparisons.json](data/generated/aishell3/round2-final/control-comparisons.json).
Four of eight failures have plosive initials, versus eight of 18 PASS controls.
Failures span all five initial classes. PASS examples also contain diphthongs,
voiced transitions and vowel/glide onsets; none of these properties alone identifies
a failure. This small selected QA set cannot support calibrated failure rates.

The eight control items maximize initial/final class coverage, then the recorded
matching scores, with any original PASS under-60 ms outlier required. The selected
controls cover all five initial classes and all four final classes, including
same-utterance kai1/de5 for failed ku4, a second ni3, a zero-initial/glide ye3,
affricate jin3, nasal san1, rhotic nar3 and the 50 ms de5 risk. Order is a fixed hash
order; former verdicts and selection reasons are absent from the page payload.

For the failures, the candidate excludes the onset/medial interval in all eight.
That removes the interval implicated by the three explicit preceding-speech notes,
but listening must determine whether the remaining vowel/coda is clean. It does
not restore a clipped k/sh; those onsets are outside the pooling proposal. It does
not extend any final: tou2's questioned /ow/ end and tong2's unspecified second
edge remain unresolved. shi4 has only 40 ms of nucleus and is flagged.

For all 18 PASS controls, the candidate keeps every owned nucleus/coda phone,
contains nonzero PCM, is nonempty and stays inside its original read unit. One
control, `aishell3:SSB00120163:1` de5, shrinks to 50 ms and is flagged and included
in Round 2. These are structural checks, not proof of no perceptual regression.
The 26-item per-case effects and both audio exports are recorded in
[reviewed26-candidate-effects.jsonl](data/generated/aishell3/round2-final/reviewed26-candidate-effects.jsonl).

## Three separate representations

The version is `nearest_sample_half_open_and_owned_nucleus_coda_v1`.
Every derived record preserves:

1. `linguistic_read_unit`: original MFA/reconstructed seconds and full phone evidence.
2. `tone_bearing_pooling_span`: an experimental candidate, not an adopted ML target.
3. `context`: the original unit plus up to 250 ms on each side, clipped to the source.

`playback_read_unit` holds the separately corrected sample indices for whole-unit QA.
No training configuration or existing model target was changed.

The candidate begins at the single vowel or syllabic nucleus and ends at the
original owned coda endpoint. The explicit phone-role grammar admits optional
onset and medial followed by a nucleus and optional nasal/rhotic coda. It retains
entire diphthong phones, /n ŋ/ codas, erhua /ɻ/, syllabic /z̩ ʐ̩/ nuclei and neutral
unmarked vowels. Zero-initial vowels start where they already began. Medial
/j w ɥ/ before the nucleus is deliberately excluded in this conservative experiment;
it can itself carry voicing, so this is **not a claim to include every tone-bearing
sample or the entire phonological final**. No pinyin or example-specific timing rule
is used. Tone marks are ignored only for phone-role lookup, never edited in evidence.
Unknown, missing, multiple-nucleus or malformed structures return **unavailable**.

The mapping is specific to the pinned
[MFA Mandarin dictionary inventory](https://mfa-models.readthedocs.io/en/latest/dictionary/Mandarin/Mandarin%20%28China%29%20MFA%20dictionary%20v3_0_0.html).
The role grammar and current corpus inventory were checked locally; phonetic
coverage beyond this inventory is not silently assumed. Re-running or fine-tuning
MFA is not needed to test this representation and was not performed.

**Context-window encoder input plus target tone-bearing pooling is recommended
conditionally on Round-2 ownership and control checks.** Playback targets are
inspection tools; the model input can contain connected context. A pooling boundary
need not equal a read-unit boundary. Fuzzy whole-unit onsets need not block release
if tone-bearing ownership is trustworthy. Contextual embedding frames can still
encode neighbors, so this representation does not prove absence of learned context
or speaker confounds. Short spans may offer few encoder frame centers and need
review; no duration gate was relaxed to increase yield.

## Full accepted-candidate audit

- **787/787 derivable; 0 unavailable.** 746 starts move inward; 41 starts stay the
  same. No final second timestamp moves.
- Tone counts remain T1 **175**, T2 **183**, T3 **147**, T4 **224**, T5 **58**.
- Tone-bearing durations: minimum **20 ms**, p5 **60 ms**, median **140 ms**,
  p95 **320 ms**, maximum **490 ms**.
- Whole-unit durations: 60–570 ms, median 230 ms; contextual windows: 410–1070 ms,
  median 720 ms, p5 530 ms, p95 930 ms.
- Initial classes: plosive 209, fricative 185, affricate 141, sonorant 126,
  zero/glide 126. Finals: open 338, nasal 252, diphthong 186, rhotic 11.
- **22 candidates under 60 ms** are flagged, not automatically approved or
  quarantined. All have a phonological nucleus; that is not an independent voiced
  material measurement. No empty/out-of-bounds spans, malformed owned phone
  sequences, neighbor crossings or nonpositive durations occur.
- All **2,361** target/tone-bearing/context exports decode, match their source
  slices exactly and contain nonzero PCM. All originals retain their labels,
  partitions and read-unit evidence.
- **No new unit was quarantined.** The original two long-phone quarantines remain
  excluded. No training dataset was released.

The [summary](data/generated/aishell3/round2-final/summary.json),
[derived records](data/generated/aishell3/round2-final/derived-candidates.jsonl),
[sample corrections](data/generated/aishell3/round2-final/sample-corrections.json),
and [private selection](data/generated/aishell3/round2-final/private-selection.json)
make each derivation and its provenance inspectable.

## Developer handoff and next step

Open exactly:

`/home/jacob/benma/research/perceptual-tone-model/data/generated/aishell3/round2-final/index.html`

There are **18 items: 8 former failures + 8 PASS controls + 2 new short-span
outliers** (suo3 at 20 ms and zhuo2 at 30 ms). The developer hears context, original
target, tone-bearing target and optionally the full utterance, and answers the two
independent integrity questions with notes. No tone judgment is requested.
See [exact review and ingestion instructions](aishell3-qa.md). Export to
`/home/jacob/Downloads/aishell3-round2-decisions.json`.

After review: ingest both judgments, resolve or explicitly quarantine true final
clipping/wrong ownership/mismatch, check control regression and short-span flags,
recheck split/coverage after exclusions, and freeze the selected representation.
A subsequent continuation may release and train with context input and tone-bearing
pooling if those conditions pass. Whole-unit onset fuzziness alone is not a reason
to quarantine or require further exact-boundary tuning. This pass stops at review.

## Validation and freeze

The final validation record and logs are in `round2-final/validation.json`,
`python-tests.log`, `node-tests.log`, `lint.log`, `original-browser-qa.json` and
`round2-browser-qa.json`. Tests cover adjacent ownership and concatenation, source
PCM preservation, deterministic exports, phone families, unavailable malformed
sequences, inside-unit pooling, independent judgments, media hash binding and
no release during ingestion. Actual full-build repetition verifies manifests,
HTML and WAV bytes, not just in-memory derivation equality.

All **413** frozen hashes match, and the **63-example** deterministic replay is
byte-identical. **1,176 pre-existing evidence files** match the initial snapshot,
including original TextGrids, candidates, media and normalized decisions. No
production pronunciation file changed. No commit, push, deploy or training occurred.

See [changed research files](reports/aishell3-round2-changed-files.txt).

