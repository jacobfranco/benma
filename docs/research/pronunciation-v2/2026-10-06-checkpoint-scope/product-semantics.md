# Product semantics, API contract and residual code

## Safe promise

Benma visualizes measured pitch aligned, where timing is available, to the text it perceived. It preserves missing evidence and suppresses gesture interpretation for incomplete, unstable or insufficient regions. Gesture descriptions are experimental; reference pronunciation is separate and learner comparison stays uncertain.

This does not establish full pronunciation correctness, reliable presence in every environment, independently observed sound/segment identity, detected lexical tones, a pronunciation score or correct target production. The primary units follow the exact perceived transcript and provider-attributed timing. Optional acoustic evidence cannot silently replace that text with an intended target or inferred conversational meaning.

## Wording and activation audit

The search covered mobile source (including reachable legacy routes, accessibility, history and advanced panels), API schemas, provider normalization, interpretation and response assembly. Test fixtures and raw provider field names were distinguished from rendered copy. `right` in layout coordinates, error text “Something went wrong”, pinyin correction actions and identity-mismatch exceptions are not grades.

| Path | Current visible/exposed wording | Condition and whether active today | Experimental gesture dependency | Can falsely accepted silence reach it? |
|---|---|---|---|---|
| Home → Practice | “See your measured pitch, or practice a target phrase.” | Signed-in home, active | No | Entry copy is unconditional |
| `SpeechEvidence` | “What Benma heard”; “Your pitch” in the graph | Successful nonempty perception; graph may load later | Measurements, not a gesture verdict | Yes; ASR may hallucinate text |
| `SentenceToneGraph` default and accessibility | Neutral cells; “tone gesture uncertain” | All cells, including grouped/untimed/synthetic | Helper never promotes the comparison | Yes; it remains uncertain |
| Character tap | “Observed pitch: …”, “Observed confidence: …”, “Tone gesture: uncertain” | Character timing, non-synthetic alignment and sufficient eligibility permit a description; otherwise unclear/low, “Incomplete evidence”, or “Pitch tracking: Uncertain” | Yes, explicitly experimental; semantic alias of gated backend classifier | Yes; silence can have sufficient local pitch |
| Character reference detail | “Lexical tone”, “Reference tone”, “Reference pronunciation. Pitch gestures are experimental; tone comparison remains uncertain.” | Resolved reading/context only; null/unresolved is preserved | No reference is detected acoustically | Yes if ASR text resolves; references still refer to perceived text |
| Word groups | “grouped word pitch”, no individual attribution/comparison | Valid word span without individual timing | No per-character gesture | Yes if timing exists |
| `SpeechEvidence` target delta | “Target difference: 广 → 贵” (example) | Target and heard text differ after punctuation/space normalization | No; textual comparison | Yes, false ASR can produce a textual difference |
| Conversation inferred wording | “What Benma understood”; “Benma heard … where context suggested …”; “Context suggested different wording” | `infer` plus actual text difference | No; contextual interpretation | Yes; presence has already accepted it |
| Conversation clarify | “Benma is unsure what you meant …” | Authoritative contextual `clarify` | No | Yes; clarify is not a reliable presence safeguard |
| Primary target assessment/score | No numeric pronunciation score or provider tone label rendered | Assessment may persist, but `SpeechEvidence` consumes only target metadata; old `PronunciationFeedback` is deleted | Not used | It may exist as evidence, not a learner score |
| Legacy `/pronunciation` default | “Experimental analysis”; “Reference Tone …”; “Tone comparison is unavailable. Reference pronunciation is not a grade.” | Signed-in direct route; not protected by `__DEV__`; reachable today | Does not render cached classifier/provider judgment | Yes, but ordinary feedback stays neutral |
| Legacy A/B | “No improvement percentage is calculated”; per-character “tone comparison unavailable” | Select two saved attempts | Does not render saved interpretation messages | Yes; even older saved strong wording is withheld |
| Legacy advanced | “Experimental diagnostics”; “Uncalibrated provider and historical interpretation data. These are not pronunciation grades.” | Explicit advanced expansion; old/raw values remain visible in labeled evidence rows | May contain historical experimental messages | Yes; treated as diagnostics, not endorsed current truth |
| Fresh API `interpretation.message` | “Uncalibrated provider tone label: T…”, or opt-in “Experimental provider tone label … reference surface tone … not a pronunciation grade”; descriptive acoustic-only fallback | Only a successful explicitly live assessment can contribute a provider label; optional legacy flag controls comparison; active diagnostics possible | Older independent direction helper, not V2 eligibility | Yes, API clients must respect experimental policy and provenance |
| Historical API interpretation/provider data | Old persisted messages, `detected_tone`, `pronunciation_score`, provider scores, agreement/mismatch keys | Owned laboratory/result/history/debug responses; stored data remains unchanged | Historical provider/classifier diagnostics | Yes; existing evidence is not a new grade or trust promotion |
| `learnerVerdict` | `matches`, `close`, `different`, `unclear` in helper return values | No runtime UI import/caller found; offline/acceptance tests retain it | Historical classifier policy | Cannot activate through current learner UI |
| Calibration route | “correct”, “wrong tone”, “wrong initial”, “wrong final”, “negative control” | Prompted production/category labels before recording; home link is development-only, route itself is signed-in | Human-requested task labels, not machine feedback | Recording can be mislabeled by a user, not automatically graded |
| API target/pinyin correction | User-corrected reference/reading | Explicit human input | No | Does not diagnose audio |

The former detected-tone label and arbitrary `interpretation.message` rendering in legacy default/A/B views were real exposure gaps found and fixed here. Advanced raw data and historical API payloads remain intentionally inspectable; old strings are not silently rewritten. The new interpreter version prevents fresh analyses from reusing old wording under an unchanged policy identity.

## Consistent/different policy

Checkpoint policy combines **A** (backend/schema architecture retained, neutral mobile presentation) with **C** (comparison always uncertain until a future explicit trust decision). No future gate is implemented or implicitly authorized. `toneGestureMatch` cannot return consistent/different today, including when fields are missing or a server sends an unfamiliar policy string. Style/type branches remain dormant, not feature toggles.

Backend `tone_comparison_policy = Literal["experimental"]`; sufficient acoustic eligibility alone has no authority to promote it. Existing `BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION` controls a different laboratory comparison path. Code and example default false; effective local `.env` explicitly true is preserved. Categorical judgment is disabled and unsupported. That local research override still cannot enable Tone Graph V2 grading or default/A/B legacy messages.

The API still stores provider scores and experimental agreement states. This is useful evidence architecture, not a calibrated endpoint contract. Default flags, explicit capability policy, new no-grade wording, neutral UI and the UI cache regression contain its presentation. A third-party client that ignores provenance would need its own review; this checkpoint does not certify arbitrary API consumers.

## API compatibility and scope

The OpenAPI diff adds **86 property declarations across 13 schemas**; nine are entirely new schemas. No schema or existing property is removed. Both checked-in generated files match the canonical exporter byte-for-byte. Computed observed fields are required/read-only in responses, with conservative computed defaults when old persisted data is parsed. Additions to pre-existing models otherwise have nullable/defaulted contracts and tolerate old data. No database migration is required.

Names distinguish original acoustic evidence, selected/display values, projection timing and eligibility from reference tones. `observed_gesture` is a semantic alias, not a new classifier or recognized lexical tone. `PerceivedTimingGroup` validates ordered positive duration and exact text-span length. Track nested models are frozen, reject extra fields and nonfinite values, and serialize tuples as arrays.

The generated TypeScript emitter currently widens JSON Schema `const` fields to `string` (for example the experimental policy and `azure_word` source). The wire schema enforces the const; the UI fails closed independently. This existing generator limitation is recorded, not treated as a future trusted flag or redesigned in this pass.

Deliberately exposed diagnostic fields are allowlisted tracker candidates, energy/periodicity, alternate-filter disagreement, exclusion reasons and completeness metrics. They explain evidence selection; they are not Silero probabilities, RMVPE activations or benchmark IDs. Raw provider timing responses remain internal to perceived-analysis persistence. The existing account-owned laboratory raw-provider API is still diagnostic. Tracker configuration contains acoustic parameters/provenance, not provider credentials; no new local storage path, model weight, raw audio bytes, provider secret or research-only inference field is added to the public schema.

Field classes below use: **FE** foundational evidence; **PP** projection provenance; **AE** acoustic eligibility; **OG** observed gesture; **RC** reference/comparison permission; **ED** experimental/debug. Diagnostic acoustic values can have FE context but are classified ED when their public purpose is inspection. R = required on that object; O = defaulted/optional; RO = computed response-only. The track/container itself remains optional on existing responses.

| Schema.property | Class | Presence |
|---|---|---|
| `AcousticRunResponse.utterance_pitch_track` | FE | O |
| `PerceivedAnalysisData.pitch_track_evidence_id` | PP | O |
| `PerceivedAnalysisData.timing_groups` | PP | O |
| `PerceivedAnalysisData.tone_graph` | FE | O |
| `PerceivedSyllable.observed_confidence` | OG | R / RO |
| `PerceivedSyllable.observed_gesture` | OG | R / RO |
| `PerceivedSyllable.pitch_eligibility` | AE | O |
| `PerceivedSyllable.pitch_projection` | PP | O |
| `PerceivedSyllable.tone_comparison_policy` | RC | O |
| `PerceivedTimingGroup.character_end` | PP | R |
| `PerceivedTimingGroup.character_start` | PP | R |
| `PerceivedTimingGroup.end_seconds` | PP | R |
| `PerceivedTimingGroup.pitch_eligibility` | AE | O |
| `PerceivedTimingGroup.pitch_projection` | PP | O |
| `PerceivedTimingGroup.source` | PP | O |
| `PerceivedTimingGroup.start_seconds` | PP | R |
| `PerceivedTimingGroup.text` | PP | R |
| `PerceivedTimingGroup.timing_evidence_id` | PP | R |
| `PitchCandidate.frequency_hz` | ED | R |
| `PitchCandidate.strength` | ED | R |
| `PitchInterpretationEligibility.metrics` | AE | O |
| `PitchInterpretationEligibility.reasons` | AE | O |
| `PitchInterpretationEligibility.state` | AE | O |
| `PitchInterpretationEligibility.version` | AE | O |
| `PitchRegionProjection.end_seconds` | PP | O |
| `PitchRegionProjection.frame_indices` | PP | O |
| `PitchRegionProjection.start_seconds` | PP | O |
| `PitchRegionProjection.timing_evidence_id` | PP | O |
| `PitchRegionProjection.timing_source` | PP | O |
| `PitchRegionProjection.track_evidence_id` | PP | R |
| `PitchSupportMetrics.discontinuities` | AE | O |
| `PitchSupportMetrics.early_retained_fraction` | AE | O |
| `PitchSupportMetrics.largest_island_seconds` | AE | O |
| `PitchSupportMetrics.largest_raw_gap_seconds` | AE | O |
| `PitchSupportMetrics.largest_selected_gap_seconds` | AE | O |
| `PitchSupportMetrics.late_retained_fraction` | AE | O |
| `PitchSupportMetrics.maximum_raw_jump_semitones` | AE | O |
| `PitchSupportMetrics.middle_retained_fraction` | AE | O |
| `PitchSupportMetrics.missing_head_seconds` | AE | O |
| `PitchSupportMetrics.missing_tail_seconds` | AE | O |
| `PitchSupportMetrics.raw_end_seconds` | AE | O |
| `PitchSupportMetrics.raw_start_seconds` | AE | O |
| `PitchSupportMetrics.raw_voiced_frames` | AE | O |
| `PitchSupportMetrics.retained_fraction` | AE | O |
| `PitchSupportMetrics.selected_end_seconds` | AE | O |
| `PitchSupportMetrics.selected_frames` | AE | O |
| `PitchSupportMetrics.selected_islands` | AE | O |
| `PitchSupportMetrics.selected_start_seconds` | AE | O |
| `PronunciationSyllableResult.pitch_eligibility` | AE | O |
| `PronunciationSyllableResult.pitch_projection` | PP | O |
| `PronunciationSyllableResult.tone_comparison_policy` | RC | O |
| `SentencePitchEvidence.filtered` | FE | R |
| `SentencePitchEvidence.mine` | FE | R |
| `SentencePitchEvidence.raw` | FE | R |
| `SentencePitchEvidence.track_evidence_id` | PP | O |
| `TrackerPitchFrame.exclusion_reasons` | ED | O |
| `TrackerPitchFrame.f0_hz` | FE | O |
| `TrackerPitchFrame.retained` | FE | R |
| `TrackerPitchFrame.selected_f0_hz` | FE | O |
| `TrackerPitchFrame.source_frame_index` | PP | O |
| `TrackerPitchFrame.timestamp_seconds` | FE | R |
| `TrackerPitchFrame.tracker_f0_hz` | FE | O |
| `UtterancePitchFrame.analyzer_selected_f0_hz` | FE | O |
| `UtterancePitchFrame.candidates` | ED | O |
| `UtterancePitchFrame.comparison_f0_hz` | ED | O |
| `UtterancePitchFrame.display_semitones` | FE | O |
| `UtterancePitchFrame.energy_gated_f0_hz` | FE | O |
| `UtterancePitchFrame.energy_rms` | ED | O |
| `UtterancePitchFrame.exclusion_reasons` | ED | O |
| `UtterancePitchFrame.filter_disagreement_st` | ED | O |
| `UtterancePitchFrame.periodicity` | ED | O |
| `UtterancePitchFrame.raw_f0_hz` | FE | O |
| `UtterancePitchFrame.selected_f0_hz` | FE | O |
| `UtterancePitchFrame.timestamp_seconds` | FE | R |
| `UtterancePitchTrack.audio_sha256` | FE | R |
| `UtterancePitchTrack.baseline_hz` | FE | O |
| `UtterancePitchTrack.duration_seconds` | FE | R |
| `UtterancePitchTrack.evidence_id` | FE | R |
| `UtterancePitchTrack.frame_cadence_seconds` | FE | O |
| `UtterancePitchTrack.frames` | FE | R |
| `UtterancePitchTrack.raw_provenance` | FE | R |
| `UtterancePitchTrack.schema_version` | FE | O |
| `UtterancePitchTrack.selection_version` | FE | R |
| `UtterancePitchTrack.tracker_configuration_json` | FE | R |
| `UtterancePitchTrack.tracker_source` | FE | R |
| `UtterancePitchTrack.tracker_version` | FE | R |

## Dead/duplicated code assessment

- Deleted `PronunciationFeedback.tsx` is superseded by `SentenceToneGraph`; no surviving runtime import was found. Preserve the existing deletion in the checkpoint.
- `SyllableComparison.tsx` now contains historical helpers, with `learnerGestureContour`, `normalizedDisplayContour` and `learnerVerdict` exercised by offline/acceptance tests. They are not imported by the active V2 graph. Do not delete the research regression surface just because it is dormant.
- `toneGestureMatch` retains a union/style vocabulary for consistent/different but no live branch returning those values. No duplicate acoustic quality/classification logic runs on the active mobile path.
- Backend `classify_contour` remains the experimental gesture classifier; the legacy interpreter's simpler `_acoustic_direction` is a separate diagnostic calculation, not a second trusted V2 verdict. Its provider-label path does not use the new completeness gate, so it stays out of ordinary mobile feedback and behind the existing opt-in comparison flag.
- Historical `ObservedContour.classification` values (`1-like` etc.), `expected_tone`/surface-shape fields, provider `detected_tone` and provider scores remain compatibility/evidence fields. They are not stale enough to remove safely: tests, historical payloads and laboratory diagnostics still use them.
- The research dataclass named `UtterancePitchTrack` in `f0_foundation.py` is distinct from the production frozen Pydantic contract in `pitch_types.py`. No production module imports the research implementation. Preserve the reproducible experiment rather than merge the types during a checkpoint.
- Old development text claimed positive/warning states and universal silence rejection. The current development summary replaces those claims and supersedes historical next-experiment recommendations; original research reports retain their context.

No aggressive refactor or additional dead-code deletion was performed. The checkpoint fixes evidence presentation and defaults; it does not claim that every legacy diagnostic is calibrated or that local acoustic sufficiency grants learner permission.
