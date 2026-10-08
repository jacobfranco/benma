# Observed gesture + pre-lexical speech architecture pass

**Ship conservative acoustic gesture feedback and grouped word pitch.** The latest 苹 is already classified falling with moderate confidence and differs from T2; the UI integration was missing. Keep the acoustic classifier unchanged. Keep T3/neutral/unstable evidence uncertain. A segmental gibberish engine remains future work, with a character-free contract and no fabricated observed sounds.

Read the [exact recordings and acoustic audit](observed-gesture-audit.md), [current/product/future architecture and policy](current-vs-target-architecture.md), [ObservedSpeechUnit contract](prelexical-contract.md), [local capability inventory](capability-inventory.md), and [validation/runtime](validation.md). Current learner behavior and smoke instructions are also in the [development guide](../../../development/tone-graph-v2.md).

## Completion report

1. **Recordings:** latest perceptions `02927481-5174-478d-a40a-6cece40b98df` (T3 sentence), `e0c56934-0bcb-47fd-aab3-a636f45092cb` (apple), `dccf8a63-0e0f-4458-82ce-facda812c8e3` (去吧), `9b1d959a-f7ec-453a-8728-1a1c685606e7` (target 广州 / perceived 贵州). UTC times, utterance/attempt/analysis/asset IDs and canonical hashes are in the audit. Fifteen prior useful takes retained; 19 canonical hashes verified.
2. **Latest 苹 classification:** `4-like / moderate / acoustic_shape_only`, [1.80,2.17), 21/37 raw/retained frames, five-bin change −5.0471 st.
3. **Latest 苹 legacy verdict:** `different` against contextual T2; new policy is also `different`.
4. **Visual/classifier agreement:** yes. Mine and unsmoothed retained contour both fall; full selected endpoints fall 5.6886 st. Outcome A: missing integration, no classifier tuning.
5. **Latest 贵:** `1-like`, mapped level-like, with a shallow valley under coarse robust-bin thresholds. Reference guì/T4, comparison different, character unchanged.
6. **Latest 州:** `unclear`; reference zhōu/T1, comparison uncertain, character unchanged.
7. **贵/州 confidence/reasons:** 贵 moderate/`acoustic_shape_only`, 25/43 retained, robust range 1.0524 st. 州 low/`low_frequency_contamination`, 25/60 retained, contamination .2188, rejected instability 1, maximum raw jump 11.8818 st.
8. **去/吧:** both unclear/low/`insufficient_voicing`, only 7/13 and 6/31 retained frames (70/60 ms). Neutral 们 may be observed level-like without a comparison.
9. **T3:** heavy-sentence 我/买/把 observed rising; 想/五 ambiguous; all uncertain. Apple 我 falling and 果 rising are also uncertain despite lexical/contextual T3.
10. **Failure found:** historical T3 `different` assumes a full categorical shape too readily for connected speech. No confidently reversed rise/fall found in the latest classifier outputs. Coarse 贵 level-like naming and short-pitch abstention are documented limits, not rewritten results.
11. **Classifier change:** none in this pass; existing uncommitted contour diagnostics are preserved. No pitch extraction/selection/smoothing/threshold change.
12. **Observed vocabulary:** level-like; rising; dipping / valley-like; falling; unclear. Internal semantic enums are level/rising/dipping/falling/unclear.
13. **Comparison policy:** reliable character timing + resolved contextual T1/T2/T4 + moderate confidence + `acoustic_shape_only` + contamination <.15 + no rejected instability/discontinuous gap. Equal expected gesture→consistent; other eligible gesture→different; otherwise uncertain. Product policy is separate from unchanged `learnerVerdict`.
14. **T3 policy:** all surface T3 uncertain; no full-dip requirement. An already-resolved T3→T2 sandhi reference can use the T2 comparison.
15. **Neutral policy:** always uncertain; no fixed neutral shape invented.
16. **Cell states:** consistent positive, different warning, uncertain neutral; whole word `grouped_evidence` gets a neutral group region with no individual grade. Accessible wording says “tone gesture …”.
17. **Tap:** Observed pitch, Observed confidence, Reference tone, Tone gesture, separate lexical reading; timing/evidence and group attribution explanation. Default remains contour + character without tone labels.
18. **No detected lexical tone:** no new `detected_tone`, no “Detected tone: T4”, no overall correct/wrong pronunciation. Existing legacy provider DTO fields are not promoted into this UI.
19. **雨伞:** `PerceivedTimingGroup`, source character offsets [5,7), word [2.88,3.87), `azure_word`, saved timing evidence ID; 59/99 raw and 49/99 retained frames. One contour spans both characters.
20. **No invented boundary:** anonymous [2.88,3.23)/[3.24,3.87) provider intervals are unused; no equal splitting or individual pitch assignment. Real timestamps/More detail remain unchanged.
21. **API/schema:** computed `PerceivedSyllable.observed_gesture` and `.observed_confidence`; typed `PerceivedAnalysisData.timing_groups`; group-aware Mine word-edge simplification; old-response enrichment from saved evidence only; generated OpenAPI/TS updated. Analyzer v5, no migration/dependency.
22. **Mobile:** new `toneGestureMatch`, whole-cell semantic treatment, tap semantics, grouped geometry and real-time word labels; shared Practice/Free Practice/Conversation path. No legacy grading UI restored.
23. **Proposed ObservedSpeechUnit:** stable ID/index, optional timing/provenance, acoustic pitch/confidence/quality, nullable segmental hypotheses/confidence/optional pinyin-like mapping, lexical links and immutable evidence refs. No character required; design only.
24. **Invariants:** observation independent of target/lexical mutation; multiple interpretations allowed; unresolved and nonsense units valid; acoustic pitch distinct from lexical tone; sound labels need independent provenance. Twelve precise rules are in the contract.
25. **Capabilities audited:** OpenAI saved transcription, Azure alignment/assessment/recognition payloads, local pitch/formant utilities, cached frozen wav2vec2, research heads, Transformers/torchaudio/module presence, CTC/pinyin/phone recognizer searches, forced alignment and posterior availability.
26. **Genuinely independent:** waveform F0/energy/spectrum and frozen audio encoder input are independent of text/target. Current crop boundaries remain lexically conditioned. Lexical ASR is target-independent but still lexical, not a sound-unit decoder.
27. **Unsuitable reference evidence:** Azure SAPI/reference phones and scores, forced-aligned phones, dictionary pinyin, target-scripted benchmark providers; none counts as observed sounds. No independent phone posterior head found.
28. **Optional probe:** skipped cleanly; cached wav2vec2-base is an encoder/pretraining checkpoint without a phone decoding head/tokenizer. No model downloaded or random head created.
29. **Runtime:** group transformation median .00345–.01200 ms per recording; allocated comparison generation <.001 ms locally. No additional acoustic/model/provider call. Device render time not measured.
30. **No-speech:** both exact historical silence hallucinations remain rejected; all 17 matching speech recordings accepted, 19/19 expected replay decisions. Guard code unchanged.
31. **Validation:** 492 API passed (4 optional skips, 5 known exclusions); 179 focused backend; 69 connected; 336 mobile native/web across 26 suites; 52 focused mobile. Ruff, 23-file formatting, 76-source API mypy, mobile lint/typecheck, web/Android exports, whitespace check pass.
32. **Known unrelated failures:** five previously stalled streaming cases remain excluded; optional PostgreSQL concurrency checks skipped; old React test warnings and unrelated formatting debt remain. No failure remains among executed final checks.
33. **DECISION 1 — TRUSTWORTHY ENOUGH FOR CONSERVATIVE CONNECTED-SPEECH PRODUCT USE.** Bounded acoustic semantics only, not validated lexical-tone accuracy or population performance.
34. **DECISION 2 — SHIP CONSERVATIVE MATCH/DIFFERENT/UNCERTAIN**, exposed as consistent/different/uncertain. Latest 苹 is an evidence-supported mismatch; no forced T3/neutral/州 grade.
35. **DECISION 3 — SHIP GROUPED WORD-LEVEL PITCH.** Preserves substantial measured 雨伞 evidence while admitting unavailable internal attribution.
36. **DECISION 4 — implement one research-only ObservedSpeechUnit adapter for cached unpooled waveform features**, with null segmental labels and no required lexical links; frame regions are not claimed phones/syllables.
37. **Manual smoke:** falling 苹→falling/different if reliable; rising 苹→rising/possibly consistent; target 广州/spoken 贵州→immutable identity with independent gestures; T3 sentence→safe character contours and grouped 雨伞; silence→existing retry/rejection. See the five-step packet below.
38. **Only recommended next development step afterward:** the single offline adapter in decision 4. No full phone recognizer, new model, training program or broad tracker research is proposed for this pass.

## Five-case manual smoke packet

1. Say **我要一个苹果。**, deliberately falling on 苹. Tap should show falling, reference T2/rising, different if evidence passes.
2. Repeat with a clear rising 苹. Tap should show rising and possible consistent state.
3. Set target **广州**, say **贵州** with changed pitch. Characters stay 贵州; references remain behind tap; gestures may differ or abstain. No transcript rewriting.
4. Say **我想买五把雨伞。** Character pitch appears where safely timed; word-only 雨伞 spans one region without an internal split or individual grade; T3 stays conservative.
5. Record **silence**. Existing no-speech rejection remains, with no successful graph or reply.

This packet has not been run on a physical device during this pass. No commit, push or deployment was performed. The final `git diff --stat` / `git status --short` output includes the earlier uncommitted work as well as this continuation.
