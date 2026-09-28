# Pronunciation architecture review — 2026-09-23

**Outcome:** one defensible recovery, not four forced passes. Latest phone 妈 changes from unclear/tracker instability to moderate-confidence 1-like → **Matches / Tone 1 ✓ / Good**. Latest 马 and 骂 remain unclear. 嘛 remains a contextual neutral target with independently observed 3-like shape. Production Praat, its parameters, candidates, energy/contamination gates and raw evidence are unchanged.

Current branch is `pronunciation-calibration`; committed checkpoint is `a8bdfab3d00365c00e1a10881e8999df63f2823c`. Earlier uncommitted work is preserved. No commits, branch switches, resets, stashes, paid provider calls, production evidence writes, or performance/UI milestones were performed. PostgreSQL test writes were confined to disposable isolated schemas.

## Architecture before and after

The [pre-implementation audit](architecture-before.md) maps recording, native/web capture, canonical conversion, perception, persisted target, assessment, alignment, acoustic extraction, candidate/path selection, energy and contamination gates, timing reconciliation, core selection, gaps, classifier, learner verdict, display, details and provider scores. It records each stage's provenance and authority.

Before: aligned syllable → selected F0/reliable filtering → whole-span jump/contamination/coverage gates → limited level-tail hypothesis → broad shape classifier. The object called `display_contour` was also the classifier input. This naming hid a real architectural coupling. The client normalized graph was already display-only.

The actual failure was **scope mismatch in quality evaluation**: peripheral raw tracker branches could veto an otherwise coherent interior. A later onset hypothesis could not undo the already-computed whole-span jump rejection. This did not prove that every rejected recording contained a recoverable tone.

After: validated alignment + raw per-frame evidence → `select_tone_evidence` → immutable internal `ToneEvidenceRegion` → reliable pitch derived directly from raw frames → quality/classification of that region → learner verdict → display. The compatibility positional contour argument to `classify_contour` is deliberately ignored; a regression passes a fabricated flat display with rising raw evidence and still gets 2-like. Full-resolution reliable filtering retains its existing Hampel/island rejection and median-of-three behavior. The visual normalization/smoothing cannot drive classification.

Region selection happens before the grading calculation. A second calculation over the whole aligned span supplies **diagnostics only**, stored under `whole_span_*`; it cannot choose the interval or veto the selected result. Public `voiced_coverage`, `full_span_coverage`, original duration and alignment bounds remain whole-span provenance. Explicit `evidence_coverage`, `evidence_duration_seconds`, start/end and exclusion counts describe what was judged.

`ToneEvidenceRegion` is a conservative acoustic support region, **not an asserted phonetic rhyme alignment**. No phoneme recognizer or new spectral segmentation model was added. No target tone, text, initial, final or intended label enters the selector. Rhyme/nucleus is the phonetic motivation for refusing to weight every boundary sample equally, not a claimed available annotation.

## Exact Tone-1 diagnosis

Attempt `1c69a605-e679-40ec-a834-d348b2e4d005`, utterance `ea38ee3a-7a65-4624-8399-92a81b17df7b`, target `9cd680f3-5eba-4f38-8f84-5abc4a8a46b8`, created **2026-09-23 15:52:43.538602 UTC / 11:52:43 EDT**. Persisted target is 妈 / ma1. Azure aligned the whole syllable to **0.68–1.37 s**.

| Time (s) | Raw selected F0 (Hz) | Candidate strength | RMS | Independent high-pass F0 | Treatment |
|---|---:|---:|---:|---:|---|
| .7306 | 62.450 | .5963 | .007508 | none | Excluded weak boundary frame |
| .7406 | unvoiced | selected strength 0; 177.751-Hz candidate .5518 | .016716 | 176.693 | Missing observation; never invented |
| .7506 | 166.166 | .6043 | .024227 | 165.878 | Excluded weak attack |
| .7606 | 145.253 | .6789 | .033293 | 145.180 | Excluded weak attack |
| .7706 | 137.312 | .8839 | .039066 | 137.289 | Retained |
| .7806 | 133.540 | .9587 | .043136 | 133.529 | Retained |
| .7906 | 131.151 | .9855 | .047244 | 131.140 | Retained |
| 1.1906 | 129.677 | .8245 | .022412 | 129.582 | Last retained frame |
| 1.2006 | 65.585 | .8181 | .015508 | 130.570 | Excluded terminal disagreement |
| 1.2106 | 65.481 | .8035 | .011104 | 130.815 | Excluded terminal disagreement |
| 1.2206 | 65.282 | .7964 | .010339 | 130.659 | Excluded terminal disagreement |
| 1.2306 | 64.857 | .8103 | .008817 | 129.784 | Excluded terminal disagreement |
| 1.2406 | 64.599 | .8458 | .007680 | 129.154 | Excluded terminal disagreement |

The original gate counted **16.942 st** between .7306 and .7506, plus a terminal octave-like event. Five terminal frames were already marked unusable by filter disagreement, yet their raw jumps still counted. It rejected the whole syllable before a core could help.

The ~62-Hz branch also exists before speech reaches the energy gate. Its lack of an independent high-pass pitch estimate, low energy and transition to a different candidate family support a boundary tracker/background branch. The brief 166→145→137-Hz movement coincides with rising amplitude and rapidly strengthening periodicity. Waveform and spectral evidence support vocal attack/transition as a plausible interpretation; they **do not identify an /m/-to-/a/ boundary**. Some early high pitch may be real attack pitch. The rule retains the strongly supported 137→133→131-Hz transition rather than erasing all onset movement.

At the terminal edge, independent high-pass estimates remain near 130 Hz while the raw path falls to ~65 Hz. Both candidate families exist: at 1.2006 s the ~130.686-Hz candidate has strength .8006, versus .8181 for the selected ~65.585-Hz candidate. The analysis excludes these fading ambiguous frames; it does not double them or claim their true F0 is established.

Final region: **[.7706, 1.2006) s**, 43 measured frames through 1.1906 s, **430 ms**, full coverage within that region. Three voiced attack frames and five terminal voiced frames are excluded; the .7406 missing frame is not counted as a fabricated or rejected voiced sample. Robust five-bin heights are **[.3294, −.2580, −.0995, .0908, .0187] st** relative to the retained filtering baseline. Range **.5874 st**, net change **−.3107 st**, maximum retained raw step **.4822 st**. Existing level-category conditions apply unchanged. Whole-span coverage remains .6667; it is not rewritten as perfect recording coverage.

[Waveform/spectrum/F0 plot](ma1-evidence.svg), [full numerical candidates and evidence](newest-evidence.json).

## Why the boundary rule is bounded

The new module accepts only raw evidence and numerical alignment bounds. It has no expected-tone argument and no shape-template search. Synthetic tests apply the same weak-boundary pattern to level, rising, dipping and falling interiors. The learner test then supplies different expected tones to the same unchanged observed evidence: Tone 1 matches; 2/3/4 differ; the selected evidence is identical.

For an attack exclusion it requires a brief peripheral span (at most 80 ms and 20% of voiced extent), weak periodicity, low amplitude relative to sustained supported speech, and actual path loss/disagreement. Three consecutive frames must establish strong periodicity and agreement with the existing independent comparison. A weak but continuously supported voiced onset is retained. A strong onset with different pitch is retained. All earlier high-energy unvoiced activity blocks this exclusion.

For a terminal exclusion it requires an already rejected short terminal branch, fading energy, >6-st raw/comparison disagreement, and a comparison track that remains near the preceding supported pitch. Later high-energy unvoiced material prevents trimming. At least 14 voiced frames and 70% of original voiced samples must remain. These are conservative engineering support requirements, not population-calibrated phoneme boundaries. They are tested as invariants, not tuned to the intended target.

Interior gaps, jumps, low phonation and sustained octave ambiguity remain in the evidence and face existing quality rules. The previous conservative onset-level and short-fall classifier rules remain intact; they were not broadened.

## Why Tone 3 remains unclear

Attempt `9714fc1d-3e61-4a7f-a32f-464d517a9a7f`, utterance `17026603-6bd6-4b25-b970-7617f8bb1d6f`, 15:54:13 UTC, alignment **.58–1.31 s**. The retained extent is .6511–1.1111 s, 38 retained frames over 470 ms, with three breaks and two discontinuous gaps.

Selected tracking disappears at **.7811–.8111 s** and **.9411–.9711 s**, both inside the active speech. The .8911-s selection has strength .4211 and is filtered from the reliable contour. During the first dropout, plausible 114/106/98-Hz candidates have strengths roughly **.43–.48**; during the second, 89/95/98/101-Hz candidates have strengths **.27–.42**. Those are candidate hypotheses, not confidently measured missing F0.

The descent from 113.566 Hz at .7711 to 78.125 Hz at .8211 is **6.476 st across 50 ms**; the current jump gate treats it conservatively. The waveform, continued energy and low-frequency candidates make irregular/creaky phonation more plausible than silence or simple hum. Low-band energy is small, so the ~78-Hz trough is not automatically rejected as contamination. A broad dip/recovery is visible, but its interior support is not strong enough for this pass to certify the category. This is a measurement limitation, not a judgment that the user pronounced Tone 3 incorrectly. No interpolation, octave unwrapping, target-selected path or relaxed threshold was introduced.

[Evidence plot](ma3-evidence.svg).

## Why Tone 4 remains unclear

Attempt `124c4065-3001-44b9-b717-3799c232e454`, utterance `1120cb8a-4b88-4cac-9ba3-7229b65e2c6a`, 15:54:34 UTC, alignment **.59–1.12 s**. Reliable selected pitch is **.6718–.8018 s**, 14 frames / **140 ms**, approximately 163→145 Hz. Robust bin change is **−1.587 st**, below the unchanged ordinary falling-category requirement. Whole coverage is .2642 and boundary-tolerant coverage .4695, below the existing .5 gate.

The last tracked frame is near maximum RMS (.152). RMS stays **.145 at .8118**, **.130 at .8218**, and **.100 at .8318** while Praat chooses unvoiced. This is substantial active audio, not established padding. At .8118 the 140.525-Hz candidate has strength .4914, then .2895 at .8218; later candidates are inconsistent. The current evidence cannot safely distinguish benign terminal devoicing from irregular/noisy tone-bearing vowel material. Merely changing the denominator would hide this uncertainty, and would not independently establish sufficient broad fall.

Future safe recovery would need independent periodic/pulse evidence supporting a coherent continuation, a validated tracker strategy on broader human data, or trustworthy phonetic timing showing that the uncertain portion is outside the tone-bearing region. A new labeled recording could establish pronunciation acceptability but would not retroactively prove this missing track. This sample remains **Unclear**, not Different.

[Evidence plot](ma4-evidence.svg).

## Tracker foundation and phonetic timing

Praat remains **raw autocorrelation**, Parselmouth .4.7 / bundled Praat 6.1.38: floor 50 Hz, ceiling 550 Hz, hop 10 ms, voicing .45, silence .03, octave cost .01, octave-jump .5, V/UV .14, 15 candidates. No production F0 settings, candidate paths, dependencies, repairs or acoustic version changed in this pass.

The offline comparisons use existing raw AC, default-jump AC (.35), raw cross-correlation and a Gaussian low-pass experiment. The latter follows the documented filter shape but is **not claimed to reproduce modern Praat's command exactly**; bundled Praat predates that command. All comparisons are diagnostic probes, with shared basic energy gating; they are not interchangeable validated production quality pipelines. Lower jump cost recovers the newest fall but breaks accepted level recordings. Filtered experimentation changes multiple contours and still leaves Tone 3 fragmented. There is no adequately labeled corpus establishing an accuracy gain, so neither replacement was adopted. No YIN/pYIN dependency was added; introducing its maintenance/package/runtime burden without validation would not be justified.

[Praat raw-AC documentation](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html) describes the candidate/continuity tradeoffs. [Current method guidance](https://www.fon.hum.uva.nl/praat/manual/how_to_choose_a_pitch_analysis_method.html) recommends filtered AC for intonation; [filtered-AC documentation](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_filtered_autocorrelation.html) specifies the Gaussian filter. These motivate comparison, not an automatic upgrade. [Xu and colleagues' consonant-perturbation study](https://dihana.cps.unizar.es/proceedings/ICASSP/2003/pdfs/01-00456.pdf) also cautions against treating all initial F0 movement alike; /ma/ is not a universal onset template.

Azure's stored SAPI “Phonemes” are `ma 1`, `ma 3`, etc.—whole pinyin syllables. They do not provide usable /m/ and /a/ timing. Pinyin reading structure is available but does not establish acoustic boundaries. No such timing was fabricated or used.

## Fixture truth and evaluation authority

The latest recordings are real uploads, canonicalized to mono 16-kHz PCM16. Perception is real OpenAI evidence; alignment is live Azure timing; acoustic evidence is local Praat. The configured assessment provider is **replay**. `ReplayPronunciationProvider.assess` hard-codes **pronunciation_score=79**, overall score 81, empty syllables, `synthetic_replay`, independent of the recording. The warning originates from that normalized assessment status. The value is static development data persisted in AssessmentRun, not an Azure pronunciation result. Azure alignment strips scoring fields from its timing payload.

Current local reference-TTS configuration is also replay; none of these four result records has attached successful reference audio. ReferenceSpeech remains separate. Browser tests use explicitly mocked reference/audio transport, not human/reference recordings. No real synthesis was invoked.

Previously the local learner verdict already ignored provider scores, but normal-looking “accuracy 79” was still displayed in details (and in the older screenshot UI, above the cards). The older interpreter also lacked an explicit fixture guard for provider detected-tone observations; the stock replay payload has no detected tones, so no evidence establishes that this theoretical path changed these four verdicts.

Now live assessment requires succeeded execution, explicit `live_provider` provenance and a non-replay adapter. Fixture/unknown evidence cannot provide syllable assessment/timing fallback or interpreted provider-tone judgments. Historical runs remain immutable; fixture-derived observations are filtered from current learner projections. Raw assessment payloads remain available as provenance. UI requires live provenance before showing supplemental numerical assessment; **79 is absent from learner score output**, including expanded details. The warning now says: “Provider assessment is a development fixture. Tone feedback uses local recording evidence.” Old endpoint-only local interpretation messages are no longer repeated as learner explanations; the explicit region classifier owns that explanation.

Authority is now explicit:

1. Recorded samples, immutable perception and accepted alignment provide facts.
2. Raw acoustic support selects the region, independently of intended tone.
3. Region quality and classifier provide the observed category/confidence.
4. Recording-wide quality remains context; it cannot independently veto a certified region.
5. Real provider assessment can supply labeled supplemental details; fixture assessment supplies no grading truth.
6. The client derives one primary Matches/Close/Different/Unclear result from expected surface tone and the observed category. Neutral remains context-dependent.

## Corpus and generalization

[Recomputation](recomputation.json) and [actual client verdicts](learner-recomputation.json) cover **46 local recordings / 88 numerical syllable spans**. **83 spans have usable timing; five remain timing-rejected.** This is a convenience calibration set, not 88 independently labeled human pronunciation judgments and not the real pilot.

On persisted F0: **one region changes, one classifier label changes, one primary learner verdict changes**—the newest 妈. All other labels/reasons remain unchanged. Local WAV re-extraction also changes only this authorized category. An additional raw DSP probe on old 活 excludes one fading terminal frame at 2.6327 s and changes the diagnostic rejection reason from tracker instability to fragmented voicing; that recording uses old unverified timing and remains ungradable. The tool now explicitly quarantines all such unvalidated-timing probes from learner results. No synthetic/equal split is used to authorize grading.

| Control | Persisted before → after |
|---|---|
| Accepted phone 妈 `c728c5e3…` | 1-like → 1-like |
| Clear rise 麻 `12df6d8f…` | 2-like → 2-like |
| Accepted phone 马 `fcac1921…` | 3-like → 3-like |
| Accepted phone 骂 `49b10b69…` | 4-like → 4-like; 180-ms coherent evidence preserved |
| Neutral 嘛 `70411287…` | 3-like → 3-like; no categorical neutral mismatch |
| Desktop fragmented control `9957925d…` | unclear/fragmented → same |
| Octave-unstable 啊 `4fbf587d…` | unclear/tracker instability → same |
| Earlier low/subharmonic phone 马 `618b19d5…` | unclear/contamination → same |

Human recordings in the broader set include 你、好、今、天、我、们、聊、周、末、吧、冰、淇、淋、睡、觉 and noisy 啊. These cover nasal, lateral, fricative, stop/affricate, aspirated onset, diphthong and nasal-final structures. The persisted regression fixture includes two multi-syllable phrases plus noisy zero-initial 啊 and the eight recent phone controls. **Their unchanged outputs are regression evidence, not proof of phonetic accuracy or dialect/speaker generalization.** No reliable initial/final hand boundaries are claimed.

Synthetic invariants separately cover continuous/strong different-pitch onsets, weak attacks across all four shapes, terminal disagreement, unvoiced onset, zero initial, short rhyme, short/long interior dropout, bad core/sustained octave errors, high-energy unvoiced offsets and base F0 at 90/180/320 Hz. Existing frontend tests cover broadband taps, hum, clean contours and missing frames. Synthetic vowels do not prove human-speech accuracy.

Pilot readiness remains **0/50 real pilot recordings**, unchanged. `architecture_review.py` supports offline evidence/candidate strategy review; `review-verdicts.cjs` runs the actual pure TypeScript verdict function and optionally consumes separately reviewed labels for mismatch/unclear rates. Target labels never enter tracking, region selection or observed classification. No reviewed labels were supplied, so mismatch rate is null rather than an invented accuracy claim.

## Runtime, UI and validation

Region selection alone: median **.054 ms**, p95 **.085 ms**, worst per-syllable median **.124 ms**, largest observed call **.155 ms** (31 repetitions per span). Full local extraction plus per-recording classification: median of recording medians **25.72→25.83 ms**, p95 **77.71→98.67 ms**, worst recording median **126.03→131.60 ms**. Newest Tone 1 **26.17→26.98 ms**, largest measured after call **27.16 ms**. Longer multi-syllable recordings account for the tail; these local wall measurements ran alongside validation and are not a production SLA. No extra tracker pass or spectral computation was added to production; the new classifier's display independence does rebuild reliable evidence from raw frames.

The existing full-width, lightly smoothed Mine graph now crops to the explicit selected region, with the same shared semitone scaling and conservative gap policy. Full/raw graphs retain the excluded frames in More detail. Playback, target identity/persistence, immutable perception and neutral/reference semantics remain intact. No visual redesign, perfect/100% score or native-likeness claim was added.

Validation and artifact inventory are recorded in [validation.md](validation.md). Final screenshots use actual persisted acoustic result fixtures with intercepted API/audio transport: [Tone 1](screenshots/touch-1.png), [Tone 1 details](screenshots/touch-1-detail.png), [Tone 3](screenshots/touch-2.png), [Tone 4](screenshots/touch-3.png), [neutral](screenshots/touch-4.png). These are Chromium acceptance, not replacement physical-phone tests.

## Checkpoint and next phone test

The combined branch is suitable for a reviewed development checkpoint after this report and diff are reviewed. It is **not production-calibrated**: phone Tone 3/4 remain unresolved, broader human labeling is absent, and final device acceptance still belongs to the user. No commit was made.

Maximum four new recordings, after loading the current bundle and confirming the visible prepared text/pinyin:

1. **妈 mā** — one natural level production; inspect Matches/Good, selected graph and raw boundary detail, with no normal 79 score.
2. **马 mǎ** — one natural dip/recovery; retain Unclear if interior pitch evidence remains irregular. Do not exaggerate until it passes.
3. **骂 mà** — one natural falling production; inspect usable duration and whether uncertainty persists. Do not force extra duration to satisfy the engine.
4. **天 tiān** — one natural level production with an aspirated non-/m/ onset, for a targeted generalization check.

Persist the four attempt IDs and actual observed results; intended labels are not acoustic ground truth. Neutral behavior is already protected by the current persisted sample and regression tests.
