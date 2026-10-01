# Gaps and next pass

## What this vertical slice establishes

Audio canonicalization, unknown-target provider transport, exact-text reading resolution, conservative Azure mapping, whole-utterance Praat extraction, typed evidence separation, deterministic target edit comparison, and JSON/Markdown reporting are reusable now. Valid single-character/native or full-pinyin mapped regions can carry pitch slices and reference phone labels. Multicharacter word-only spans remain useful word evidence with unresolved syllable timing.

What it does **not** establish: sentence-tone accuracy, native listener perception, gold syllable boundaries, phone identities actually produced, the cause of a text substitution, calibrated reliability of a tone classifier, or the correctness of every target/surface reading. No learner recording or live provider response was collected in this pass. Structural fixtures and generated signals cannot answer those questions.

## Largest blocker

**Reliable, auditable perceived-syllable localization on real sentence speech.** The default ASR adapter supplies no usable timing. The existing Azure adapter can conditionally map SAPI labels to exact perceived characters, but that is reference-conditioned alignment, with no calibrated timing confidence and no guarantee for coarticulation, rapid speech, misrecognition, polyphones, erhua, omitted words or multi-character tokens lacking suitable phones. A synthetic mapping test proves the rule works on its inputs; it does not validate those provider inputs acoustically.

This is the immediate bottleneck in the trace, not proof a new forced aligner is necessary. The repository already has an optional MFA wrapper; the harness does not invoke it or introduce another aligner. First measure actual Azure/native coverage and boundary quality. If mapping fails frequently, preserve failures and propose a separately scoped alignment comparison, with explicit provenance and independently checked boundaries.

## Contextual expectation: current support and limits

| Phenomenon | Existing implementation | Missing / correct architectural layer |
| --- | --- | --- |
| Third-tone sandhi | `surface_expectations`: adjacent pair in a reviewed word set or a whole two-character clause → 2,3 | broader word/prosodic grouping; chains of ≥3 return unresolved. Belongs in expected contextual pronunciation |
| Half-third / connected T3 | lexical/final category remains 3; drawing uses a lexical dip/recovery template | no explicit half-third surface representation conditioned on prosody/following tone; a T3 category does not demand a full dip. Expected layer must describe allowed realizations; measurement stays untouched |
| 不 | citation restored to bu4; before a contiguous lexical T4 → T2 | A不A marked unresolved; other grammatical neutralization/phrase boundaries incomplete. Expected layer |
| 一 | citation restored yi1; quantity follower + next lexical tone → T2 before T4, T4 before T1/2/3; ordinals/numerals/final cases retain T1 | follower allowlist is limited; reduplication and other syntax unresolved. Expected layer |
| Neutral tone | 0 retained; no fixed context-free graph; reviewed 妈妈 supplement, dictionary neutral words, grammar for 们 and clause-final 吧 | broad lexical coverage, context-dependent F0/duration, stress/reduplication, optional neutralization and variety differences. Reading + expected layer |
| Polyphonic characters | perceived reader uses longest phrase matching, small supplement, grammatical rules, dominant readings and explicit ambiguity; exact pronunciation tokens may ground a choice | remaining readings must abstain; segmentation/lexicon limitations; Practice parser's first-choice behavior differs. Reading layer |
| Word boundaries | longest phrase matches support some reading decisions | no general retained prosodic word segmentation or acoustic boundaries inferred from that segmentation. Expected context ≠ alignment |

The new harness reuses the conservative perceived reader even for the intended expectation; it does not add speculative phonology rules. Lexical tone and expected surface category remain separate. A future improvement should remove silent lexical fallback in unresolved production judgment, but that would be a separate reviewed behavior change.

## Segmental evidence

Azure alignment labels describe the reference pronunciation. A score estimates fit to that reference; it is not an independently recognized sound. Multicharacter words cannot safely be distributed across intended indices by list order. Mandarin independent phone alternatives, validated consonant/vowel confusion evidence, acoustic phone-to-syllable mapping under substitutions, and source reconciliation remain missing. ASR alternatives/logprobs do not fill that gap. Keep any future target-relative assessment in a separate layer; never promote its forced text to what was heard.

## Frozen learned model

Not wired into v1. `benchmark/pronunciation_v2/features.py::encode_waveforms` accepts waveforms and extracts frozen wav2vec hidden representations; `model_probe.py::predict_head` applies the persisted scaler/linear parameters to feature vectors. A sufficiently long mono 16 kHz crop is mechanically consumable. Very short crops need explicit minimum-length behavior, and feature/checkpoint/layer/head provenance must match the locked research artifacts.

These helpers are embedded in an isolated-clip research workflow, not a production crop-inference port. The harness would need a small read-only adapter, checkpoint/head verification, deterministic crop/context policy and a clear out-of-domain contract. That is additional scope with no established connected-speech validity. The user-reported ~52.9% fresh-panel isolated result supplies no sentence-crop accuracy estimate. No historical experiment was rerun or reinterpreted. A future adapter must preserve every probability, label every inference experimental/out-of-domain, never use expected-tone thresholds, and never discard a region because its prediction looks wrong.

## Exact next pass after recordings arrive

1. Use the [study packet](manual-sentence-study.md) IDs. Retain originals outside tracked paths; preserve device/rate/session, intended sentence and separately declared manipulation. Do not annotate natural attempts with imagined gold tones.
2. Run each waveform once through frozen unknown-target perception and perceived-reference Azure timing + production Praat. Save raw responses/configuration and hashes. Run the same saved evidence with and without intended text and compare perception/alignment/acoustics for identity.
3. Make a per-recording coverage table: recognized text, token lengths, valid/unresolved syllable regions, mapping rejection reasons, transcript/timing conflict, F0 missing/usable counts, reading ambiguity and target edits. Keep all failures, not only attractive contours.
4. Listen to sentence and short contextual windows; inspect provider spans against waveform/pitch. Note obvious truncations, overlapping/wrong spans, recognizer substitutions and whether each known manipulation remains visible. Listening is an audit, not native tone labeling.
5. Select a small disputed-boundary/segment subset for independent native/phonetic review if needed. Keep annotator identity/uncertainty and label provenance separate. Do not calculate pronunciation accuracy from learner self-assessment.
6. Decide the next engineering change from observed failures: strengthen perceived timing/mapping and Practice's dual trace first if coverage is weak. If regions are dependable, scope independent segmental evidence and a read-only, explicitly out-of-domain frozen-head probe. No architecture tuning until sentence evidence and evaluation labels justify it.

Deliverable for that pass: a recording-by-recording evidence audit, coverage/failure counts and a bounded next change. Not a model ranking or a product correctness score.
