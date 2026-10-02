# Validation

No production or shared API module was edited. The completed pass is confined to new
research modules/tests under `benchmark/pronunciation_v2/` and this documentation directory.
The starting tree was clean on `pronunciation-v2-research`, HEAD `2f04fc5`.

## Completed checks

| Check | Result |
| --- | --- |
| New focused probe tests | **25 passed** |
| Connected-speech mapping/schema/replay tests | **69 passed** |
| Benchmark acoustic and acoustic-comparison tests | **6 passed** |
| Relevant API acoustic/pronunciation/perception/contour/evidence tests | **212 passed** |
| Total final test selection | **312 passed**, no failures |
| Source identity | All four original record hashes and source audio hashes unchanged; reviewed audio/perception/acoustics/raw provider evidence equal saved captures |
| Exact saved pitch reuse | Every allowlisted frame field equals its original saved value in all twelve spans; only public timestamps are made crop-relative |
| Packet blinding | All emitted text scanned for focal/control characters, study IDs, target/reading/score fields, reference phones and source paths; none present |
| Artifact generation | 12 PCM16 crops, 36 SVGs, 12 evidence JSONs, local HTML/index, summaries and seal |
| Render checks | Two representative plots rendered locally and visually checked; all SVGs parsed as XML |
| Formant handling | 6 attempted regions, 68 centers, 25 joint-sanity passes; zero accepted region summaries; no new pitch extraction |
| Model provenance | Cached revision/config/processor/weight hashes match prior checkpoint receipt |
| Frozen embeddings | 12 × 768, every crop repeats bitwise, no gradients, unchanged state hashes |
| Initial vs clarified artifacts | All numeric observations unchanged; embeddings bitwise equal; initial artifacts retained |
| Post-seal unblinding | Key joined only after blind observations/interpretation and seal verification; join receipt retained locally |
| Ruff check / format check | Passed on all six new Python files |
| Whitespace | `git diff --check` plus explicit new-file trailing-whitespace/final-newline checks passed |
| Git scope | Only research additions; no staged changes, audio/large artifact additions, commit or push |

No unrelated broad test suite was started, and no hang was observed. This is not a claim
that every repository test passes. Initial lint findings were corrected. The first
embedding `python -m` invocation failed before model loading because the isolated research
environment lacks Pydantic; the direct-script launcher solved that without installing
anything. Transformers emitted the existing checkpoint-config gradient-checkpointing
deprecation warning; inference still ran frozen with no gradients.

The final packet seal SHA-256 is
`cf7b335f21469ac28648036756912be3e337b1aab5676d28d56ae6f75e945cc7`.
Local receipts and hashes establish ordering/integrity for this run, not a public
preregistration or a claim of author blinding to the originally requested cases.

## Test commands

```sh
services/api/.venv/bin/python -m pytest \
  benchmark/pronunciation_v2/test_phonetic_evidence.py \
  benchmark/pronunciation_v2/test_connected_speech.py \
  benchmark/pronunciation_v2/test_connected_replay.py \
  tests/test_acoustics.py tests/test_acoustic_comparisons.py -q

services/api/.venv/bin/python -m pytest \
  services/api/tests/test_acoustic_frontend.py \
  services/api/tests/test_pronunciation_corrections_ownership.py \
  services/api/tests/test_pronunciation_diagnostic.py \
  services/api/tests/test_pronunciation_laboratory.py \
  services/api/tests/test_live_pronunciation.py \
  services/api/tests/test_perceived_speech.py \
  services/api/tests/test_readings_contours.py \
  services/api/tests/test_tone_evidence_region.py \
  services/api/tests/test_upstream_evidence.py -q

.venv/bin/ruff check benchmark/pronunciation_v2/phonetic_*.py \
  benchmark/pronunciation_v2/test_phonetic_evidence.py
.venv/bin/ruff format --check benchmark/pronunciation_v2/phonetic_*.py \
  benchmark/pronunciation_v2/test_phonetic_evidence.py
git diff --check
```

## Offline reproduction

Run from the repository root in the existing environments; do not sync/install packages.
Use a new output directory. Preparation refuses missing captures/audio, hash/evidence
mismatches, missing reviewed v2 timings, or an existing destination. It requires the
previous pass's locally preserved reviewed records; it does not redo mapping.

```sh
audit_dir=/tmp/benma-phonetic-audit-replay
services/api/.venv/bin/python -m benchmark.pronunciation_v2.phonetic_prepare \
  --output "$audit_dir/private"
services/api/.venv/bin/python -m benchmark.pronunciation_v2.phonetic_packet \
  --manifest "$audit_dir/private/acoustic-manifest.json" \
  --output "$audit_dir/blinded"

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  benchmark/pronunciation_v2/.venv/bin/python \
  benchmark/pronunciation_v2/phonetic_embeddings.py \
  --manifest "$audit_dir/private/acoustic-manifest.json" \
  --packet "$audit_dir/blinded" \
  --snapshot /home/jacob/.cache/benma/pronunciation-v2-model/hf/models--facebook--wav2vec2-base/snapshots/0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8 \
  --output "$audit_dir/embeddings"
```

Review and lock the blind packet **before** running the following identity join:

```sh
services/api/.venv/bin/python -m benchmark.pronunciation_v2.phonetic_report \
  --packet "$audit_dir/blinded" \
  --key "$audit_dir/private/unblinding-key.json" \
  --embeddings "$audit_dir/embeddings" \
  --output "$audit_dir/region-results.md" \
  --receipt "$audit_dir/private/unblinding-receipt.json"
```

The optional embedding runner fails cleanly if the local model is absent and cannot
download it. The current post-seal report command expects the embedding receipt from
this completed audit; if embeddings are skipped in another environment, the independent
packet/observations remain usable on their own.

## Limitations of validation

Synthetic test waves check numeric behavior and abstention, not Mandarin correctness.
The real audit has one learner, four recordings, an intentionally selected subset,
no expert boundary/phonetic gold, and no completed listening annotation. Numeric
repeatability does not validate the choice of acoustic window, Burg model or generic
sanity bounds. No per-speaker adaptation, HNR, SNR, new voicing detector, VOT or phone
recognition was attempted. This pass retains existing pitch gaps/branches and cannot
separate genuine unvoiced sound from a tracker/gate miss. The nonzero spectra and
embeddings are evidence availability, not a learned diagnostic capability.
