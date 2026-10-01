# Experiment 3 preflight review

**Preflight complete; no fresh panel available.** The linear baseline reproduces
bitwise exactly. One nonlinear architecture and training protocol are frozen,
and its implementation passes synthetic learning/determinism tests. No real-data
nonlinear fit or fresh-test prediction was run. This is no evidence yet for or
against nonlinear generalization.

Started clean on `pronunciation-v2-research`, HEAD
`5574b4bfdb717de18349502fe6fa024c456ede12`. No production files or dependencies
changed. No commit or push. The requested directory uses 2026-10-01; receipts
record actual UTC times. Experiment 2's 118 clips remain OPENED/INSPECTED and
Luilui remains a known stress set. Frozen lexical labels are benchmark truth;
no error-driven relabeling and no mandatory human listening gate were introduced.

## Frozen head and training

B is **768 → 8 → tanh → 4**, with biases: **6,188 parameters** versus A's 3,076.
A 96-fold bottleneck and approximately twofold parameter increase keep the one
candidate modest given 386 training clips from two speakers. This is not a claim
that the capacity is optimal. No alternative architecture or hyperparameter sweep.

Train-only StandardScaler; CPU FP32; Xavier-uniform weights (gain 1), zero biases;
seed **20261001**; full batch **386**; AdamW **lr=0.001**, betas **0.9/0.999**,
epsilon **1e-8**, weight decay **0.01** on weights only; unweighted mean cross
entropy; **200 updates**, final epoch; no schedule, dropout, shuffling or early
stopping. Nonfinite values abort. Levi cannot choose a checkpoint. Exact controls,
prospective success limits and reporting requirements are in [protocol.md](protocol.md),
with code/config/input hashes in [protocol.lock.json](protocol.lock.json).

Both heads use unchanged frozen `facebook/wav2vec2-base` revision
`0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`, layer 8, whole-valid-frame mean,
mono 16 kHz and original 386 training rows. No tone-specific pretraining, F0,
expected tone, text/lexical identity, temporal thirds, crops, augmentation or
encoder gradients enter this implementation.

## Linear reproduction

Freshly decoded and re-extracted **435 original training/Levi clips**, using only
layer 8. Every feature, fitted scaler/head array and Levi probability equals the
frozen Experiment 1 artifact **bitwise**, with maximum difference **0.0**.
The encoder state hash is unchanged and first-clip repeated extraction is bitwise
identical. Train membership is exactly 386; Levi is 49.

Levi accuracy **0.9591836734693877**, balanced accuracy **0.9464285714285714**,
macro F1 **0.9557692307692308**. Full per-tone metrics, confusion counts and
extraction evidence are in [baseline-reproduction.json](baseline-reproduction.json).
The newly fitted compact linear head is retained as `head-linear.npz`; waveform
and feature caches remain ignored. No stress-set prediction was generated.

## Candidate speakers and no-seal decision

Reverified 9,363 inventory pages, 1,710 cached Commons revision audits and 82
OMPAL native sentence records. The larger inventory exposes 23 Lingua Libre
speaker display names; uploader counts are never substituted for speakers.

Eligible new isolated T1/T2/T3/T4 counts:

| Speaker/profile | Counts | License | Mandarin native status |
| --- | --- | --- | --- |
| Vickylin77amis / Q19761 | 1/0/2/0 | CC BY-SA 4.0 | UNKNOWN |
| Assassas77 / Q4250 | 0/0/1/1 | CC BY-SA 4.0 | UNKNOWN; French-native/intermediate-Chinese declaration |
| BlueCamille / Q927785 | 0/1/0/0 | CC BY-SA 4.0 | UNKNOWN |
| Yug / Q480 | 0/0/1/0 | CC BY-SA 4.0 | UNKNOWN |
| Yihsiangyang / Q190194 | 0/0/0/0 | CC BY-SA 4.0 | UNKNOWN; ambiguous reading |
| Shangkuanlc / unresolved ID | 0/0/0/0 eligible | CC BY-SA 4.0 in raw revisions; strict parser defers | UNKNOWN |
| OMPAL SPEAKER01001 / 01002 / 01003 | 0/0/0/0 each | CC BY 4.0 | NATIVE by corpus documentation |

Shangkuanlc's unambiguous but excluded lexical candidates are **13/8/6/7**;
resolving identity and license parsing still would not meet coverage. OMPAL has
20/29/33 original sentence files, with no valid isolated label per whole clip.
No segmentation/cropping was performed. Nine additional inventory-only names
(Cookai1205, XtexChooser, Aa087159, Liang, KhawaChenpo, Bakerkobe, Lim Natee,
Zhjiang1103, Kokhanloong2019) have no audited eligible isolated targets; native
status is UNKNOWN, with per-source license fields and blockers preserved.

See [sources.md](sources.md), [candidate-speakers.csv](candidate-speakers.csv),
[candidate-items.csv](candidate-items.csv), [exclusions.csv](exclusions.csv) and
[source-audit.json](source-audit.json) for exact provenance and count definitions.
Previously GREEN alternatives did not resolve the speaker/isolated-target gap.
The seven sparse eligible items cannot satisfy three new speakers with eight
items per tone each. **No sealed-test-manifest.csv exists; seal SHA-256: N/A.**
The old 118-clip seal is never repurposed.

## Untouched data and next pass

No candidate audio was downloaded or supplied to either Experiment 3 head.
Previously cached OMPAL audio remains unused by either head. The nonlinear head
has seen synthetic fixtures only; it has not seen real train, Levi, opened 118,
Luilui or new candidate features. Linear reproduction sees original train/Levi
only. Historical stress sets remain inspected regardless of this pass's access.

Next execution (fits B on the original 386 and locks both fitted heads; no test
predictions, no fresh-data acquisition required for this training step):

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/nonlinear_head.py verify
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/nonlinear_head.py develop
```

That command has **not** been run. Receipts reject silent reruns. A later bounded
data pass must identify sufficient new independent speakers and seal verified
assets before an evaluation runner is implemented/locked and predictions opened.
There is intentionally no fresh-test CLI in this preflight implementation.

## Validation and limitations

- **78 research/model unittest tests passed**, including 12 new tests for exact
  baseline config, head shape/capacity, deterministic learning, membership and
  label integrity, prediction-independent selection, speaker disjointness,
  provenance requirements and immutable manifest writes.
- **54 existing evaluation-preflight tests passed.** Thus 132 directly relevant
  checks pass with the existing pinned environments.
- Broader historical forensic/error-audit checks: **14 passed, 1 failed**.
  `test_full_deterministic_replay` reproduces all historical artifacts identically
  except `provenance.json.head`: current HEAD is `5574b4b…`, while the historical
  report records `1b40cda…`. The two newly generated replays match each other.
  This pre-existing HEAD-sensitive fixture is documented, not rewritten.
- An initial attempt to load those API-dependent modules in the ML environment
  produced two import errors (missing SQLAlchemy); rerunning in the API environment
  required no package changes. Logs/commands are summarized in `validation.json`.
- Those extra historical tests replayed saved error diagnostics, including legacy
  acoustic/F0 analysis, under temporary directories. They did not fit a head,
  generate new model predictions, change lexical labels, supply F0 features to
  Experiment 3, or affect the frozen architecture/training policy.
- Ruff check and format check pass on all three new Python files. `git diff
  --check` passes; final protocol/code/checkpoint/environment verification passes.

The lock protects protocol/code and original membership, not a nonexistent test
panel. Public profile identity does not guarantee unique biological speakers;
UNKNOWN native status cannot support native-specific claims. No accuracy claim
for B is made from synthetic fixtures or opened stress data.
