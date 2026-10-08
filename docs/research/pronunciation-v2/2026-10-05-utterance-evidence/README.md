# Character-free utterance evidence: final report

**AUDIO EVIDENCE != SPEECH PRESENCE != PERCEIVED TEXT != REFERENCE PRONUNCIATION != INTENDED TARGET.**

**ACOUSTIC ELIGIBILITY != PERMISSION TO GIVE LEARNER FEEDBACK.**

**CHARACTER/WORD GRAPHS ARE PROJECTIONS OF ONE IMMUTABLE UTTERANCE ACOUSTIC TRACK.**

The architecture is implemented without a tracker migration, filter redesign, database migration or new concurrency mechanism. Acoustic eligibility now exposes incomplete/unstable regions while retaining useful healthy descriptions. Learner comparisons remain experimental because the newest accidental-silence recording still passes the separate speech-presence guard.

The interrupted RMVPE report was completed and verified **from saved artifacts before production edits**. No RMVPE rerun, 49-file extraction rerun, download, new recording or external provider request occurred. **STOP TRACKER SEARCH** remains the foundation decision.

## Final decisions

1. **UTTERANCE PITCH TRACK SUCCESSFULLY FIRST-CLASS.** Typed immutable audio evidence, existing persistence and traceable projections are implemented and tested.
2. **PITCH RUNS INDEPENDENTLY / CONCURRENTLY WITH PERCEPTION.** This already existed; preserved and verified, not newly introduced.
3. **SAFE GENERIC ACOUSTIC ELIGIBILITY FOUND.** Scoped to generic target-independent detection of incomplete/unstable regions, with healthy-control retention. This is a bounded completeness/stability rule, not global speech detection or proof of estimator correctness.
4. **KEEP ALL TONE FEEDBACK DESCRIPTIVE/EXPERIMENTAL.** Presence acceptance, real timing, acoustic eligibility and allowed reference must all be trustworthy before a learner comparison. Consistent/different remains disabled.
5. **PITCH ARCHITECTURE READY AFTER SEPARATE SILENCE FIX.** The evidence/persistence/projection architecture is sound. This does not certify Praat universally or imply that fixing presence automatically enables comparisons without reviewing all trust gates.
6. **FIX NEWEST ACCIDENTAL-SILENCE FALSE ACCEPT.** One next pass, at the speech-presence layer. No new tracker, tone-classification project or UI polish is proposed.

## Requested 42-point completion record

1. **Production flow:** canonical audio → existing parallel acoustic warmup and unknown-target ASR → validated perceived/target timing → immutable projections → backend eligibility → gated observed gesture → separately experimental comparison. [Verified before/after flow](current-flow.md).
2. **Track contract:** frozen `UtterancePitchTrack`, frozen nested frames/candidates and tuples; no linguistic identity. [Complete field contract](utterance-pitch-track.md).
3. **Evidence ID:** content SHA-256 over audio hash, source/configuration/selection versions, waveform metadata and all typed frames; no database UUID, wall clock or text.
4. **Audio/provenance:** canonical asset hash; analyzer/version/parameter JSON; selection version; explicit native-vs-legacy raw provenance; hash mismatch fails loading.
5. **Raw/selected:** native pre-Benma raw Hz is separate from energy-gated, analyzer-selected and final unsmoothed selected Hz. Existing smoothing is presentation-only; rejected frames keep raw values and reasons. High-pass F0/disagreement is retained as diagnostic evidence.
6. **Extract once:** one successful analyzer invocation per ordinary utterance/configuration, containing primary and existing diagnostic computation. Never per character.
7. **AcousticRun reuse:** account/utterance/algorithm/version/parameter matching under the existing lock; changed transcript/reading/target does not invalidate it. Explicit administrative reruns remain append-only exceptions, not ordinary projection behavior.
8. **Concurrency:** existing bounded optional warmup uses its own session; final analysis retains request-owned persistence. ASR does not wait for pitch to finish.
9. **PostgreSQL:** four isolated-schema integration cases pass: duplicate perceived/raw-acoustic requests and duplicate target requests, with and without warmup; one acoustic run and independent ASR FK persistence.
10. **Character-free regression:** real Praat service/cache tests cover 贵州, 鬼粥, arbitrary text/target, empty metadata and no target; complete snapshot equality includes ID, timestamps, raw/selected values, exclusions and provenance. Distinct saved perceptions and target revisions reuse the track.
11. **Source traceability:** projections carry digest + source frame indices; graph Raw carries the index and reasons. [Projection model](projection-model.md).
12. **Characters:** exact [start,end) ownership; shared boundaries, final frames, punctuation and untimed characters are covered. No invented values or boundary filling.
13. **Words:** word-only 雨伞 owns one whole-word projection; no equal splitting, anonymous-syllable attribution or per-character grade.
14. **Eligibility:** raw voiced extent, selected support, temporal thirds, attrition, head/tail loss, islands, gaps and raw discontinuities; sufficient/incomplete/unstable/insufficient. [Exact rule and tables](eligibility.md).
15. **Presence distinction:** local periodic support cannot establish global speech presence or voice ownership. Comparison permission is a third, separately disabled gate.
16. **Repeated 苹:** takes 1/3 lose 160/150 ms of late raw evidence and change Level-like → Unclear/incomplete. Take 2 stays Rising/sufficient. No take is repaired into an expected tone.
17. **一:** all three repeats continue Unclear; diagnostics expose 80–100-ms maximum islands, gaps and 11.84/12.15-st jumps in takes 1/3.
18. **州:** the historical 21.88-st jump is explicitly recorded; primary state insufficient (100-ms island), with instability reason. No octave/branch repair.
19. **吧:** all four saved difficult cases abstain; no evidence or too little sustained evidence (0/0, 0/0, 17/8, 6/6 raw/selected frames).
20. **Healthy retention:** 50 prior classifiable speech regions → 37 after gating; 70/140 speech regions acoustically sufficient. Three named healthy human 苹/要 controls retain 3/3 observations; rising/falling shape controls retain 2/2. Human-control 要's conservative loss is explicitly reported.
21. **Low F0:** no low-frequency veto in eligibility; coherent 54/60/70-Hz controls remain sufficient. All 11 saved under-70-Hz proxy frames remain selected unchanged. Legacy filter limitations remain separate.
22. **Negatives:** six recordings; 12 saved character/whole-waveform regions, two prior classifiable observations → zero after gating. One saved accidental-silence region is locally sufficient; stress scanning finds 61 sufficient windows.
23. **Silence lesson:** this counterexample is retained rather than concealed by an acoustic threshold or ID/character hack. Eligibility is not presence detection.
24. **Gesture gate:** only sufficient regions retain an existing observed category; otherwise unclear/low with explicit evidence-state reason, preserving diagnostics and plots. Existing classifier ambiguity still abstains.
25. **Comparison gate:** `tone_comparison_policy=experimental`; mobile always uncertain, including sufficient Rising/T2 or Falling/T2. No pronunciation grade is added.
26. **Mobile:** backend owns acoustics; mobile presents sufficient descriptions and incomplete/unstable wording, neutral cells, original characters and separate references. Shared Practice/Free Practice/Conversation paths remain intact.
27. **Detail/Raw:** Mine retains measured fragments, More Detail uses unsmoothed selected samples at real times, Raw keeps original Hz/timestamps/source indices plus exclusions. Abstention erases no measured evidence.
28. **Replay:** typed saved tracks deserialize without extraction/refiltering; old raw JSON is wrapped without mutation or tracker execution. Legacy compatibility wrapper persistence limits are explicit in the contract.
29. **Latency:** warm extraction 41.56 ms; new fresh-track construction/serialization about 8.12 ms once; typed replay 1.25 ms. Projection/eligibility medians approximately 0.03/0.05 ms per region. Gesture and comparison timings are included in [latency](latency.md); no new concurrency or live turn-speedup claim.
30. **Backend changes:** `pitch_types.py`, `pitch_evidence.py`, `acoustics.py`, `contours.py`, `perceived.py`, `laboratory.py`, `tone_graph.py`, `schemas.py`; regression fixtures/tests, saved-only replay script. No presence/reading/tracker-configuration change.
31. **Mobile changes:** `toneGestureMatch.ts`, `SentenceToneGraph.tsx`, their tests, generated OpenAPI/TypeScript contracts. No workflow/UI redesign.
32. **Tests:** 525 bounded API passes, four PostgreSQL integration passes, 69 connected-speech passes, 331 mobile passes across 26 native/web suites. [Validation details](validation.md).
33. **Static/build:** Ruff, touched Python formatting, mypy (78 source files), mobile lint/typecheck, web export, Android export and diff whitespace checks pass.
34. **Limitations/failures:** the unbounded API attempt stalled in an unchanged streaming test; bounded suite excludes 22 streaming/meaning tests. A mobile render timeout under concurrent build load passed on isolated full-suite rerun. No unrelated application debt was changed; validation distinguishes these from executed passing checks.
35. **Accidental silence:** exact saved waveform still accepted by unchanged presence logic; no confident learner comparison can escape the separate experimental policy. The synthetic clicks control also remains a presence regression for that next pass.
36. **Decision 1:** UTTERANCE PITCH TRACK SUCCESSFULLY FIRST-CLASS.
37. **Decision 2:** PITCH RUNS INDEPENDENTLY / CONCURRENTLY WITH PERCEPTION (pre-existing).
38. **Decision 3:** SAFE GENERIC ACOUSTIC ELIGIBILITY FOUND, scoped to local completeness/stability.
39. **Decision 4:** KEEP ALL TONE FEEDBACK DESCRIPTIVE/EXPERIMENTAL.
40. **Decision 5:** PITCH ARCHITECTURE READY AFTER SEPARATE SILENCE FIX.
41. **Decision 6:** FIX NEWEST ACCIDENTAL-SILENCE FALSE ACCEPT.
42. **One next pass only:** investigate and fix that exact presence failure at its own layer, retaining all existing speech/negative regressions.

## Eventual physical smoke set

Prepared only; no new recording requested or collected: normal 我要一个苹果; the same sentence with intentionally falling 苹; target 广州 with acoustically altered 贵州; 我想买五把雨伞 with grouped word timing; silence during the separate guard pass. Verify immutable audio evidence, honest interval projection and supported descriptions; no expected-tone-driven repair.

The narrow quantity-context 要 resolution and lexical gè/T4 with optional reduction remain unchanged and are covered by the backend suite. All work remains uncommitted on `pronunciation-v2-research`; nothing was pushed or deployed.
