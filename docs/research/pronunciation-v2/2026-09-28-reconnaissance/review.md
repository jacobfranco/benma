# Pronunciation V2 reconnaissance — 2026-09-28

**Recommendation:** test a frozen English-pretrained wav2vec2 Base encoder with a linear four-tone head, using independently audited surface-tone labels. Keep HuBERT Base LS960 as the backup. The experiment is CPU-feasible and can be small. Commercial data provenance, trustworthy labels and boundary preparation are the main prerequisites.

**Legal outcome:** two documented permissive encoder paths and an explicitly commercially permitted learner corpus were found. No complete public native-training plus pretrained-alignment chain was verified GREEN under the requested strict policy. Common Voice, AISHELL and Mandarin-model licensing contain material conflicts or unresolved scope. The concrete fallback is a small directly licensed native collection with manual boundaries; it has been designed, not collected or cleared. A public-data substitution must close the exact questions in [licensing.md](licensing.md).

**This pass changed only six curated Markdown research files.** No model/data downloads, training, package installation, paid provider calls, production code/schema/UI changes, commit or push occurred. Research conclusions are proposals, not empirical performance claims.

## Requested decision record

1. **Branch / baseline:** current branch `pronunciation-v2-research`; HEAD and merge-base with local `pronunciation-calibration` are both `68057aa57cdfccbba01c986be827a402fcb59a67` (`feat: checkpoint Mandarin pronunciation calibration`). This branch has no newer commit than that inherited checkpoint. Initial working tree clean. Remote state was not queried or changed.
2. **Objective:** target-independent observed/realized Mandarin T1–T4 for known/aligned Practice syllables; expected surface tone compared only afterward. Neutral tone deferred, uncertainty explicit, F0 optional.
3. **Dataset shortlist:** [datasets.md](datasets.md) inventories Common Voice zh-CN, AISHELL-1/3, THCHS-30, FLEURS, OMPAL and a directly licensed native collection, including size, speakers, labels, segmentation and recommended roles. [licensing.md](licensing.md) covers commercial, redistribution, derivative, attribution, privacy and access conditions. No public corpus is silently promoted from lexical transcript to gold observed label.
4. **L2 findings:** OMPAL provides a viable commercial-use grant, but its tone scores are correctness annotations requiring additional realized-category audit. LATIC permission unverified; Griffith/Nanjing ND workflow unresolved. Benma recordings remain held out. [Details](datasets.md#learner-specific-findings).
5. **Encoder shortlist:** wav2vec2 Base and HuBERT Base LS960 are GREEN documented paths; WavLM Base, Tencent Mandarin HuBERT/wav2vec2 family and XLSR-53 are YELLOW. Architecture, grants, corpus ancestors and resource estimates: [models.md](models.md).
6. **Rejected/deferred:** AISHELL-2, MAGICDATA, ST-CMDS, Primewords and several tone-related collections have explicit incompatible restrictions. WenetSpeech is a license conflict and excluded, rather than resolved in favor of a permissive link. Large multilingual models add provenance/compute burden without answering the first question more cleanly.
7. **Label meaning:** lexical tone, expected contextual tone, observed realization and learner correctness remain separate. A target-independent classifier can identify the wrong tone correctly. [Label contract](experiment-plan.md#2-label-contract-and-inclusion-policy).
8. **Phase-1 labels:** safe isolated, safe connected, verified surface transformation, ambiguous/exclude, neutral/defer. Rights, boundary quality and rater confidence are additional gates. No v1 pseudo-labels.
9. **Sandhi:** listening-confirmed T3 sandhi can map lexical T3 to observed T2; 一/不 grammar and phrase boundaries must be audited. Partial low T3 stays T3 when identifiable, without requiring a textbook rise. Complex chains/reduction excluded initially.
10. **Alignment:** manual gold/phase-1 boundaries avoid hidden weight lineage. MFA is technically strong for offline phone alignment but its Mandarin training ancestry is YELLOW. CTC algorithms do not independently provide a cleared acoustic model. [Comparison](experiment-plan.md#3-alignment-and-extraction).
11. **Native gold:** 240 instances, 60 per tone, 12 independent test speakers; balanced isolated/connected and clean/consumer conditions. Enough for large-effect screening, not production certification.
12. **Learner challenge:** 120 newly audited OMPAL centers plus all eligible Benma phone spans, separately reported; no head/threshold/calibration fitting. Historical Benma convenience data is not unbiased population gold.
13. **Robustness:** controlled codecs, resampling, noise, mild reverb, gain and measured clipping; originals and variants share splits/clusters. First measure clean-trained failures; augmentation is a later decision.
14. **Speaker splits:** proposed 48 speakers: 24 train, three disjoint groups of four for tuning/calibration/thresholds, 12 test. All recordings and augmentations of a person stay together. [Exact counts](experiment-plan.md#1-data-and-locked-splits).
15. **OOD:** hold all OMPAL out; add FLEURS after its text-lineage check. Native OMPAL has too few speakers to replace the main gold. Missing FLEURS IDs limit per-speaker claims.
16. **Pretraining leakage:** recommended Base checkpoints document English LibriSpeech, with no known Mandarin benchmark inclusion. That is disclosed-lineage evidence, not proof of every file's history. XLSR-53 includes historical Mandarin CV; a newer CV release can repeat old audio/speakers. Wenet-pretrained models invalidate any claim of never-seen Wenet audio. Directly collected new native audio is the strongest practical source holdout. Also audit pretraining of aligners and annotation tools, not just the tone encoder.
17. **Input:** exact aligned syllable, no acoustic padding first. Bounded ±100/250-ms context with center-only pooling is a later controlled ablation; whole-window pooling is a control. Keep unvoiced initials.
18. **First encoder:** `facebook/wav2vec2-base`, frozen, no ASR head; three predefined middle-layer candidates, selection only on tuning speakers.
19. **Backup:** `facebook/hubert-base-ls960`, same data/protocol, no new architecture search.
20. **Head:** mean pooling + standardized features + multinomial linear softmax; unweighted cross-entropy on balanced labels, L2 regularization. Three-bin temporal pooling is the bounded diagnostic if temporal averaging fails.
21. **Why frozen:** tests recoverable representation with few trainable parameters, reusable CPU feature cache and less overfitting. Primary probing research supports the hypothesis but does not establish realized learner-tone accuracy. [Scientific basis](models.md#why-this-is-scientifically-worth-testing).
22. **Metrics:** macro F1/balanced accuracy, per-tone precision/recall, T2↔T3, all-item correct/wrong/abstain, calibration, selective accuracy and source/speaker/condition/style slices; uncertainty clustered by speaker.
23. **Calibration:** scalar temperature on separate speakers, max-probability thresholds locked on another group, actual accuracy/coverage at nominal 80%/60%. Margin and entropy diagnostic only; neutral/OOD overconfidence explicitly tested.
24. **V1 comparison:** frozen whole-audio extraction and same center bounds; show v1's attainable confidence points, V2 curves, common-coverage and all-item outcomes. Never assign numeric probability to v1's ordinal confidence or silently remove its unclear cases.
25. **F0 fusion:** later paired embedding-only/F0-only/combined ablation, including missingness; no v1 labels or continuous-F0 admission gate.
26. **Neural F0:** low priority. CREPE/torchcrepe, FCPE, RMVPE could improve graphs/features/diagnostics; none benchmarked or production-cleared here.
27. **Phrase path:** center syllables with bounded acoustic context, contextual labels and per-center abstention. Prosody/coarticulation need coverage, not rigid template matching.
28. **Hardware:** i7-10700F, 8 cores/16 threads, 31 GiB RAM, ~195 GiB free disk; `nvidia-smi` driver communication failure. No usable GPU or VRAM claim. [Estimates](models.md#actual-machine-and-planning-estimates).
29. **Server inference:** resident ~95-M encoder, bounded CPU worker/batches plausible; latency unmeasured. First benchmark warm/cold p50/p95/RSS before an interactive deployment decision.
30. **Legal matrix:** [licensing.md](licensing.md), conservative on conflicting wording and precise artifact identity. A model's permissive label does not resolve ancestor rights.
31. **Unresolved legal questions:** exact CV private-commercial/crop/cache/head permissions; AISHELL/THCHS academic scope; Wenet rights; WavLM license pointer; XLSR/MFA ancestors; FLEURS text; consent and new-recording grants. No permission request was sent to any owner.
32. **First experiment:** execute the nine-step data/split/audit → exact crop → frozen features → small head → calibration → paired v1 evaluation plan in [experiment-plan.md](experiment-plan.md). Directly licensed data is the fallback, not an already available resource. Public-data clearance can change acquisition without reopening architecture.
33. **Cost/time:** approximately 3–5 engineering days after data readiness; 35–70 annotator-hours plus 48 recording sessions; 1–6 h provisional local compute budget. Example acquisition/annotation budget $1.4k–$5.4k is an assumption, not a quote or authorized expense. Rights/recruitment turnaround unestimated.
34. **Do not do yet:** no fine-tuning, broad model sweep, neural-F0 integration, augmentation policy optimization, production dependency/schema/UI work, conversation architecture, on-device deployment, large downloads, provider calls or v1 modifications.
35. **Next reasoning level:** HIGH.
36. **Why:** implementation is small, but label separation, speaker leakage, boundary handling, frozen-v1 parity and calibration are subtle. EXTRA HIGH adds little before data/rights gates close; MEDIUM can handle a later isolated head/cache task.
37. **Created files:** this review, [datasets.md](datasets.md), [models.md](models.md), [licensing.md](licensing.md), [experiment-plan.md](experiment-plan.md), [sources.md](sources.md).
38. **`git diff --stat`:** empty for tracked files, because this pass adds an untracked directory and does not stage it. Report the new files separately; do not imply no work was created.
39. **`git status --short`:** expected/verified final scope is `?? docs/research/pronunciation-v2/`. Final command output is shown in the completion response. No commit or push.

## Repository interface audit

All paths below are relative to the repository root; line anchors refer to the inspected checkpoint.

| Boundary | Inspected implementation | Consequence for an offline V2 harness |
|---|---|---|
| Practice analysis orchestration | `services/api/src/benma_api/pronunciation/laboratory.py:215`, `service.py:75` | Laboratory prepares assessment/acoustic/alignment work, persists results and derives interpretation. Do not call its analyze path for offline research: it can invoke providers and commit DB rows. |
| Local acoustics / persistence | `pronunciation/acoustics.py:303` and `:456`; `db/models.py:336`; `schemas.py:322` | `AcousticRun` records algorithm/version, parameters, JSON normalized result and runtime/status; raw F0 evidence is separate from any future learned-tone observation. Do not overwrite or reinterpret old JSON as V2 output. |
| V1 observation | `pronunciation/contours.py:221`; `schemas.py:382`; `evidence_region.py` | `classify_contour` uses raw evidence and numeric bounds, ignoring the display argument. Categories are 1-like…4-like/neutral-like/unclear; actual schema confidence is moderate/low. No calibrated probabilities exist. |
| Expected tone | `pronunciation/surface.py:25`, `readings.py`, `targets.py`; `schemas.py:392` | Existing limited deterministic surface rules and reasons stay downstream; expected/lexical fields are not classifier features. |
| Learner verdict | `apps/mobile/src/speech/learnerVerdict.ts:6` | Category, confidence/reason and quality gates map to matches/close/different/unclear. A future V2 mapping needs its own validated semantics; don't force probabilities through current reason allowlists. |
| Audio | `audio/service.py:88`; `storage/audio_store.py:11` | Original-preserving ingest and canonical mono PCM WAV; object-store keys, hashes, metadata and account ownership. Use authorized research copies, not DB/storage path guessing. |
| Timing | `pronunciation/alignment.py`, `azure_alignment.py`, `timing.py` | Existing replay/MFA/Azure adapters do not make all historic intervals phonetic gold. Never infer voicedness from an interval's label. |
| Diagnostics | `pronunciation/diagnostic.py`, `laboratory.py`; scripts `pronunciation_diagnostic.py`, `architecture_review.py`, `calibration_contours.py`, `calibration_upstream.py` | Existing provenance and numeric replay tools can supply v1 comparison evidence; avoid live-service mutations. |
| Explicit export | `pronunciation/research_export.py:43`; `scripts/export_pronunciation_attempt.py` | Checks original/canonical hashes, marks requested production as **not ground truth**, and uses personal-development consent. Export records and commits a ResearchExport row: not a read-only function. No export invoked in this pass. |
| Benchmark/replay | `benchmark/cli.py`, `models.py`, `annotation_workbench.py`, `providers/replay.py`, `acoustics/alignment.py`, `acoustics/pitch.py` | Existing standalone harness/annotation/replay infrastructure is useful. MFA TextGrid parser flattens interval tiers; it is not ready syllable gold. torchcrepe adapter already exists; no reason to integrate a second production F0 tracker. |
| Future research location | Proposed `benchmark/pronunciation_v2/` | Isolated optional dependencies, manifest/cache/head/evaluation modules; curated reports remain under `docs/research/pronunciation-v2/`, data/features outside tracked docs. No directory/module implemented now. |

Future V2 observation should be versioned separately from `ObservedContour`, preserving audio/span/model/config hashes, probability vector, calibration and abstention provenance. That is an interface recommendation only; no migration or new schema was authored.

## Inherited v1 assets and provenance limits

All four requested reports are tracked and present:

- `docs/calibration/2026-09-23-architecture/review.md`: raw evidence/display separation and conservative evidence selection.
- `docs/calibration/2026-09-24-final/review.md`: narrow low-confidence recoveries and stopping point for heuristic calibration.
- `docs/calibration/2026-09-25-consistency/review.md`: graph/classifier consistency; then-current 63 persisted recordings / 112 rows.
- `docs/calibration/2026-09-25-f0-tracking/review.md`: tracker alternatives/continuity failed to establish a safer replacement; latest historical corpus 67 recordings / 116 rows, 95 authorized spans.

Local directories contain 40 / 38 / 59 / 46 files respectively, approximately 13.4 / 5.4 / 9.9 / 17.5 MB including ignored artifacts. `.git/info/exclude` contains `docs/calibration/*`; tracked reports remain tracked despite that rule. The F0 inventory JSON exists with 67 entries. `/tmp/benma-f0-corpus` **does not currently exist**. Audio availability was not reestablished by querying production DB, and no old traces were regenerated or copied into this report.

Historical reports refer to the pre-checkpoint working tree and older `a8bdfab` base. The actual frozen code to compare now is the inherited **68057aa** checkpoint, not the historical report's older base hash.

## Initial commands and final validation

```text
$ git branch --show-current
pronunciation-v2-research
$ git status --short
[empty]
$ git log -3 --oneline
68057aa feat: checkpoint Mandarin pronunciation calibration
a8bdfab feat: add conversational pronunciation feedback
b3ab72c feat(api): add persisted free talk assistant speech
$ git merge-base HEAD pronunciation-calibration
68057aa57cdfccbba01c986be827a402fcb59a67
```

Validation is appropriate to documentation-only work: verify six small Markdown files, local report links, trailing whitespace, unchanged HEAD/branch and absence of tracked code diffs. No application test suite or ML experiment is claimed. The source register distinguishes inaccessible pages, documentary findings and unmeasured estimates. The next pass has one bounded hypothesis and explicit acquisition/label gates, rather than an open-ended architecture discussion.
