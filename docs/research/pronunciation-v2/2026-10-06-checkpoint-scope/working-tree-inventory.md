# Complete working-tree inventory and artifact audit

The initial audit enumerated **268 modified/deleted/untracked files**, expanding Git's collapsed research directories. It found **15,288,312 bytes** of existing candidate file content. Of those, **25 generated/local files (8,105,520 bytes)** are now explicitly ignored and excluded, leaving **243 original candidate paths**. This pass adds 15 paths to the review boundary: eight previously unchanged tracked files, one mobile regression file and these six report files. No pre-existing work or user data was deleted; the pre-existing component deletion is retained.

The final file-by-file boundary is **258 KEEP paths + 25 EXCLUDE paths = 283 reviewed paths**. The KEEP list includes tracked modifications, untracked additions, the existing deletion and this inventory itself. Its final byte size changes slightly as documentation is completed; file membership is the authority. No unexplained J/unclear category remains.

The Git index is empty (`git diff --cached --stat` has no entries). No files have been staged by this pass. `git status --short` omits ignored outputs; they are still enumerated in the EXCLUDE table below so no originally untracked artifact disappears from the audit.

## Category definitions and totals

| Category | Meaning | Final KEEP paths | Excluded reviewed paths |
|---|---|---:|---:|
| A | Production core / checked-in configuration | 24 | 0 |
| B | Production tests (backend and mobile, including numeric fixtures) | 24 | 0 |
| C | Mobile product | 13 | 0 |
| D | Generated API/client | 2 | 0 |
| E | Reproducible research tooling / retention rules | 21 | 0 |
| F | Documentation and retained numeric research evidence | 174 | 0 |
| G | Generated/transient | 0 | 25 |
| H | Private/raw user evidence and private configuration | 0 | Already ignored storage, below |
| I | Model weights/cache | 0 | Already ignored storage, below |

Only one category is assigned per reviewed file. `.gitignore` is E because its change defines research-output retention. READMEs are F even when located under a product directory. Mobile tests are B, not C. Raw diagnostic provider field names in a schema/test do not turn source code into private evidence.

## KEEP IN COMMIT — exact staging allowlist

This table is the proposed path boundary, **not authorization to stage**. `M` means tracked modification, `D` the existing tracked deletion, and `??` a new file. Every benchmark/research candidate has an explicit KEEP/EXCLUDE decision; F includes numeric evidence only where it documents a frozen result or enables reproducibility.

| Path | Status | Category | Decision |
|---|---|---|---|
| `.gitignore` | M | E | KEEP IN COMMIT |
| `apps/mobile/README.md` | M | F | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/freeTalkScreen.test.ts` | M | B | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/freeTalkWorkflow.test.ts` | M | B | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/perceivedFixture.ts` | M | B | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/practiceScreen.test.ts` | M | B | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/pronunciationSafety.test.ts` | ?? | B | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/sentenceToneGraph.test.ts` | ?? | B | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/sentenceToneGraph.web.test.ts` | ?? | B | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/toneGestureMatch.test.ts` | ?? | B | KEEP IN COMMIT |
| `apps/mobile/src/__tests__/transcriptFeedback.test.ts` | M | B | KEEP IN COMMIT |
| `apps/mobile/src/api/openapi.generated.ts` | M | D | KEEP IN COMMIT |
| `apps/mobile/src/api/openapi.json` | M | D | KEEP IN COMMIT |
| `apps/mobile/src/app/index.tsx` | M | C | KEEP IN COMMIT |
| `apps/mobile/src/app/practice.tsx` | M | C | KEEP IN COMMIT |
| `apps/mobile/src/app/pronunciation.tsx` | M | C | KEEP IN COMMIT |
| `apps/mobile/src/components/PitchPlot.tsx` | M | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/PronunciationFeedback.tsx` | D | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/SentenceToneGraph.tsx` | ?? | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/SpeechEvidence.tsx` | M | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/SyllableComparison.tsx` | M | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/TranscriptFeedback.tsx` | M | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/sentenceToneGraph.ts` | ?? | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/toneGestureMatch.ts` | ?? | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/useSpeechTurn.ts` | M | C | KEEP IN COMMIT |
| `apps/mobile/src/speech/workflow.ts` | M | C | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_acoustic_windows.json` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_browser_check.cjs` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_report.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_rmvpe.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_rmvpe_audit.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_rmvpe_run.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_run.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_verify.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_viewer.html` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/f0_foundation_viewer.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/silero_vad_audit.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/silero_vad_latency.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/silero_vad_report.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/speech_presence_audit.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/test_f0_foundation.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/test_f0_foundation_rmvpe.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/test_silero_vad_artifacts.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/test_silero_vad_audit.py` | ?? | E | KEEP IN COMMIT |
| `benchmark/pronunciation_v2/utterance_evidence_replay.py` | ?? | E | KEEP IN COMMIT |
| `docs/development/tone-graph-v2.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-02-pitch-reliability/README.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-02-pitch-reliability/method.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-02-pitch-reliability/results.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-02-pitch-reliability/trust-pass.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-02-pitch-reliability/validation.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-native-control-calibration/README.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-native-control-calibration/capture-robustness-repeatability.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-native-control-calibration/capture-robustness-replay.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-native-control-calibration/capture-robustness-syllables.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-native-control-calibration/capture-robustness.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-native-control-calibration/comparison.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-native-control-calibration/forensics.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-native-control-calibration/per-character-forensics.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-prelexical-speech/README.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-prelexical-speech/capability-inventory.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-prelexical-speech/current-vs-target-architecture.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-prelexical-speech/observed-gesture-audit.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-prelexical-speech/prelexical-contract.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-03-prelexical-speech/validation.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/README.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/acoustic-support.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/aggregate.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/architecture.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/artifact-verification.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/benchmark-corpus.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/blinded-review.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/corpus.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/decision.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/diagnostic-windows.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/five-tracker-decision.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/low-f0-and-silence.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/low-f0-proxy.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/low-f0-under70.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/model-download-receipt.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/pairwise-repeatability.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/per-recording-metrics.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/raw-results.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/raw-tables.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/repeatability-tables.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/repeatability.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/research-environment.txt` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe-artifact-verification.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe-blind-review-before-reveal.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe-blind-review-receipt.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe-download-receipt.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe-per-file-runtime.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe-predeclared-config.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe-threshold-summary.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe-threshold-sweep.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/rmvpe.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/runtime.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/runtime.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/safety-tables.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/source-perturbations.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/synthetic-results.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/synthetic-tables.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/tracker-inventory.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/validation.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/verification-crepe_full.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/verification-harvest.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/verification-praat_ac.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/verification-praat_cc.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/verification-pyin.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/verification-rmvpe.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/README.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/comparison-latency.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/current-flow.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/eligibility.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/extraction-latency.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/latency.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/low-f0-replay.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/negative-window-stress.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/presence-replay.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/preservation.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/processing-timings.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/projection-model.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/replay.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/retention-summary.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/utterance-pitch-track.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/validation.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-checkpoint-scope/README.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-checkpoint-scope/commit-plan.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-checkpoint-scope/presence-blast-radius.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-checkpoint-scope/product-semantics.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-checkpoint-scope/validation.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-checkpoint-scope/working-tree-inventory.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/README.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/accidental-analysis.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/accidental-overlays.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/accidental-silence.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/artifact-sha256.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/baseline-replay.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/corpus-results.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/corpus-results.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/corpus.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/decision.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/default-results.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/environment.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/hash-verification.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/inference-verification.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/latency.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/latency.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/model-provenance.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/model.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/preservation.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/02927481.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/0f4107fe.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/1a927887.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/209ef0c7.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/277e9941.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/27ea3b92.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/370aa8f4.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/484e80c0.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/5b995fff.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/5ca771a7.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/6f56aef1.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/7787300e.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/87ac7dd1.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/90aa0d8d.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/9b1d959a.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/a0270cee.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/c5188fc3.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/c95673d3.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/dccf8a63.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/e0c56934.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/e59a6350.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/f3c642b5.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/f47fadb3.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/f5dc0cc1.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/google_old.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/human_control.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/low_f0_excerpt.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/low_f0_excerpt_2.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/native_16k.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/native_bandlimit.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/native_gain.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/neg_clicks.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/neg_digital_silence.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/neg_stationary_noise.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/padding_human_head.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/padding_human_tail.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/padding_low_voice.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/padding_phone.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/short_human_a.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/short_human_b.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/short_human_c.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/short_native.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/silence_accidental.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/silence_original.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/silence_periodic.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/take_1.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/take_2.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/probabilities/take_3.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/protected-files-sha256.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/threshold-results.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/thresholds.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/validation.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/README.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/asr-audit.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/audit-version.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/candidates.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/corpus.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/decision.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/failure-forensics.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/feature-comparison.csv` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/feature-comparison.md` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/latency.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/measurements.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/preservation.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/saved-alignment-audit.json` | ?? | F | KEEP IN COMMIT |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/validation.md` | ?? | F | KEEP IN COMMIT |
| `services/api/.env.example` | M | A | KEEP IN COMMIT |
| `services/api/README.md` | M | F | KEEP IN COMMIT |
| `services/api/src/benma_api/api/routes.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/audio/presence.py` | ?? | A | KEEP IN COMMIT |
| `services/api/src/benma_api/audio/presence_service.py` | ?? | A | KEEP IN COMMIT |
| `services/api/src/benma_api/audio/service.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/config.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/conversation/service.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/errors.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/perception/service.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/acoustics.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/alignment.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/azure_alignment.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/capabilities.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/contours.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/interpretation.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/laboratory.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/perceived.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/pitch_evidence.py` | ?? | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/pitch_types.py` | ?? | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/readings.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/service.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/surface.py` | M | A | KEEP IN COMMIT |
| `services/api/src/benma_api/pronunciation/tone_graph.py` | ?? | A | KEEP IN COMMIT |
| `services/api/src/benma_api/schemas.py` | M | A | KEEP IN COMMIT |
| `services/api/tests/conftest.py` | M | B | KEEP IN COMMIT |
| `services/api/tests/fixtures/utterance_pitch_evidence.json` | ?? | B | KEEP IN COMMIT |
| `services/api/tests/test_final_acoustic_calibration.py` | M | B | KEEP IN COMMIT |
| `services/api/tests/test_live_pronunciation.py` | M | B | KEEP IN COMMIT |
| `services/api/tests/test_observed_gesture_groups.py` | ?? | B | KEEP IN COMMIT |
| `services/api/tests/test_perceived_postgres.py` | M | B | KEEP IN COMMIT |
| `services/api/tests/test_perceived_speech.py` | M | B | KEEP IN COMMIT |
| `services/api/tests/test_perception_truth.py` | M | B | KEEP IN COMMIT |
| `services/api/tests/test_presence_regression_corpus.py` | ?? | B | KEEP IN COMMIT |
| `services/api/tests/test_pronunciation_corrections_ownership.py` | M | B | KEEP IN COMMIT |
| `services/api/tests/test_pronunciation_laboratory.py` | M | B | KEEP IN COMMIT |
| `services/api/tests/test_quantity_reference.py` | ?? | B | KEEP IN COMMIT |
| `services/api/tests/test_sentence_tone_graph.py` | ?? | B | KEEP IN COMMIT |
| `services/api/tests/test_speech_presence.py` | ?? | B | KEEP IN COMMIT |
| `services/api/tests/test_utterance_pitch.py` | ?? | B | KEEP IN COMMIT |

## EXCLUDE AS GENERATED/LOCAL — all 25 initially visible outputs

All these files still exist and are now matched by exact report-specific `.gitignore` entries. PNGs are generated acoustic plots/spectra, not source assets. They are excluded regardless of size. The generated Silero viewer is reproducible; the similarly named HTML under `benchmark/` is a source template and is intentionally kept.

| Path | Category | Reason | Decision |
|---|---|---|---|
| `docs/research/pronunciation-v2/2026-10-05-f0-foundation/archive-verification.json` | G | Local temporary-archive receipt | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-05-utterance-evidence/git-state.txt` | G | Transient Git snapshot | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/figures/7787300e.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/figures/human_control.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/figures/low_f0_excerpt_2.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/figures/native_gain.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/figures/short_human_b.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/figures/short_native.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/figures/silence_accidental.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/figures/silence_periodic.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/git-state.txt` | G | Transient Git snapshot | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/validation-output.txt` | G | Historical execution log | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-silero-vad/viewer.html` | G | Generated HTML presentation | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/c95673d3-spectrum.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/c95673d3-waveform.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/human_control-spectrum.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/human_control-waveform.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/silence_accidental-spectrum.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/silence_accidental-waveform.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/silence_periodic-spectrum.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/silence_periodic-waveform.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/take_1-spectrum.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/figures/take_1-waveform.png` | G | Generated presentation figure | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/git-state.txt` | G | Transient Git snapshot | EXCLUDE AS GENERATED/LOCAL |
| `docs/research/pronunciation-v2/2026-10-06-speech-presence/validation-output.txt` | G | Historical execution log | EXCLUDE AS GENERATED/LOCAL |

## Private, secret and large-artifact audit

The audit read every candidate text file and checked binary signatures/extensions, file sizes, high-confidence key/private-key patterns, credential assignments, account/contact field names, embedded waveform/audio indications and local absolute paths. It did not read or print secrets from ignored environment files. A final allowlist audit repeats the candidate checks after report completion; `.env` is explicitly absent from the allowlist and Git index.

Findings:

- **No raw audio, model weights or private binary evidence is included.** The initial 18 candidate binaries were all generated PNG plots and are excluded. The final KEEP boundary contains text only. No RIFF/WAVE, audio data URI, embedded recording, executable/model binary or large opaque generated blob is staged/proposed.
- **No non-placeholder secret detected.** High-confidence key/private-key patterns, credential-valued assignments and contact scans found no live secret in the reviewed candidate set. Existing source/examples contain the repository's documented local development DB credentials; tests use synthetic phone/account/token fixtures. These are not exported private `.env` values. “RIFF” in a test is a WAV signature assertion, not embedded audio.
- **Pseudonymous provenance remains intentionally present.** Research metadata uses recording/perception IDs, audio hashes, relative private asset paths and fixed test-phrase transcripts. Those are required to associate fixed evidence; they are not anonymized public datasets, and the checkpoint must not be described as permission to publish the private corpus. No contact/credential value or raw recording accompanies them.
- **Absolute paths were reviewed.** Source references to `/tmp/benma-f0-bakeoff` and other temporary roots are historical research defaults, not production paths. Older Markdown commands mention the original workspace path for reproducibility; they are non-runtime historical provenance. The generated absolute archive-location receipt is excluded. No new user-home path is introduced into production runtime or the API. Historical reports are not rewritten to fabricate portability; private-input and environment requirements are explicit.
- **Large retained text is deliberate.** `services/api/tests/fixtures/utterance_pitch_evidence.json` (1,201,963 bytes) is sanitized numeric acoustic regression evidence. The utterance-evidence `replay.json` (1,667,508 bytes) preserves fixed per-region results. Both were examined as structured JSON, contain no waveform bytes/credentials and remain useful. Remaining saved tables/probabilities/receipts permit cross-checking decisions without model inference. No blanket retention of generated presentations is proposed.
- **Local configuration is excluded.** `services/api/.env` is ignored by `.gitignore`'s `.env` rule; mobile `.env` is also ignored. The local `BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION=true` is an explicit diagnostic research override, not committed default configuration. Code and `.env.example` use false; graph comparison is uncertain regardless.

This is a scoped source/artifact inspection and pattern scan, not a claim that automated scanning proves absence of every imaginable identifier. The allowlist and no-force-add boundary are the commit control.

## Already ignored H/I/G storage — must remain out

| Storage | Category | Evidence and exclusion |
|---|---|---|
| `services/api/var/` audio, captured provider evidence and local inventories | H | Initially 240 WAV, 33 WebM and 81 M4A files among its contents; private. Whole directory ignored. No data deleted. |
| `benchmark/corpus/recordings/original/`, `canonical/`; `benchmark/corpus/provider-captures/` | H | Original/canonical recordings and provider captures remain ignored (tracked `.gitkeep` exceptions are unchanged). The recordings tree initially contained 920 WAV files; none enters this boundary. |
| `services/api/.env`, `apps/mobile/.env`, any local root `.env` | H | Private configuration/credentials; ignored, not tracked or staged. Only `.env.example` belongs in the checkpoint. |
| `services/api/var/` model/runtime/activation directories | I | Initial scan includes 9 ONNX files, 1 PT and 2 PTH plus 103 NPZ and 6 NPY; this is inventory, not a model download/evaluation. All remain ignored. |
| `benchmark/pronunciation_v2/.venv/`, other `.venv/`, `node_modules/` and caches | I | Existing environments/downloaded packages remain excluded; research dependencies are not promoted to runtime dependencies. |
| `/tmp/benma-checkpoint/`, `services/api/var/checkpoint-scope/`, Expo dist/cache outputs | G | Validation logs, temporary audit scripts/manifests and export builds, never commit inputs. `/tmp` from the earlier execution environment was not retained; results already recorded in validation are not rerun to recreate logs. |

The two production presence source files also match the frozen pre-checkpoint SHA-256 receipt in the Silero report. No threshold or algorithm changed. No provider call, new capture, model download, destructive Git operation, staging, commit, push or deployment occurred.

## Retention rationale

Retain benchmark scripts/tests, frozen acoustic windows, numeric corpus/results/threshold probabilities, pinned model/source hashes and package-version receipts, diagnostic replay summaries, architecture and decision reports. A clean clone can run the documented portable numeric/structural checks. Private waveform/model/viewer tests require separately provisioned local inputs and are explicitly outside the portable subset. Optional historical output links are not instructions to force-add generated figures or private files.

Do not remove old reports simply because their then-proposed next experiment has been superseded; the current development overview and checkpoint README establish the current closed-research decision. Do not retain execution transcripts, old Git snapshots or generated image/HTML output when the script and numeric evidence already explain the result.
