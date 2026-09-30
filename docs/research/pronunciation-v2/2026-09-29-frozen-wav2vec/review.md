# First frozen-wav2vec pass — preflight stop

**INCONCLUSIVE — not run.** Corpus verification found positive evidence that the nominal `shtooka:wei-gao` group contains an audio file from a different credited voice. The user explicitly required stopping before training in that case. All 500 files pass byte/decode integrity checks, but that does not validate source identity or licensing. No empirical conclusion about frozen wav2vec2 or superiority to V1 is possible from this pass.

The decisive item is **commons:3052714 / Zh-wéi.ogg**: manifest speaker Wei Gao; actual embedded speaker Tan, copyright Yue Tan, female speaker metadata and a 2009 date. The remaining 326 group members name Wei Gao. The same file has embedded text 围 versus manifest 为 and a CC BY-SA grant versus selected CC BY. A second license conflict affects the Yue Tan singleton. The full evidence and caveats are in [preflight.md](preflight.md) and [provenance-conflicts.json](provenance-conflicts.json).

## Requested decision record

1. **Branch / starting commit:** `pronunciation-v2-research`, `30820a449df3ed7f50ddd2c0013910e3844048a1`; clean starting tree and finalized data checkpoint present.
2. **Corpus preflight:** 500 paths, source lengths/SHA-1, local SHA-256, fresh PCM SHA-256 and decode success verified; no exact duplicates. Provenance gate **failed**.
3. **Usable clips:** 500 physically usable/decodable; training-approved retained count **not certified**. The original manifest is unchanged.
4. **Acquired tones:** T1/T2/T3/T4 = **118/110/120/152**; zero neutral labels.
5. **Groups:** Wei Gao-labelled 327, CanonNi 60, Levi Highway 49, Luilui6666 60, four singletons. Full tone cells in [preflight.md](preflight.md).
6. **Shtooka provenance:** 326 files explicitly name Wei Gao as speaker. One names Tan/Yue Tan. Nicolas Vion is jointly credited; exact recorder/operator role remains independently unverified. No biometric certainty is claimed.
7. **Audit:** automatic metadata/hash/signal verification on all 500; 38 stratified metadata/content audit items, including duration extremes and anomalies. No direct listening. [Listening list](human-listening-audit.csv).
8. **Primary split:** requested allocation remains a proposal, **387 train / 49 validation / 60 test**, four auxiliary. It was not frozen because of the explicit stop condition.
9. **Leakage:** proposed group IDs are disjoint; actual source grouping failed validation. No training/evaluation happened, so no model leakage occurred. Do not describe this as a certified person-disjoint experiment.
10. **Encoder:** planned `facebook/wav2vec2-base`; no loaded model, resolved revision, measured dimension or inference device. Its current card still declares Apache-2.0. No model-license change was observed.
11. **Dependencies/environment:** no installation or dependency-file changes. CPU available; NVIDIA driver unavailable. [Environment](environment.md).
12. **Feature implementation:** not started.
13. **Hidden-layer indexing:** not exercised or empirically verified; planned 4/6/8 comparison remains pending.
14. **Extraction runtime:** not measured; no embeddings extracted.
15. **Pooling:** not implemented; requested padding-aware mean pooling remains pending.
16. **Normalization:** no scaler fitted; no data used to estimate model normalization.
17. **Linear head:** not fitted; requested multinomial logistic regression remains pending.
18. **Grid:** no search performed; intended three layers × three C values remains pending.
19. **Validation candidates:** none evaluated; no fabricated validation table.
20. **Selected configuration:** none; no experiment-config lock created.
21. **Selection-before-test evidence:** no model selection and no test metric opening; machine summary explicitly records both the pre-model stop and unopened test metrics.
22. **Primary test results:** not run. Accuracy, balanced accuracy, macro F1, per-tone scores, confusion matrix and T2/T3 error counts are unavailable.
23. **Naive baselines:** not evaluated. No headline comparison is claimed.
24. **V1:** not run or tuned; no coverage/accuracy/F1/abstention metrics. Production pronunciation source remains unchanged from the historical checkpoint.
25. **Per-item test results:** none; [corpus-diagnostics.csv](corpus-diagnostics.csv) contains integrity diagnostics, not predictions.
26. **V2 errors:** none available; the listed issues are source metadata conflicts, not model errors or pronunciation defects.
27. **Confident wrong predictions:** none available.
28. **Secondary source-group diagnostic:** not run because the primary experiment never started.
29. **Source dependence:** unmeasured.
30. **Softmax:** no scores generated; no calibration or confidence claims.
31. **Test contamination:** no test predictions/metrics examined and no model decisions made. The requested integrity audit included held-out metadata, without fitting or modifying preprocessing.
32. **Decision:** **INCONCLUSIVE — preflight blocked, hypothesis untested**. This is not NO-GO for the formulation.
33. **Reason:** explicit mixed-voice stop condition, corroborated by actual file metadata and replacement history; unresolved file-specific license/content conflicts add concern.
34. **Hypothesis survived?** Neither supported nor falsified; it has not been tested.
35. **Material V2 improvement over V1?** Unknown.
36. **Next experiment:** first repair/review the corpus; then run the originally requested experiment #1. There is no scientific basis yet for choosing experiment #2 from results.
37. **Future choice:** more independently verified speakers and audited learner speech remain important after the first probe, but no result here justifies switching to HuBERT, context windows, explicit F0 or fine-tuning.
38. **Production:** implement no V2 integration, thresholds, feedback, graph/UI, schema or API changes from this stopped pass.
39. **Next reasoning level:** HIGH for corpus provenance resolution and the subsequent guarded model pass.
40. **Files:** two new offline audit/test Python files and seven curated artifacts listed below. No existing tracked file was modified.
41. **Focused tests:** 39 tests pass (31 existing, eight new); Ruff lint/format checks pass for both new files. The broader directory lint check exposes a pre-existing E501 at `report.py:95`, left unchanged. ML-specific tests are not claimed because no ML harness was implemented.
42. **git diff --stat:** empty; all additions are untracked. Nothing staged, committed or pushed.
43. **git status --short:** shown below.

## Concrete next step

Resolve the two license conflicts and the replaced Wei Gao-labelled file before resuming. A conservative later repair could exclude the two disputed files without acquiring replacement audio, retain all remaining Shtooka/Wei Gao items in one group, and manually review the unmarked `na` tag. That would leave **498 acquired candidates / 495 primary candidates**, with a possible **386/49/60** primary split, if every other check survives. These are hypothetical arithmetic counts, **not an applied exclusion or approval**. Do not silently reassign the replaced audio to a new primary group or train through this stop.

The anomaly also exposes an acquisition-gate limitation: page-derived speaker/license assignments were preserved even when embedded metadata contradicted them. This pass adds a separate reproducible preflight that surfaces those contradictions; it does not rewrite historical acquisition evidence or alter existing download/selection behavior.

## Created artifacts

- `benchmark/pronunciation_v2/preflight.py`: read-only byte/decode/source-metadata verification, embedded contradiction diagnostics, deterministic audit sampling, nonzero stop status.
- `benchmark/pronunciation_v2/test_preflight.py`: regression cases for replacement metadata, license fields, incomplete pinyin, hash changes, sampling and singleton separation.
- `review.md`, `preflight.md`, `environment.md`.
- `preflight-summary.json`, `corpus-diagnostics.csv`, `provenance-conflicts.json`, `human-listening-audit.csv`.

No raw audio, model weights, embeddings, trained head or cache files were added to Git. No production code, user recordings, old manifests or persistent corpus files were changed.

```text
$ git diff --stat
[empty]
$ git status --short
?? benchmark/pronunciation_v2/preflight.py
?? benchmark/pronunciation_v2/test_preflight.py
?? docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec/
```
