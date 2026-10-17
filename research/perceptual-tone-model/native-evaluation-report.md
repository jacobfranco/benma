# Native-speech tone feasibility — stopped in Phase A

**Status: STOPPED_PHASE_A_DATA_QUALITY. No evidence yet that learned tone
perception beats the frozen deterministic classifier.** This is neither a positive
ML result nor evidence that ML cannot work. No classifier was trained; no held-out
predictions, accuracy, F1, recall, confusion matrices or learned probe probabilities
were produced. Phase B did not start.

The selected bounded THCHS-30 subset exposed inadequate syllable extraction and
unrepresentative retained context coverage. Speaker alias/native-status provenance
and original transcript matching also remain unresolved. The requested stop
conditions apply: do not train through those gaps or claim speaker generalization.
The developer audio QA packet remains unreviewed; code/text inspection and encoder
execution must not be described as listening.

## Actual data and engineering results

Retrieved **16 MiB of official corpus audio archive**, plus **40.9 MB of published
alignments**, small metadata and a pronunciation dictionary. Parsed **68 complete
utterances / 10.68 minutes**, **2,210 syllables**, **36 released speaker prefixes**,
and **21 conservative speaker groups**. These counts do not certify 21 native
people. Only **229 candidates** survived, with **1,981 exclusions**. Candidate
partitions have **137/57/35** syllables; actual training/test sizes are **0/0**.

| Tone | Train candidates | Validation candidates | Test candidates |
| --- | ---: | ---: | ---: |
| T1 | 32 | 8 | 4 |
| T2 | 25 | 17 | 13 |
| T3 | 16 | 7 | 3 |
| T4 | 61 | 25 | 15 |
| NEUTRAL | 3 | 0 | 0 |

The principal problem is not a low classifier score. **1,615 syllables lack a
verified boundary inside a multi-character word.** A convenient alignment tier
contains evenly spaced transcription timing; using it would invent syllable
ownership. Strictly keeping single-Han word intervals leaves no T3-before-T3,
T3-before-neutral or utterance-final T3 candidates. Neither held-out partition
contains neutral. These omissions directly undermine the intended comparison.
See [the complete exclusions and T3 table](native-error-analysis.md).

The real encoder smoke check used two training-partition utterances, never test
audio. It extracted **48 vectors**: 2 encoders × 3 layers × 2 views × 2 poolings ×
2 targets. HuBERT revision `fce0375452b1dd6c080ac3248d423d4d037bc831` and WavLM
revision `4c66d4806a428f2e922ccfa1a962776e232d487b` remain pinned and frozen.
Layers **6/9/12**, **target-only / ±200 ms** windows, and **target mean / context
mean** pooling all executed. Label/text metadata poisoning left vectors and cache
entries identical. This tests extraction, not tone-recognition quality.

The initial extraction check took **6.72 seconds** with two CPU threads; the
final-manifest cache check took **2.31 seconds**. These small engineering timings
are not an extrapolated Phase B training estimate. The existing encoder cache is
about 721 MiB. Downloads occupy about 58 MiB including the initial 2 MiB probe;
the final packet occupies 31 MiB, with two earlier 31 MiB audit iterations retained.
No GPU, paid service, new dependency installation or recruited annotation was used.

## Requested result checklist

| # | Requested item | Actual outcome |
| --- | --- | --- |
| 1 | Pass status | Stopped at data quality; scientific comparison incomplete. |
| 2 | Corpus candidates | THCHS-30, AISHELL-1, AISHELL-3, Common Voice zh-CN, Primewords, ST-CMDS; AISHELL-2 access terms not established. |
| 3 | Primary and why | THCHS-30: small official prefix, connected speech, 16 kHz, published alignments; selection failed readiness audit. |
| 4 | License/access | Official audio Apache-2.0, derived alignments MIT; actual bounded downloads verified locally. [Decision table](native-corpus-recon.md). |
| 5 | Corpus size/speakers | Advertised corpus and actual subset distinguished above; true independent/native speaker count unverified. |
| 6–8 | Labels, sandhi/neutral, exclusions | Conservative weak surface supervision; uncertainty excluded, no lexical fallback for unresolved surface cases. [Policy](tone-labeling-policy.md). |
| 9 | Speaker split | Seed 20261015, mechanical group/source/prompt/PCM/text separation passes; true speaker independence not certified. |
| 10 | Input leakage | Strict audio-vector schema; no lexical/surface tones, Hanzi, expected-family/context block. Tone-stripped identity requires train-only ambiguity controls. |
| 11 | Encoder/layer/pooling tested | Both pinned encoders; 6/9/12; target/context mean; tight/±200 ms. Engineering smoke only. |
| 12–13 | Training/test sizes | **0 trained / 0 evaluated**; 137/57/35 quarantined candidates are not an executed experiment. |
| 14 | Deterministic baseline | Corpus accuracy/coverage not measured. Read-only adapter matches 53 saved acoustic units; 63-example full replay unchanged. No synthetic corpus F0 supplied. |
| 15–20 | Learned results, accuracy/F1, per-tone/T3 recall, T3→T4, matrices | **Unavailable**, including deterministic paired comparison. Never replaced with zeros or mock scores. |
| 21 | Best model | None selected. |
| 22–23 | 我想买这个 / natural 我→T4 | No learned probe. Current archived 我想买这个 baseline has 我=T3; T4 decisions persist in other archived phrases. [Exact probe inventory](native-external-probe.md). |
| 24 | Resources/runtime | CPU-only engineering timings and disk usage above; Phase B not run. |
| 25 | Tests | 33 Python tests; 2 Node test files; 413 baseline hashes; unchanged 63-example replay; real cache invariance checks. |
| 26 | Changed files | [Pass-specific list](reports/native-changed-files.txt). Existing uncommitted infrastructure preserved. |
| 27 | Limitations | Weak labels, unaudited audio, poor context/class coverage, incomplete original transcript and speaker provenance, no model comparison. |
| 28 | Next step | Repair source/ownership/identity provenance, then repeat 500–1,000-candidate Phase A including the missing contexts and complete the small developer audio QA. |

## Model set status and comparison rules

Baseline 0's saved-evidence acoustic adapter is implemented and tested. It has
four numbered-tone outputs; `UNCLEAR`/`UNAVAILABLE` are abstentions, **never
neutral**. Its family support values are not class probabilities. Corpus F0 and
production evidence preparation was not pursued after the data gate failed.

Baseline 1 (existing F0/prosody features → logistic regression), HuBERT and WavLM
logistic heads, and a 64-unit MLP are recorded as a **recipe**, not fitted models.
The existing acceptability trainer is not a five-class tone trainer and was not
reused under a misleading label. A complete native-tone training/selection runner
is **not implemented in this stopped pass**. Model B/identity augmentation and
embedding+F0 fusion are not fitted either.

A future valid run must report all-example coverage and metrics, both models on
the exact common covered subset, and a separate numbered-tone comparison so that
the baseline's lack of neutral output does not dominate the conclusion. Keep
neutral performance explicit. Select on validation only, freeze the small chosen
configuration, then evaluate held-out test once. Add speaker-level uncertainty
and tone-stripped-identity controls before interpreting a tone-perception gain.
The current script does not silently promote candidates into that workflow.

## Reproduction and artifacts

Use `benchmark/pronunciation_v2/.venv/bin/python` from repository root. An optional
separate environment uses `native-requirements.txt`; no production install is
needed. Downloads require network access and stay under ignored generated data.

```sh
P=research/perceptual-tone-model
D="$P/data/generated/native-tone-recon"
mkdir -p "$D"
curl -fSL --max-filesize 16777216 --range 0-16777215 \
  https://www.openslr.org/resources/18/data_thchs30.tgz -o "$D/thchs-16MiB.gz"
curl -fSL --max-filesize 41000000 \
  https://zenodo.org/api/records/7528596/files/grids.zip/content -o "$D/grids.zip"
curl -fSL --max-filesize 1000000 \
  https://zenodo.org/api/records/7528596 -o "$D/zenodo.json"

PY=benchmark/pronunciation_v2/.venv/bin/python
# OUTPUT must be a new directory. Existing manifests/packets are write-once.
OUTPUT="$P/data/generated/native-tone-reproduction"
$PY "$P/scripts/native_prepare.py" --prefix "$D/thchs-16MiB.gz" \
  --grids "$D/grids.zip" --metadata "$D/zenodo.json" --output "$OUTPUT"
$PY "$P/scripts/native_smoke.py" --manifest "$OUTPUT/candidates.jsonl" \
  --output "$OUTPUT/encoder-smoke.json"
PYTHONPATH="$P" $PY -m unittest discover -s "$P/tests" -v
node --test "$P/test_evaluate.cjs" "$P/test_native_baseline.cjs"
$PY "$P/scripts/pilot.py" verify-baseline
```

The retained authoritative packet is
[`data/generated/native-tone-phase-a-v3/review.html`](data/generated/native-tone-phase-a-v3/review.html).
It contains 15 **training-only** review items and an unanswered JSONL checklist.
Manifest SHA-256:
`20b8953bd18f2f273f14b5d05180f26ebb177f47d1e4c4170ffea348ae5cf2f8`.
Changing output paths changes manifest hashes because provenance contains paths;
content-addressed PCM/embedding keys remain reusable. Source prefix SHA-256:
`a0d94c1ba7f32e02bf889c57d14a1c78f5c7aac59e0994eabb5ea741be9708aa`.

[`reports/native-feasibility-summary.json`](reports/native-feasibility-summary.json)
records counts, gates, null metrics, config, source identities and baseline;
[`reports/native-encoder-smoke-v3.json`](reports/native-encoder-smoke-v3.json)
records every extraction configuration and cache key. Cached audio/vectors and
raw corpus material remain ignored local artifacts. No production pronunciation,
grading, alignment, F0, coaching or UI code changed. No commit, push or deploy.
