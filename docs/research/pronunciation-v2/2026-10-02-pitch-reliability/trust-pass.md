# Tone Graph V2 — Trust Pass

Continuation of the uncommitted `pronunciation-v2-research` tree. All evidence was read locally; PostgreSQL transactions were read-only. No provider calls, new recordings, downloads, audio additions to Git, commits, pushes or deployment. This report supersedes the prior claim that one silence replay established sufficient protection.

## Decisions

- **No speech: ROBUST ENOUGH FOR PRODUCT SMOKE.** Both exact real false accepts are rejected. This is bounded corpus evidence, not calibrated VAD accuracy.
- **Missing pitch: CURRENT PRIMARY ONLY / NO FALLBACK.** Latest 雨 and 伞 each have TIMING FAILURE; individual character pitch coverage is unidentifiable without inventing attribution.
- **Graph semantics: YES.** The line is measured evidence; perceived character identity and reference pronunciation remain separate. Reference tones appear only on tap.
- **UI readiness: READY FOR FORMAL UI POLISH after the five-case smoke packet.** Known provider missingness is honestly represented; there is no newly unresolved functional failure requiring broad research.

## Exact recording identity

The latest matching persisted records are unique. R0–R9 retain the previous audit indices; R10–R14 are the new physical smoke set. SHA-256 verified for all 15 canonical files; the local inventory additionally records original assets and attempt IDs. Dates/times below are UTC, 2026-10-02.

| Case | Heard text | Timestamp UTC | Perception ID |
|---|---|---|---|
| R0 | 我想买五把雨伞。 | 14:51:20.001932+00:00 | `7787300e-d43a-48d2-bf1d-121e11761af9` |
| R1 | 我想买五把雨伞 | 14:52:03.084658+00:00 | `c95673d3-ab32-443c-b2cd-49c5f95c8a45` |
| R2 | 我要一个苹果。 | 15:19:32.327506+00:00 | `0f4107fe-5c8f-49ac-8302-63070cbadfca` |
| R3 | 我们去吧 | 15:21:11.403659+00:00 | `f3c642b5-ef7b-451a-8e96-ec7e143338d9` |
| R4 | 我们要去贵州。 | 15:25:32.507541+00:00 | `f47fadb3-63a6-4445-9c11-3b2170de9343` |
| R5 | 我想买五把雨伞。 | 19:19:29.518506+00:00 | `a0270cee-2e62-41b3-b266-cec08c185226` |
| R6 | 现在是下午两点半。 | 19:20:07.268747+00:00 | `de4b999e-a527-4613-8709-618c68716477` |
| R7 | 我要一个苹果。 | 19:23:25.955471+00:00 | `484e80c0-cc41-49ab-9623-ba09d71a7458` |
| R8 | 我们去吧。 | 19:24:09.462939+00:00 | `e59a6350-6631-43bd-ab64-7f02a6ed377a` |
| R9 | 贵州。 | 19:24:53.758159+00:00 | `f5dc0cc1-cd1f-4721-918b-9357f33774e1` |
| R10 | 其实我不行 | 23:32:46.556503+00:00 | `ab6c16ab-ece9-4d00-a3f9-ca693d103624` |
| R11 | 我想买五把雨伞。 | 23:34:52.005699+00:00 | `1a927887-320c-4f15-876e-60648b472c8c` |
| R12 | 我要一个苹果。 | 23:36:05.974350+00:00 | `5ca771a7-ad1f-42a0-b7ee-20babc4a1385` |
| R13 | 我们去吧。 | 23:37:43.979291+00:00 | `209ef0c7-c22b-4e74-af1c-391892040d29` |
| R14 | 贵州 | 23:38:29.504301+00:00 | `87ac7dd1-702e-46af-92f5-652507487d51` |

Latest exact provenance:

- R10: utterance `f4232709-efe6-4a1e-9ff4-c8b65967b5c1`; canonical `f81b2d76-324a-4ab8-9cb8-43caaea4fbc5`; SHA-256 `6f8c2f58de72ce69fce08125091c12b6194d517f5e6752fdba556b9f25e789d1`; attempts `1263135b-70a0-4a49-ab4f-60e79021b967`; persisted target `我想买`.
- R11: utterance `0dcfe4a5-2283-4de4-969f-a98789c4059a`; canonical `512d7797-7ac1-4dd6-96ea-0b702b12d86d`; SHA-256 `66b6ec23a83c8e96417e1832df7bebb0692f204c1f7ef80208bcc59723eccafc`; attempts `a76769dd-0906-42d9-9f1c-acdf7105e798`; persisted target `我想买五吧雨伞`.
- R12: utterance `1e2278c5-12fd-4c06-a9d9-e64159fecd8d`; canonical `3256a18f-0c7e-4ced-88b2-05214e1c5b69`; SHA-256 `bdfea0fa05fbda85a29f595e9261debfd31d34754d85d918e3a32c0b9a8f8248`; attempts `064c6bfa-71a8-40c2-88d9-29395c9236bb`; persisted target `我要一个苹果`.
- R13: utterance `e9e2777a-ba2a-4200-8aba-eda013e37287`; canonical `a7b08eb9-8f32-461b-9d2a-03f8c0d2e104`; SHA-256 `0ed2c58291c4acbe98b56eec67027b8027f9e9ba3995b62ae772695a5771a794`; attempts `5ee51353-d171-493a-bb09-ffc6bcd20d45`; persisted target `我们去吧`.
- R14: utterance `ccc678fb-ad22-415c-b7e8-afdf7c26b713`; canonical `5365c3ad-d50d-4822-9bb7-d37ce1f0168c`; SHA-256 `9c2c3828fa4362188ff5e1e87f00747f42adda3dba76399e1595191d0bfc48d3`; attempts `61977fc3-051a-4bf3-9a0b-f6a05346602a`; persisted target `广州`.

Persisted latest T3 target is `我想买五吧雨伞`, while perception is `我想买五把雨伞。`. Latest mismatch target is `广州`, perceived `贵州`; no new full `我要去广州` target take is inferred. The separate S13 regression retains `我要去广州。` / `我要去贵州。`. User reports of intentionally altered tones are self-report, not acoustic labels.

## Both real silence recordings

| Metric | R6: 现在是下午两点半。 | R10: 其实我不行 |
|---|---:|---:|
| Duration s | 6.78025 | 3.50625 |
| RMS | 0.00613245 | 0.00296642 |
| Peak | 0.536041 | 0.0121765 |
| Total elevated activity, hop-weighted s | 0.16 | 0 |
| Broad AC finite frames | 0 | 147 |
| Clipping fraction | 0 | 0 |
| Crest factor | 87.4106 | 4.10478 |
| Whole-file power 40–80 / 40–4000 Hz | 0.282289 | 0.494384 |
| 20-ms centered RMS p10 | 0.0027652 | 0.0020125 |
| 20-ms centered RMS p20 | 0.0030279 | 0.0022314 |
| 20-ms centered RMS p50 | 0.0036612 | 0.0027790 |
| 20-ms centered RMS p90 | 0.0050421 | 0.0037816 |
| 20-ms centered RMS p99 | 0.0188950 | 0.0049826 |
| 20-ms centered RMS max | 0.0570669 | 0.0066846 |

Both original files recanonicalize to the exact saved canonical SHA-256: mono PCM16 / 16 kHz. No clipping or canonicalization defect. R6 has seven short elevated runs (20,30,30,20,20,20,20 ms of hops), large crest factor and transient/click evidence; longest window support is 40 ms. R10 has **no elevated runs and no comparable click**. Its broad AC finds 147 frames (1.47 s hop-weighted), longest run 170 ms, F0 min/median/max 45.220/58.644/63.257 Hz. Those are periodic background candidates, not proof of speech. Production AC50 also has 148/345 raw-finite frames and 46 retained frames in R10 (versus 0/673 in R6); pitch existence alone is not a speech-presence gate.

R10 broad periodic run lengths, seconds: `[0.14, 0.05, 0.05, 0.07, 0.17, 0.14, 0.07, 0.09, 0.04, 0.04, 0.1, 0.06, 0.05, 0.13, 0.11, 0.07, 0.09]`. Activity uses 20-ms centered windows / 10-ms hop, background p20 above one quantization step. Hop-weighted totals are not nonoverlapping acoustic interval durations.

**Exact v1 acceptance reason:** background .002238855 <.01 and elevated activity 0 <.05, but `periodic_seconds=.17`, so `background<.01 AND activity<.05 AND periodic==0` is false. It accepts solely via periodicity. R6 background .003030228 / activity .03 / periodic 0 satisfies all three absence conditions and is rejected. Raising RMS or peak thresholds would not address this mechanism.

Both ASR payloads provide token logprobs, not a no-speech probability. The already-saved R10 Azure alignment has zero confidence, all words omitted, and no timing; this corroborates the diagnosis but is **not** used as a speech/pronunciation score or required new provider call.

## Gate V2 and workflow

The pre-ASR absence thresholds remain unchanged. Only ambiguous periodic background (background <.01, no >=50-ms elevated activity, some broad AC pitch) receives a second acoustic view: 100–4000 Hz Hann band, transition 20 Hz, same AC40–550 settings. Count frames where both tracks voice and their frequencies agree within 2 semitones. These values never modify the production pitch extractor or graph.

After ASR and before success persistence/callbacks, count Han units only. Reject a claim of >=3 units when this ambiguous path has <`min(units,10)*20 ms` total corroboration **and** <50 ms continuous corroboration. This deliberately broad bound rejects extreme lack of support; a coherent 50-ms run independently rescues the turn. No target, semantic plausibility, tone expectation or transcript agreement is consulted.

R10 has only **4 corroborated frames / 40 ms total, longest run 30 ms**, below the 100-ms total bound for five claimed units. It fails post-ASR. R6 fails pre-ASR. The filtered tracker alone finds 40 frames on R10, but most disagree with the raw background branch: accepting it just because it returns F0 would fail.

The second view runs on 1/15 original cases, 0/13 ordinary speech takes. Quiet continuous speech can invoke it; it is an acoustic check, not a fallback pitch tracker. Single/two-character speech and sub-80-ms uncertain recordings remain permissive. Persistent voiced hum may still support short ASR claims; louder arbitrary noises and all nonspeech classes are not solved. No universal false-accept/false-reject rate is claimed.

A failed post-ASR run stores `status=failed`, `error_code=no_speech`, **no product transcript**, and internal gate diagnostics/raw provider evidence. The raw rejected payload remains auditable; it is not a successful heard sentence. No graph, target assessment, successful attempt/history item or Conversation reply starts. Internal canonical upload may exist for post-ASR failure. Existing historical transcripts/results remain immutable.

Legacy graph, Conversation/stream preflight, attempt creation and assessment paths re-check audio plus available persisted perception. Target endpoints check the latest no-speech failure and use perceived text only for corroboration, never intended target. Practice retains its prepared target and offers fresh capture: “Didn't catch any speech. Try again.”

## False rejection and real-speech controls

**67/67 expected offline decisions:** 2 original false accepts rejected; 13 original speech takes + 26 attenuations (0.1×/0.01× PCM amplitude) + 13 provider-timed one-character excerpts + 13 doubled-speed sample-stride variants accepted. Speed variants are stress tests, not phonetic gold. All previous accepted takes are retained.

| Real speech case | Activity longest s | Broad periodic longest s | Post check |
|---|---:|---:|---|
| R0 | 1.09 | 0.38 | Accepted |
| R1 | 2.05 | 0.75 | Accepted |
| R2 | 0.50 | 0.46 | Accepted |
| R3 | 0.48 | 0.20 | Accepted |
| R4 | 0.62 | 0.64 | Accepted |
| R5 | 0.55 | 0.69 | Accepted |
| R7 | 0.64 | 0.62 | Accepted |
| R8 | 0.62 | 0.29 | Accepted |
| R9 | 0.26 | 0.16 | Accepted |
| R11 | 0.87 | 0.55 | Accepted |
| R12 | 0.53 | 0.43 | Accepted |
| R13 | 0.54 | 0.46 | Accepted |
| R14 | 0.23 | 0.17 | Accepted |

CI-safe synthetic coverage includes digital silence, near-silence, stationary noise, click, periodic hum, quiet/short voiced fixtures, sustained nonperiodic activity, and fast multi-character support. Real audio remains outside Git. Two opt-in pytest regressions verify exact perception IDs, SHA-256 and rejection; enable with `BENMA_TRUST_RECORDINGS=/tmp/benma-tone-trust/recordings.json`.

## Latest 雨 / 伞: attribution failure, not absent word pitch

Saved Azure word `雨伞`: Offset 33,200,000 / Duration 9,900,000 ticks → **[3.32,4.31) s**. Its two `Syllables` entries have empty `Syllable`, no `Grapheme`, and intervals [3.32,3.75), [3.76,4.31). `Phonemes` says `yu 2`, `san 3`, but these reference labels cannot establish observed phones or independently attribute character timing. No recoverable explicit character/grapheme timing was discarded by production. The exact mapper correctly abstains; its regression confirms adding explicit Grapheme labels would preserve the given intervals without splitting.

| Region | Frames | Raw finite | Retained | Filter loss | Classification |
|---|---:|---:|---:|---|---|
| 雨 character | N/A | N/A | N/A | N/A | TIMING FAILURE |
| 伞 character | N/A | N/A | N/A | N/A | TIMING FAILURE |
| 雨伞 word [3.32,4.31) | 99 | 53 (53.54%) | 52 (52.53%) | 1 energy-gated | Word attribution only |
| Anonymous interval A [3.32,3.75) | 43 | 36 (83.72%) | 36 (83.72%) | 0 | Not assigned to 雨 |
| Anonymous interval B [3.76,4.31) | 55 | 17 (30.91%) | 16 (29.09%) | 1 energy-gated | Not assigned to 伞 |

This is not an extractor-wide or display-rendering failure: substantial measured word evidence survives and is available in real-time More detail/Raw. **Exact per-character raw F0 coverage cannot be stated honestly.** Primary cells remain blank because local-time mapping requires valid character attribution. No equal split, phone-count, reading agreement or anonymous-tier positional assumption is introduced.

## Missing/suspicious pitch sample set

Counts use 10-ms source frames within half-open provider character intervals. Islands break at missing pitch; short islands <4 frames. >6/>12-st jumps below are adjacent finite frames; cross-gap jumps are separate. Energies and ACF use centered 60-ms waveform windows; ACF is an uncalibrated proxy, not voiced gold.

| Case / unit | Region s | Raw/frames | Retained/frames | Raw islands / short | >6 / >12 st | Max cross-gap st | Mine segments |
|---|---|---|---|---|---|---:|---:|
| R3 吧 | 0.79–1.07 | 0/28 | 0/28 | 0/0 | 0/0 | 0.000 | 0 |
| R8 吧 | 0.92–1.24 | 0/32 | 0/32 | 0/0 | 0/0 | 0.000 | 0 |
| R13 吧 | 1.14–1.41 | 17/27 | 8/27 | 2/0 | 0/0 | 10.400 | 1 |
| R14 贵 | 0.52–1.03 | 22/51 | 17/51 | 2/0 | 0/0 | 10.242 | 1 |
| R14 州 | 1.04–1.42 | 15/38 | 8/38 | 3/1 | 0/0 | 11.990 | 1 |
| R9 州 | 1.06–1.60 | 13/54 | 13/54 | 2/1 | 0/0 | 21.876 | 2 |
| R12 一 | 1.33–1.53 | 19/20 | 19/20 | 2/1 | 0/0 | 2.928 | 2 |
| R11 我 | 0.76–1.23 | 22/47 | 22/47 | 1/0 | 0/0 | 0.519 | 1 |
| R11 想 | 1.24–1.57 | 26/33 | 26/33 | 1/0 | 0/0 | 0.890 | 1 |
| R11 五 | 2.42–2.85 | 33/43 | 32/43 | 1/0 | 0/0 | 0.618 | 1 |
| R12 要 | 1.01–1.32 | 24/31 | 24/31 | 1/0 | 0/0 | 1.003 | 1 |

| Case / unit | RMS min/median/max | ACF min/median/max | Raw selected strength min/median/max | Rejection reasons (overlap) |
|---|---|---|---|---|
| R3 吧 | 0.0025/0.0041/0.0452 | 0.1139/0.3985/0.5158 | none | tracker_missing: 28, missing_or_out_of_range_f0: 28, weak_periodicity: 28 |
| R8 吧 | 0.0035/0.0085/0.0908 | 0.2277/0.3881/0.6145 | none | tracker_missing: 32, missing_or_out_of_range_f0: 32, weak_periodicity: 32 |
| R13 吧 | 0.0043/0.0055/0.0442 | 0.1711/0.6106/0.8158 | 0.5909/0.7190/0.8574 | tracker_missing: 10, missing_or_out_of_range_f0: 19, weak_periodicity: 10, below_energy_gate: 9 |
| R14 贵 | 0.0023/0.0090/0.0660 | 0.2335/0.5557/0.9311 | 0.5394/0.8508/0.9374 | tracker_missing: 29, missing_or_out_of_range_f0: 34, weak_periodicity: 29, below_energy_gate: 5, low_frequency_contamination: 4 |
| R14 州 | 0.0038/0.0185/0.0808 | 0.2015/0.4872/0.9171 | 0.5295/0.6891/0.9490 | tracker_missing: 23, missing_or_out_of_range_f0: 30, weak_periodicity: 23, below_energy_gate: 7 |
| R9 州 | 0.0033/0.0115/0.1957 | 0.1905/0.4397/0.9343 | 0.4906/0.7951/0.9470 | tracker_missing: 41, missing_or_out_of_range_f0: 41, weak_periodicity: 41 |
| R12 一 | 0.0104/0.0227/0.0360 | 0.3036/0.8256/0.9803 | 0.5213/0.8400/0.9816 | tracker_missing: 1, missing_or_out_of_range_f0: 1, weak_periodicity: 1 |
| R11 我 | 0.0021/0.0166/0.0307 | 0.1472/0.5697/0.9640 | 0.4910/0.9234/0.9712 | tracker_missing: 25, missing_or_out_of_range_f0: 25, weak_periodicity: 25 |
| R11 想 | 0.0158/0.0363/0.0412 | 0.2619/0.9167/0.9893 | 0.6124/0.9666/0.9918 | tracker_missing: 7, missing_or_out_of_range_f0: 7, weak_periodicity: 7 |
| R11 五 | 0.0033/0.0226/0.0400 | 0.3462/0.9171/0.9811 | 0.4789/0.9444/0.9911 | tracker_missing: 10, missing_or_out_of_range_f0: 11, weak_periodicity: 10, below_energy_gate: 1 |
| R12 要 | 0.0107/0.0369/0.0446 | 0.3049/0.5679/0.9398 | 0.4830/0.8531/0.9528 | tracker_missing: 7, missing_or_out_of_range_f0: 7, weak_periodicity: 7 |

Prior 吧 R3/R8: 0/28 and 0/32 raw finite, hence no filter/display loss. Neither has a sustained independent ACF>=.65 region; tracker path/candidate weakness and limited periodic support remain the explanation. This does not prove every sample is unvoiced or diagnose pronunciation. Latest 吧 R13: 17/27 raw, 8 retained; nine removed by the energy gate, one surviving Mine segment. Latest 一: 19/20 retained with two islands. Latest 贵/州: 17/51 and 8/38 retained; energy/low-frequency exclusions explain attrition, not reference tones.

The prior 州 branch remains 134.611 Hz → missing frame → 476.266/467.038/462.807 Hz, a 21.876-st cross-gap jump, with strengths .5855/.614/.4906. No returning low branch supplies bilateral support. A one-sided large-jump deletion could also delete genuine expressive pitch. **No continuity/octave change**; no tone-based special case. Its Raw evidence stays visible.

## Region-only fallback feasibility

Current local environment still has Parselmouth/NumPy; librosa/pYIN, WORLD, CREPE/torchcrepe, torchaudio, WebRTC VAD and Silero are absent. No download. The only serious candidate is **Praat CC50**, cropped to the candidate region with <=60 ms of acoustic context on either side. This is a narrower check than the previous whole-utterance bakeoff.

Eligibility: trustworthy character interval, primary retained coverage <10%, and >=5 consecutive 10-ms independent waveform probes with normalized ACF>=.65 and RMS>=.0003. Candidate acceptance: CC strength>=.65, independent ACF>=.65, RMS>=.0003, >=5 consecutive frames, adjacent motion <=3 st, deterministic on three repeats. Expected tones/text are never inputs. These are fixed conservative feasibility criteria, not validated pitch accuracy.

The previous two missing 吧 regions fail independent-support eligibility. Diagnostic CC was still run offline to quantify the opportunity, without accepting those frames. No eligible missing character region demonstrated recovery; 雨/伞 cannot enter because their character timing is unavailable. Healthy primary regions cannot be overwritten. Negative/probe intervals below are diagnostic acoustic windows, not newly claimed phone/character timing.

| Diagnostic region | CC finite | Islands | Accepted by acoustic subset alone | Production recovered | CC median ms |
|---|---:|---:|---:|---:|---:|
| R3 prior 吧 | 2 | 2 | 0 | 0 | 1.952 |
| R8 prior 吧 | 1 | 1 | 0 | 0 | 1.397 |
| R13 latest 吧 | 19 | 2 | 7 | 0 | 1.861 |
| R9 suspicious 州 | 12 | 1 | 7 | 0 | 2.311 |
| R14 latest 贵 | 27 | 3 | 13 | 0 | 1.982 |
| R14 latest 州 | 20 | 3 | 7 | 0 | 1.469 |
| R11 雨伞 word only | 50 | 4 | 41 | 0 | 2.043 |
| R12 一 control | 19 | 2 | 12 | 0 | 1.396 |
| R11 我 control | 26 | 2 | 21 | 0 | 2.171 |
| R11 想 control | 27 | 1 | 26 | 0 | 1.676 |
| R11 五 control | 36 | 2 | 31 | 0 | 1.517 |
| R11 pause | 4 | 1 | 0 | 0 | 1.578 |
| R6 old silence | 0 | 0 | 0 | 0 | 9.074 |
| R10 new silence | 189 | 21 | 11 | 0 | 4.419 |
| R3 initial probe, not phone timing | 0 | 0 | 0 | 0 | 1.486 |

All cropped candidate outputs repeat exactly. All have zero adjacent >6/>12-st jumps in these probes; the new silence nevertheless has 21 pitch islands and even 11 frames passing the acoustic subset alone. Region/timing/primary-support gates matter: those 11 are **not accepted speech or production pitch**. Prior 吧 yields only 2 and 1 CC frames (neither accepted), versus zero primary. New 吧 and clean controls already have healthy primary evidence. The word-only 雨伞 crop has 50 CC frames versus 53 primary; it cannot solve attribution.

**Final: NO FALLBACK / CURRENT PRIMARY ONLY.** Recovered production coverage 0; added production fragmentation 0; added jumps 0; added pitch latency 0; no fallback provenance field is needed because no fallback measurements enter transport. Tests cover current-primary abstention with valid timing/no F0, filter-rejected raw preservation, healthy retained evidence, expected-tone independence, silence/pause gaps, and the timing prerequisite. Future fallback is not silently enabled by this offline experiment.

**No Mine-only bridge.** A very short within-character gap (latest 一 has 19/20 frames) alone does not certify absence of an unvoiced interval; transport lacks the independent acoustic support needed for safe display interpolation. Latest word-only 雨伞 also has >12-st across-gap movement. More detail remains unsmoothed retained samples with elapsed timestamps; Raw remains original tracker output. Neither is bridged, retimed, tone-shaped or silently repaired.

## Primary graph and target semantics

**ASR CHARACTER IDENTITY != OBSERVED PITCH != REFERENCE TONE.**

- Default cells contain measured pitch above a large perceived character. No lexical/contextual T1/T2/T3/T4/N/*/? labels beneath them, including accessibility labels.
- Tap shows character/pinyin, lexical tone, explicitly `Reference tone: T4` or contextual T2 for 一; unresolved T3 shows `Lexical tone: T3` / `Contextual realization: unresolved`. Copy: “Reference pronunciation, not a detected tone. The line shows measured pitch.”
- No observed-tone classifier, categorical correctness, score, Good/Wrong or expected-tone geometry was introduced. Arbitrary rising/falling/flat contours coexist with 贵/T4 and 州/T1 in regression tests.
- Equal-width cells use a symmetric 12% plot inset: `cell_start + .12 + .76 * local_time_fraction`. Character midpoint equals plot-box midpoint. The actual trace is never recentered; late voiced onsets remain late. One utterance Y domain remains shared; no per-character vertical normalization.
- Every perceived character remains visible, including untimed/unpitched and final cells. Missing pitch stays blank. New result remount/reset preserves horizontal scroll/tap/Raw reset.
- The completed all-Han strip serves as the heard sentence; redundant full transcript text is hidden only when the strip covers all lexical text. Loading/failure/mixed text retains full heard text.
- Target comparison remains separate and hidden when lexical text agrees. 广→贵 means different perceived character, not wrong tone. S13 retains perceived 我要去贵州 regardless of reference/target completion order or measured contour.

## Latency

Paired local warm medians, 10 repeats after two warmups; v1 comparison disables only the new second acoustic view. This is local guard time, not provider/network end-to-end latency. Ordinary speech adds no second tracker; signed median differences range −0.567 to +0.365 ms (measurement variation), plus post-ASR count/check about 0.010–0.016 ms. Existing repeated endpoint guards remain. Cached target-analysis reuse now also runs the guard (roughly 3–12 ms on these normal takes); fresh assessment uses its existing check and does not duplicate it.

R10 ambiguous/background check: 6.011→10.659 ms, **+4.648 ms per guard invocation**, post-ASR rejection .024 ms. Since upload and perception each check canonical audio, this path can add roughly 9.3 ms locally across both; it still waits for the existing ASR call before post-check rejection. R6 pre-ASR rejection: ~10.834 ms total guard time. Digital silence uses the short amplitude path. Normal production pitch adds **0 ms**; region-only fallback is not installed. Diagnostic CC cropped regions cost ~1.4–2.3 ms, whole silence controls up to 9.1 ms; those costs are offline only.

## Files changed in this Trust Pass

Backend:

- `audio/presence.py`: ambiguous-background spectral corroboration and post-ASR unit-count check; diagnostic fields/version.
- `audio/presence_service.py` (new): legacy target endpoint guard using persisted perception.
- `perception/service.py`: post-check before success; failed product transcript omitted, raw payload/diagnostics retained internally.
- `pronunciation/perceived.py`, `pronunciation/service.py`, `pronunciation/laboratory.py`, `conversation/service.py`, `api/routes.py`: downstream/legacy guards, including cached target-assessment reuse.
- `tests/test_speech_presence.py`, `tests/test_sentence_tone_graph.py`: no-speech, exact opt-in replay, attribution, abstention and raw/gap regressions.

Mobile:

- `speech/SentenceToneGraph.tsx`: remove inline references; explicit tap semantics.
- `speech/sentenceToneGraph.ts`: centered plot-box insets and Reference wording.
- `speech/SpeechEvidence.tsx`: avoid complete heard-text duplication when covered by the strip.
- `__tests__/sentenceToneGraph.test.ts`, `__tests__/transcriptFeedback.test.ts`: layout/semantics/S13 regression updates (shared native/web).
- `README.md` and development/reliability docs updated. All earlier uncommitted API schema, alignment, workflow and graph work preserved; no new schema migration or dependency.

## Validation

Final checks: **479 API tests passed** (4 optional skips, 5 known streaming exclusions); **79 focused API tests passed**; **69 connected-speech tests passed**; **314 mobile tests passed** in 25 suites; **67/67 offline decisions**. API/mobile lint, API mypy, mobile typecheck, touched Python formatting, production web/Android exports, phone/desktop browser checks and `git diff --check` passed. See [validation.md](validation.md#trust-pass-validation) for commands and unrelated limitations. Private artifacts under `/tmp/benma-tone-trust/`: `recordings.json` (IDs/paths/hashes/provider evidence), copied canonical WAVs named by utterance ID, `forensics.json`, `audit.json`, `fallback.json`, `gate-replay.json`, `performance.json`, scripts, logs, browser reports/screenshots and local exports. No private audio is added to the repository.

## Final manual smoke packet

1. **SILENCE — target 我想买:** record nothing. Expect no hallucinated transcript, no graph, no successful attempt; retry preserves target.
2. **T3 — 我想买五把雨伞。:** every character visible and centered beneath its plot box, no default reference-tone labels. Show any trustworthy character-timed measurements; if Azure again omits 雨/伞 attribution, keep their cells blank and expose measured word evidence in More detail.
3. **一 — 我要一个苹果。:** measured pitch above 一 where supported; no default T2; tap reveals `Reference tone: T2`.
4. **我们去吧。:** 吧 remains visible; retained primary pitch renders and absent evidence stays absent. No fallback is adopted.
5. **Target 广州 / say 贵州:** graph reads 贵州, measurements follow the audio, no default T4/T1. Tap shows reference guì/T4 and zhōu/T1; compact 广 → 贵 stays separate.

**Only recommended next step after those checks pass: formal UI polish.** No further broad research pass is recommended.
