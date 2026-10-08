# Tone Graph V2 — Native Control Calibration Audit

**October 4 continuation:** the [repeated-capture robustness pass](capture-robustness.md) audits all three new clean-control captures, Praat candidates, cross-take similarity and three bounded acoustic rules. No acoustic repair passed acceptance. Narrow 要 quantity-reading and optional 个 reduction reference fixes are implemented; native character calibration and the accidental-silence false accept remain unresolved. The remainder of this page records the earlier audit and its then-current behavior.

**The current evidence does not establish calibration readiness.** The phone-recorded Google control loses all selected pitch for 一 and 苹. The first observable problem is the primary raw F0 path, followed by rejection of that unreliable evidence; the renderer is faithful to the backend. Both speech recordings have a useful falling 要, but the backend leaves its reference reading unresolved. The exact cached native file is available and has substantial F0, but no saved alignment exists for it, preventing a legitimate character-level control result.

Diagnostic continuation of the uncommitted `pronunciation-v2-research` tree. Recording dates are October 3, 2026; the pass completed October 4 UTC after a machine restart removed `/tmp` artifacts. No production code, classifier/filter thresholds, comparison policy, UI styling, tracker, or database evidence was changed. No provider calls, commit, push, or deployment. Only this report directory is new outside ignored storage.

[Full six-character tables for A/B/C](forensics.md), [one-row-per-character CSV](per-character-forensics.csv), and [critical comparison table](comparison.md) accompany this report. Local-only absolute-time plots, original-time sample ownership, actual mobile coordinates, replay scripts and fixture metadata are under [`services/api/var/native-control/`](/home/jacob/benma/services/api/var/native-control/absolute-time-audit.html), already ignored by repository policy. No audio is included in the report directory.

## Required critical comparison

Raw coverage means finite original tracker frames, **not trustworthy voicing**. Retained coverage uses all tracker frames in the provider character interval. Direct native character-level NA means missing alignment, not zero F0. “Direct grapheme” establishes provider identity and structurally valid timing; this is not an independently annotated phonetic boundary gold standard.

| Control | Character | Timing quality | Raw F0 coverage | Retained coverage | Observed gesture | Confidence | Comparison | Primary cause / limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DIRECT NATIVE | 要 | NA: no saved alignment | NA | NA | NA | NA | uncertain fallback | TIMING |
| DIRECT NATIVE | 一 | NA: no saved alignment | NA | NA | NA | NA | uncertain fallback | TIMING |
| DIRECT NATIVE | 苹 | NA: no saved alignment | NA | NA | NA | NA | uncertain fallback | TIMING |
| PHONE TTS | 要 | Direct grapheme; exact mapping | 38/39, 97.4% | 31/39, 79.5% | falling / 4-like | moderate | uncertain | COMPARISON: reference reading unresolved |
| PHONE TTS | 一 | Direct grapheme; exact mapping | 28/37, 75.7% | 0/37, 0% | unclear | low | uncertain | RAW_F0: low-frequency path, then energy rejection |
| PHONE TTS | 苹 | Direct grapheme; exact mapping | 42/69, 60.9% | 0/69, 0% | unclear | low | uncertain | RAW_F0: near quarter-frequency path |
| HUMAN | 要 | Direct grapheme; exact mapping | 31/33, 93.9% | 20/33, 60.6% | falling / 4-like | moderate | uncertain | COMPARISON: reference reading unresolved |
| HUMAN | 一 | Direct grapheme; exact mapping | 16/21, 76.2% | 15/21, 71.4% | unclear | low | uncertain | NO_FAILURE: conservative abstention |
| HUMAN | 苹 | Direct grapheme; exact mapping | 27/37, 73.0% | 27/37, 73.0% | rising / 2-like | moderate | consistent | NO_FAILURE |

“COMPARISON” here identifies the first blocker to useful reference feedback: lexical/contextual reference resolution, upstream of the comparison function. It does not mean the comparison function incorrectly ignored a resolved T4. No new cause category was introduced.

## Exact sources and provenance

The read-only database inventory contains 127 perceptions. Eight perceptions match the sentence or its explicit target, including an earlier misrecognition. The three new takes share target `590fbe10-a13b-4878-8f75-7e47be2d0438`, text **我要一个苹果**, created `2026-10-03T18:50:44.483111Z`. The two speech transcripts are **我要一个苹果。**. The third transcript lacks final punctuation. The user explicitly identified the three sources; timestamps alone did not establish speaker identity. No later matching perception exists in this inventory.

| Source | Perception / reference ID | Utterance ID | Attempt ID | Created UTC |
| --- | --- | --- | --- | --- |
| C: HUMAN | `422877d2-558e-4eae-89f2-f5f3c8fb9027` | `6180c6b9-95d5-40d9-a8a6-b62f07865df4` | `e0bb0c46-ec43-4d79-93b3-ade7f967f08b` | `2026-10-03T18:50:51.419039Z` |
| B: GOOGLE TRANSLATE PLAYBACK | `c19a5a74-40ea-42a4-8b77-b360b85c33b6` | `b9c6878c-f285-4969-a10c-47920faa61a6` | `8246be1c-e3f9-4e34-8366-879a59c40ac4` | `2026-10-03T18:58:25.802193Z` |
| N: ACCIDENTAL NO-SPEECH, excluded from A/B/C | `7e489fd3-c36d-41f6-a20b-300616ad1a42` | `3259a3fd-16d2-45b4-8b81-69e52140d10b` | `0182290b-a945-449a-bf40-b38281fd588c` | `2026-10-03T18:58:57.143148Z` |
| A: cached Azure reference | `d1272f79-c791-4eb4-973c-3864cc1af03d` | NA | NA | `2026-10-02T15:19:22.936924Z` |

Eastern times of C/B/N are 14:50:51 / 14:58:25 / 14:58:57. C analysis is `b66e15ba-b13a-4a37-addb-dbea484fe26a`, acoustic run `03eacd19-05a6-4122-b785-721078a1db28`. B analysis is `eb8cafb0-b7e1-475e-9421-01a285c36fd4`, acoustic run `65a7d2eb-d672-4b83-90e7-53b9ae8d783d`. Both are `perceived-speech-v5-gesture-groups`. N analysis is `8a55d361-4b8c-469a-9893-86bee3cbce36`.

All hashes were recomputed from local bytes and matched persisted assets:

| Source | Original SHA-256 | Canonical SHA-256 |
| --- | --- | --- |
| C | `09738486b5ce48576ade4a489fdc69ef98570b16252ebcc9c0bd1790a28af1e1` | `ef3081f0d3f0ddc1fd71a2f3af0282842cf091b37316f418136cb49302bf3350` |
| B | `58f945a18c45e82d47170f5076779654376f62922ceab76f50c3131340cff475` | `bbe264ec0a910fcf76cd3582c4fe4f6b7d137753f8c7f6bc59a8d673202b83cd` |
| N | `4a34bf726dc8d179cec068b370119c766abedca9f8fa0de248d7316f31f481d1` | `fcaf551459dc957c7544e396858395e4214c2447aa23cc577a2f9c5261b28eaf` |
| A | `ec96b80ac58bab2941badf3401a135810eb8737b41816337af0f2a2d3b70e9c9` | `88e6b9325b545a1c16e893f18b65b7645d2cfd7ccab7f35fb5df1b6788228fbe` (audit-derived, not a persisted upload) |

Audio paths are in `inventory.json`; C/B/N canonical basenames are respectively `d11c8332ef1e4db695c8163bc7ce1480.wav`, `c53d3e1c502549188961e3a14c53a436.wav`, and `2b9ed25369134ee0b389b93039dd92f5.wav`, under `services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical/`.

## Native reference resolution and the direct-control limit

`practice.tsx` prepares a target, calls `createReferenceSpeech()`, and plays the returned `reference.audio_url` with the “Native reference” button. `ReferenceSpeechService.get_or_create()` caches by normalized text, locale, provider, voice, model and rate, scoped to account; cache reuse is not restricted to one target ID. The route serves the stored audio asset. This is generated, provider-backed speech cached in the local object store, not a bundled recording of a human.

The sole matching Azure cache row contains exactly **我要一个苹果**, provider `azure_speech`, voice `zh-CN-Xiaochen:DragonHDLatestNeural`, model `DragonHDLatestNeural`, rate `0%`, locale `zh-CN`, evidence status `live_provider`. Its stored cache key matches recomputation for that recorded provider/configuration. Target snapshot ID is `8ee46063-30d2-49ef-9df5-064cee20da2e`; audio asset ID is `d36b2875-e2e7-45c1-beb1-7a55ae22633e`.

Exact source: `services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/reference/987c656c33044898928a54e1d3d816c9.wav`, 50,444 bytes, mono PCM16, 24 kHz, **1.05 seconds**. Its generation snapshot contains lexical readings but **no audio timing**. Reference generation stores an older generic autocorrelation result; that result was not mistaken for current production Praat evidence. The unchanged current Praat analyzer was run offline on both the exact digital bytes and the normal 16-kHz canonical derivative.

The standalone shell’s settings currently resolve reference provider to `replay`; historical successful rows record Azure. No app request was made to reconstruct a current live server configuration or device playback history. This audit uses the user-designated, verified Azure cache asset as A. It does not assert that an unobserved current server request would select Azure under different settings.

No persisted perceived analysis matches either A’s source hash or its newly canonicalized hash. Repository/local study searches found no matching saved timing. No cached local MFA executable was available. Therefore A has no perceived reading, trustworthy word/grapheme boundary, or per-character F0 assignment. Generation-text dictionary labels were used only to exercise the untimed presentation fallback. No ASR transcript, equal partition, timing transfer from B/C, or phonetic annotation was fabricated.

For **each of 要 / 一 / 苹 in A**, timing trustworthiness is NA; raw and retained F0 *within that character* are NA; gesture and confidence are NA; comparison is the untimed uncertain fallback; Mine has no attributed trajectory. The first blocked stage is **TIMING**. In particular, this pass did not observe “native 苹 is falling” or establish “native 苹 has no acoustic evidence.” It established that those statements cannot be measured with the available native timing.

A has **73/100 finite raw and 73/100 retained frames at 24 kHz**, versus **74/100 finite raw and 70/100 retained at 16 kHz**. All 100 frame timestamps agree across rates. One voicing decision differs at 0.44 s; the ambiguous 0.43-s estimate changes 487.154→411.907 Hz. The four-frame 0.40–0.43-s high branch is rejected by the existing short-island rule only in the canonical replay. This is local pitch-path/filter sensitivity, not a time-coordinate shift. Both rates also contain a high branch around 0.74–0.76 s and ~66.6-Hz estimates at 0.78–0.80 s; clean digital input is not evidence that every raw estimate is correct. Without verified boundaries these anomalies cannot be attributed to a critical syllable or called a calibrated native classifier failure.

## Absolute-time assignment and earliest failures

[Open the local absolute-time audit](/home/jacob/benma/services/api/var/native-control/absolute-time-audit.html). Each standalone SVG includes the waveform, spectrogram, saved word/grapheme boundaries, raw F0, retained F0, the already-existing comparison track, and exact frame ownership marks. [Every frame and owner](/home/jacob/benma/services/api/var/native-control/frame-assignments.csv) and [mobile mappings](/home/jacob/benma/services/api/var/native-control/mobile-mapping.json) are machine-readable. No additional pitch tracker was used; the spectrogram is only a waveform display.

B and C each have six explicit `Grapheme` entries. Provider units, recomputed mapper units and persisted character intervals match exactly. No anonymous syllables, inferred spans, grouped spans, overlap, or conflicting character tiers occur in these two recordings. Existing regressions separately cover anonymous syllables, grouped multi-character words, exact correspondence, punctuation exclusion, final-character timing and half-open ownership. All saved owned samples satisfy `[start,end)`. The final endpoint stays unowned. All three phone originals re-canonicalize **byte-for-byte** to the saved canonical audio, and all three current Praat acoustic results reproduce their saved results exactly. No canonicalization offset or off-by-one assignment was found.

**要:** C [1.06,1.39) retains 20/33 frames, robust-bin change −3.2689 st; B [1.70,2.09) retains 31/39, selected-region change −5.5378 st. Both are falling/moderate/`acoustic_shape_only`; neither is shifted into 一. B’s classifier uses the already-existing independently supported region [1.7525,2.09), excluding two voiced onset frames; Mine correctly retains those display measurements. The current exact-text reading resolver leaves 要 ambiguous among `yao4`, `yao1`, `yao3`. Consequently the actual product reference is null and comparison abstains. External knowledge of intended yào cannot silently repair that input during this audit. Primary useful-feedback blocker: **COMPARISON/reference resolution**, not the classifier or renderer.

**一:** C [1.42,1.63) has 15 retained frames from 1.453 to 1.593 s. Their robust-bin change is −1.7178 st, and the existing classifier returns `ambiguous_shape`, low confidence. This is an appropriate conservative abstention on measured evidence, not a grade of the speaker. B [2.10,2.47) has 28 finite tracker frames, all **52.012–65.638 Hz**, median 56.7315. Every one fails the energy gate: the entire character’s RMS windows are 0.0055–0.010507, below the unchanged recording gate 0.01424265. Only five existing comparison estimates exist (one around 81 Hz, four around 250–257 Hz); they do not establish a complete reliable rising contour. There is no good primary rising trajectory being discarded, and no retained evidence sent to the classifier. Primary observed failure: **RAW_F0**; filtering is the immediate mechanism leaving the cell empty. Capture susceptibility is plausible but not isolated experimentally.

**苹:** C [1.88,2.25) has 27/37 finite and retained frames, 1.983–2.243 s, 107.846–124.922 Hz; change +2.1282 st; rising/moderate/consistent. B [2.76,3.45) has 42 finite primary frames, all **52.481–62.122 Hz**, median 54.4875. Thirty-three fail energy selection; the remaining nine fail the existing contamination/disagreement check. At 24 shared timestamps from 2.9625 to 3.1925 s the existing comparison path is 209.494–219.519 Hz, with median comparison/primary ratio **3.9955**. The spectrogram also shows a harmonic trajectory in that interval. This is strong evidence of a roughly quarter-frequency primary path in low-frequency background, not evidence that a valid ~210-Hz primary contour was discarded. Primary observed failure: **RAW_F0**, with correct downstream abstention. Its rising comparison evidence remains inside 苹 in absolute time. No fallback substitution was performed.

B’s visible rise around 4.0425–4.1425 s is inside provider 果 [3.46,4.41), a separate acoustic region from 苹’s 2.96–3.19-s comparison trajectory. The ~394-Hz branch at 3.9525–3.9825 s is rejected; three raw jumps >12 st in 果 explain its unstable/uncertain result. There is **no evidence of a 苹→果 rendering or sample-assignment shift relative to provider timing**. Independently verifying all phonetic boundaries would require labeled audio; this audit does not elevate valid provider structure into phonetic ground truth.

Across the inspected critical speech cells, there is no demonstrated contradictory classifier label. Low raw estimates and failed selection precede the classifier in B. A’s per-character classifier correctness remains untested. Filter attrition is real and quantified, but removal of demonstrably good primary 一/苹 F0 was not established. No deterministic assignment, coordinate-conversion, or render-index bug was found, so no production fix was made.

An additional reference mismatch exists outside the three critical syllables: the requested contextual expectation for 个 is neutral, but the saved backend uses gè/T4, `surface_rule=unchanged`. B therefore displays 个 as falling/consistent. This is a contextual-reference/comparison limitation, not proof of a lexical tone in the recording. T3 characters remain uncertain; none was forced positive.

## Mobile/backend correspondence

The audit transpiled and executed the current `normalizedMine()`, `toneGestureMatch()` and `normalizedGeometry()` functions. All **43/43 C**, **37/37 B**, and **34/34 N** owned backend Mine vertices retain their timestamp, semitone height and expected owner. Detail exposes all **102 C / 146 B / 76 N** selected measurements; C has one retained inter-character sample in detail without a Mine owner. A has 70 detail measurements and zero attributed Mine vertices. Mine intentionally draws the backend’s smoothed/simplified vertices, not every full-resolution retained point.

Normalized x is `cell_start + .12 + .76*(timestamp-start)/(end-start)`. These six-cell examples have extent 6 and no pause separators. At a 608-px plot, actual x is `4 + normalized_x/6*600`. Shared y is `4 + 128 - (st-domain_min)/(domain_max-domain_min)*128`; the domain is calculated once for the utterance, not once per cell.

| Control | Backend timestamp | Expected cell | Rendered normalized x |
| --- | --- | --- | --- |
| C | 1.0630 → 1.2530 | 要 | 1.126909 → 1.564485 |
| C | 1.4530 → 1.5930 | 一 | 2.239429 → 2.746095 |
| C | 1.9830 → 2.2430 | 苹 | 4.331568 → 4.865622 |
| B | 1.7125 → 2.0725 | 要 | 1.144359 → 1.845897 |
| B | NA: no retained samples | 一 | NA; empty cell |
| B | NA: no retained samples | 苹 | NA; empty cell |
| A | NA: no timing | 要 / 一 / 苹 | NA; no attribution |

Cell/plot padding, shared y mapping, segmentation, group handling, scroll reset and final-cell reachability are covered by the passing native/web graph suites. The measured geometry fits inside plot bounds; no evidence of clipping or character-index drift was found. No new physical-device screenshot/session was available, so runtime device-specific clipping cannot be ruled out from this pass. The reported blank cells are already explained by backend zero retention: **no DISPLAY failure demonstrated**.

## A/B/C acoustic comparison

| Metric | A direct native, canonical replay | B phone TTS | C human |
| --- | --- | --- | --- |
| Duration | 1.050 s | 4.435 s | 2.856 s |
| RMS, full scale = 1 | 0.07721 | 0.03023 | 0.03221 |
| Peak / clipping fraction ≥.98 | 0.3834 / 0 | 0.3844 / 0 | 0.2109 / 0 |
| Raw finite / total | 74/100, 74.0% | 253/438, 57.8% | 204/280, 72.9% |
| Retained / total | 70/100, 70.0% | 146/438, 33.3% | 102/280, 36.4% |
| Retained / finite raw | 94.6% | 57.7% | 50.0% |
| Frame periodicity ≥.45 | 74.0% | 56.8% | 72.9% |
| RMS q90/q10 dynamic proxy | 35.44 dB | 19.67 dB | 23.94 dB |
| Active-window spectral tilt | −4.49 dB/octave | −5.18 dB/octave | −7.85 dB/octave |
| Active-window 80–1000 / 1000–4000 Hz energy | 11.48 dB | −3.98 dB | 18.68 dB |
| Saved provider SNR field | NA | 12.728 | 15.167 |
| Character timing | unavailable | 6 direct graphemes | 6 direct graphemes |

The dynamic proxy is `20*log10(q90_RMS/q10_RMS)` on 40-ms windows every 10 ms; it is **not measured SNR**. Tilt is a least-squares spectral-power slope across octave bands centered at 125–4000 Hz in windows above max(0.003, 0.2×q90 RMS). Spectral comparisons depend on speech content, voice, rate and silence. The original phone files are stereo 44.1-kHz M4A, canonical files mono PCM16 16 kHz. Offline canonicalization reproduces both exactly.

B versus A has −36.7 percentage points retained whole-recording coverage, −16.2 points raw coverage, −15.77 dB dynamic proxy and about −8.15 dB RMS. These are **unpaired descriptive differences**: A is Azure, B is Google, and the clean digital Google source is not cached. Different voices, renditions, speech rate and padding confound a numerical estimate of speaker→room→phone degradation. A’s missing timing also prevents the proposed “A works, B fails” syllable-level conclusion. No causal capture-only percentage is claimed.

B versus C has better retained coverage for 要 (79.5% versus 60.6%), but zero evidence for 一/苹 versus 71.4%/73.0% in C. Summing all character spans gives B 146/305=47.9% retained, C 101/214=47.2%; that aggregate hides the loss of both critical rising controls. The human recording supplies more useful critical-syllable evidence overall. C’s 一 measures a modest fall, not a certified rise, and both have unreliable final 果 evidence. None of these observations ranks speakers or establishes overall pronunciation quality.

## Additional negative control

The user-confirmed accidental no-speech take N is **not** a speech control and is not relabeled. The immutable saved result accepted its transcript, alignment, attempt and graph. Current offline `require_speech()` also accepts it. Its samples are not digital silence: RMS 0.02041, activity-run 0.29 s, periodic-run 0.47 s. The current guard skips spectral corroboration because sustained activity is present. These measurements describe why its permissive path was taken; they do not overturn the user’s source label or establish who/what produced the background signal.

Under the supplied no-speech ground truth this is a **failed negative-control regression**. It can even produce 个 “consistent” under the current T4 reference. The two previously known false-accept controls still reject correctly. No silence-rule tuning or reinterpretation of persisted truth was made in this audit.

## Changes, replay and validation

Production bug fixes: **none**. Production tests added: **none**, because no deterministic code bug was established. Ignored replay assertions verify hashes, byte-identical phone canonicalization, full saved/current acoustic equality, classifier equality on all 18 timed units of B/C/N, saved/current graph equality, exact mapper equality, and every rendered owned Mine vertex. A replay metadata fixture and the normal canonical derivative were saved locally. It deliberately has null native timing/gesture expectations rather than invented passing labels.

| Validation | Result |
| --- | --- |
| Focused API: graph, grouped evidence, contour/readings, evidence-region selection, perceived speech, presence | 200 passed; initial 2 opt-in real-silence checks skipped pending restored inventory |
| Presence suite rerun with restored exact prior-negative inventory | 22 passed, including those 2 real controls; no remaining coverage gap from the initial skips |
| Connected speech and connected replay | 69 passed |
| Mobile native/web SentenceToneGraph, toneGestureMatch, historical learnerVerdict | 72 passed, 4 suites |
| B/C/N fresh acoustic and graph replay versus saved data | exact equality |
| Fresh observed contours versus saved B/C/N | 18/18 exact equality |
| Actual mobile owned Mine mapping | 114/114 vertices exact, none duplicated or reassigned |
| User-confirmed latest no-speech replay | **FAIL: accepted**; reported separately from passing code regressions |
| Production changes requiring Ruff/mypy/mobile lint/export | none; no production static-check/export rerun needed |
| `git diff --check` and preservation of baseline tracked diff | checked at completion; see local final Git artifact |

Commands, stdout and source hashes are retained in ignored storage. The initial PostgreSQL container was stopped after restart; only the existing local database container was started to recover read-only evidence. No API server, provider, deployment or schema mutation was started. Original audio remains in its existing ignored store. The report CSV contains measurements/metadata, not audio or provider secrets.

## Decisions and one bounded next step

1. **DIRECT NATIVE CONTROL: FAIL.** This is a failure to meet the acceptance/evidence requirement, **not proof that native 要/一/苹 are acoustically misclassified**. Direct extraction succeeded; trustworthy native per-character timing and resulting classification/comparison were unavailable. A passing native calibration claim cannot be made.
2. **PHONE-RECORDED TTS: NOT ROBUST ENOUGH.** Two of three critical controls have zero retained evidence; 要’s acoustics are useful but its reference comparison is unresolved. The pipeline is not useful enough on this recapture even though conservative abstention avoids false “different” labels.
3. **LEARNER FEEDBACK READINESS: DEMOTE FEEDBACK TO DESCRIPTIVE UNTIL CALIBRATED.** This is the audit recommendation, not an implemented UI/policy change. Missing native acceptance, B’s raw-path failure, unresolved/wrong-context reference inputs and the additional no-speech false accept prevent a justified readiness claim.

**Only next step:** complete a verified **offline character-timing fixture for this exact cached Azure file**, then replay the unchanged pipeline on 要/一/苹. This is one bounded native-control alignment task on one existing file. It supplies the missing baseline before any extraction, filtering or classifier tuning is justified.
