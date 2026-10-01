# Truth boundaries

## Research contract

1. **Perception:** `run_live` accepts audio/settings/alignment opt-in, no intended text. It calls the production `UnknownTargetPerceptionInput` port. `Perception` preserves exact raw/normalized text (identity normalization), raw provider JSON, uncertainty and request policy. The digest and record validator require exact agreement with the perceived alignment reference. Target comparison occurs after region/evidence construction.
2. **Perceived alignment:** Azure `ReferenceText` is the exact unknown-target transcript. The raw Azure response stays under `alignment.raw_response`; its text/scores are not merged into perception. Complete native exact-offset timing avoids a separate Azure request. Word spans survive even if subdivision fails. Unsupported/malformed mappings produce missing boundaries and issue codes.
3. **Observed evidence:** production Praat sees only audio. Raw tracker F0, energy-gated F0, selected F0, periodicity proxy, candidates, missingness and rejection reasons remain separate. Phones are explicitly labeled `reference_label_not_observed_phone`. No reference tone digit becomes an observed tone. No five-bin/classical tone classifier or learned classifier is invoked by the harness.
4. **Expected pronunciation:** `compare_text` alone sees intent. It uses deterministic text edit distance and existing exact-text reading/surface functions. Intended reading, lexical tone and contextual category live only in `TextEdit.expectation`. The perceived reading is itself a dictionary/contextual reading of recognizer text, **not a phone transcription**.
5. **Judgment:** every unit currently returns `INSUFFICIENT EVIDENCE`, with interpretable reasons. An ASR substitution, a provider accuracy score, or a dictionary label cannot by itself establish the physical cause of a mismatch.

Records are snapshots: perception payloads are copied, typed models reject field reassignment, and the CLI refuses an existing output directory. This is append-by-new-run application behavior, not tamper-proof storage; nested raw JSON remains ordinary JSON and hashes cannot prevent deliberate file edits. Consumers must validate records on read. Intent may differ across runs without changing perception, alignment or observed evidence for the same input evidence.

## Existing production boundaries that are clean

- `UnknownTargetPerceptionInput` has no target/history/correction fields. `openai_form_fields` uses a fixed nonsemantic Mandarin policy. Provider request/response provenance is retained by `PerceptionService`.
- User corrections and semantic interpretations are separate resources. Conversation's reconstructed meaning is allowed into assistant generation/history, not ASR or the perceived alignment reference.
- `PerceivedSpeechAnalysisService` explicitly reads persisted `perception.transcript`, never the conversation's inferred wording.
- Acoustic analyzer and `classify_contour` do not receive expected tone. Display filtering preserves measured evidence and does not redraw it to fit a target.
- Target assessment/alignment runs preserve target snapshots and are different DB types from perception/perceived analysis.

## Existing conflations and gaps (documented, not changed)

| Location | Observed behavior | Consequence |
| --- | --- | --- |
| mobile `speech/workflow.ts::submitSpeech` | Practice starts target analysis and unknown-target ASR, but shares a single analysis promise; no perceived-reference analysis branch when target exists | Practice does not yet satisfy the requested dual-trace diagnostic contract, despite preserving ASR text |
| `speech/providers/azure.py::AzurePronunciationProvider.assess` | appends each `Words[]` entry to normalized `AssessmentEvidence.syllables` | field name can conceal multi-character words; count is not syllable count |
| `pronunciation/laboratory.py::result`, `interpretation.py::interpret_evidence` | provider `syllables[index]` attached/considered alongside target pinyin by index | multi-character tokens/miscues can mismatch target-unit indexing, even though separate contour timing has identity gates |
| `pronunciation/targets.py::parse_mandarin_target` | uses `group[0]` while retaining alternatives; punctuation/non-Han token-to-character assumptions | Practice reading resolution is less conservative than perceived `resolve_run`; ambiguity can look resolved |
| `pronunciation/interpretation.py::interpret_evidence` | if no complete expected-surface list exists, falls back to `target.lexical_tones` | unresolved contextual surface pronunciation can revert to dictionary expectation in derived observations |
| mobile `speech/learnerVerdict.ts`, `SyllableComparison.tsx` | target + acoustic shape category can produce “Good”/“Yours sounded more like Tone …” | stronger learner-facing judgment than a measured shape alone establishes; categorical backend setting does not disable this client comparison |
| `pronunciation/perceived.py::perceived_syllables` | constructs dictionary/surface patterns inside the perceived analysis object | fields are expectation about text, not evidence of actual phonetic production; downstream consumers must retain that distinction |
| `pronunciation/alignment.py::ReplayAligner` | equal-duration partitions labeled synthetic | suitable for UI fixtures only; research CLI never invokes it |
| `pronunciation/azure_alignment.py` | intentionally whitelists timing and discards scoring/text fields from normalized timing output | good separation, but production alignment response alone cannot support phone-error explanations; harness separately preserves original raw JSON |

No observed code path supplies the intended transcript to unknown-target OpenAI recognition. That does not imply ASR is unbiased: language-model priors and recognition errors remain possible. The evidence claim is “what this recognizer returned,” not “what the learner objectively said.”

## Critical fixture

[Input](../../../../benchmark/pronunciation_v2/fixtures/connected-guizhou.json) explicitly simulates perception `我要去贵州`. Invoke with target `我要去广州`.

```json
{
  "perception": {
    "raw_transcript": "我要去贵州",
    "normalized_transcript": "我要去贵州"
  },
  "intended_text": "我要去广州",
  "alignment": {"reference_text": "我要去贵州"},
  "text_comparison": [{
    "operation": "substitution",
    "intended": "广",
    "perceived": "贵",
    "diagnosis": "not_inferred_from_text"
  }]
}
```

This is an excerpt; the [complete generated record](example-guizhou/record.json) has the full edit sequence. Its synthetic whole-word span does **not** create five syllable intervals. The [report](example-guizhou/report.md) prints `我要去贵州` unchanged and marks those units untimed/insufficient. This tests structural isolation, not recognizer performance.
