# Experiment 3 fresh-data acquisition and sealing review

All **720 preselected SAIT-EMA clips** were acquired successfully. The panel
contains all 18 qualifying speakers, with 10 targets in each lexical tone per
speaker. No selected ID was replaced or removed. This review accompanies the
exclusive `SEALED_UNOPENED` receipt in the final data directory; `seal.json` is
the authority for the exact sealing time and artifact hashes. No evaluation
has been performed.

## Exact composition

Status is source-declared, using the paper's native-control/L2-learner distinction.
It was not inferred from nationality, name, accent or model performance.

| Stable speaker ID | Source-declared status | T1 | T2 | T3 | T4 | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| sait-ema:A_F001 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:A_M001 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:F001 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:F002 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:F003 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:F004 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:F005 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:M001 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:M002 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:M003 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:M004 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:M005 | NATIVE | 10 | 10 | 10 | 10 | 40 |
| sait-ema:L_F001 | LEARNER | 10 | 10 | 10 | 10 | 40 |
| sait-ema:L_F002 | LEARNER | 10 | 10 | 10 | 10 | 40 |
| sait-ema:L_F003 | LEARNER | 10 | 10 | 10 | 10 | 40 |
| sait-ema:L_M001 | LEARNER | 10 | 10 | 10 | 10 | 40 |
| sait-ema:L_M002 | LEARNER | 10 | 10 | 10 | 10 | 40 |
| sait-ema:L_M003 | LEARNER | 10 | 10 | 10 | 10 | 40 |
| **All speakers** | **12 NATIVE / 6 LEARNER** | **180** | **180** | **180** | **180** | **720** |

The 12 native controls contribute 480 clips and the six learners contribute 240.
These are descriptive groups; neither replaces the full panel. Each speaker's
eligible unique-target inventory was T1/T2/T3/T4 = 161/20/13/21 before the cap.

## Source, audio rights and lexical labels

The source is [SAIT-EMA record 17506802](https://zenodo.org/records/17506802),
DOI 10.5281/zenodo.17506802, concept 17506801. No semantic version is published;
the record ID and exact metadata hashes identify this release. The API records
publication on 2025-11-02 and modification at 2025-12-13T05:14:51.679245+00:00.

The [dataset README](https://zenodo.org/records/17506802/files/README.txt),
sections 4–7, gives the CC BY 4.0 data license, explicitly includes synchronized
audio, defines speaker folders and links prompt numbers to distributed WAVs.
The [paper](https://www.nature.com/articles/s41597-026-07237-9) independently
documents the dataset license and the 12 native controls/six L2 learners.
Its article publication license is separate from the dataset's audio grant.
Every selected row retains attribution, dataset title, DOI/source URL, license
URL and evidence URL. Preserve these notices and disclose changes when sharing
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The Mandarin prompt inventory supplies exact numbered character/pinyin prompts.
The corresponding complete nonempty TextGrid word tier must agree. Labels use
pypinyin 0.55.0, built-in dictionary, `heteronym=True`, `Style.TONE3`, with neutral
tone represented as 5. A target must have exactly one acceptable lexical reading
and tone 1–4. Every alternate reading, including same-tone alternatives, neutral
reading, missing character, multi-character prompt or source/dictionary conflict
is excluded. No pinyin-to-character invention or transcript correction occurs.
The whole distributed monosyllable WAV is retained; no TextGrid boundaries,
cropping, F0, listening or realized-tone quality judgments enter selection.

The metadata audit contains 17,316 candidate rows (962 per speaker), 4,104 eligible
recording IDs before repeated-character deduplication and 3,870 unique targets.
Unequal archive CRC32/byte-size pairs established distinct eligible source bytes
before selection; collisions would have required investigation. Frozen selection
ranks each speaker/tone by SHA256(source_asset_id UTF-8), then ID, and caps at ten.
All qualifying speakers enter. `selection.json` retains the exact original IDs.

## Acquisition, integrity and historical overlap

The continuation reused all 720 completed acquisition receipts and existing WAVs.
No source search was restarted and no verified WAV was downloaded again.
The 18 cached archive indexes, source metadata and selected IDs remain pinned.
Bounded HTTP 206 member ranges avoided downloading 40.62 GB of full archives.
Published full-ZIP MD5 values are retained but **not claimed verified**; exact
member lengths and CRC32 were checked against ZIP metadata, and source SHA-256
and SHA-1 were computed locally. Detailed URLs/ranges/hashes survive in receipts.

All 720 files successfully decode, totaling 204,277,130 source bytes and
2,127.5567708333333 seconds. Their measured source format is mono 48 kHz; the
README describes both 16/48 kHz generally and says 16 kHz in its directory table,
so measured per-file values are retained rather than copying that table.
Each row records duration, native decoded-PCM SHA-256 and whole-waveform mono
16 kHz float32 PCM SHA-256 (`evaluation_pcm_sha256`). The latter uses FFmpeg
options matching the frozen preprocessing decoder, without importing or running
the encoder or its checkpoint normalization. Sealing rechecks every source hash,
CRC and decode result and reproduces every normalized-PCM hash.

There are **zero within-panel duplicates** by source asset ID, source hash,
native decoded PCM, mono-16k decoded PCM, or speaker/character identity.
There are **zero exact historical matches** across 7,983 historical metadata rows
and 700 retained historical audio files. The original 700-file source/native-PCM
audit was preserved and extended with mono-16k hashes after source verification.
Its scope includes the original Experiment 1 corpus, Levi, Luilui, opened 118,
OMPAL and auxiliary/singleton files and manifests, including extant manifest paths
outside the two scanned cache roots. New SAIT audio is excluded from that scan.
Lexical word overlap alone is not treated as contamination. Exact hashes cannot
detect every transformed copy.

Speaker IDs/names were compared with all historical metadata and the explicit
exclusion list: Wei Gao, CanonNi, Levi Highway, Luilui6666, Jouketou, 雲角,
Fake estate, Xudong Yang/wyverald, Wang Cheng, Jun Da and Yue Tan. The finding is
**no known source-identity overlap**. Public pseudonyms cannot establish biological
uniqueness or rule out undisclosed aliases across unrelated datasets.

## Seal and model firewall

The final canonical CSV is sorted by speaker, tone, source-ID SHA-256, then ID;
columns and serialization are deterministic. Its exact SHA-256 is:

`141a9349da2786b822d6bbb109ff726f97b466bdb0f4548c5a7f1a2874b60490`

The selection lock SHA-256 is:

`4199ae7c975d8cd53f1f5d06bc9914799b62c6e4fed8d4db1d83dd9ae660cfc7`

`seal.json` binds counts, selection rule/hash, manifest hash, artifacts, frozen
heads/protocol, exact UTC timestamp and unopened state. `provenance.json` also
binds the data tooling/tests, source evidence and historical audit. Creation
refuses any pre-existing final directory and writes the seal receipt last.
The read-only `verify` stage checks artifacts, canonical bytes, code, local WAV
hashes, exact composition and frozen state.

Neither wav2vec nor either fitted head accessed candidate audio. No embeddings,
model features, predictions, confidence, F0 or listening-based relabeling were
produced. Head files were read only as opaque bytes for hash checks; no arrays
were loaded or refitted. Existing protocol/head hashes and unopened flags remain
unchanged. Raw audio remains Git-ignored; no production change, commit or push.

## Source audit and validation

The bounded 21-source audit is complete: **1 GREEN, 4 YELLOW, 16 RED**.
SAIT-EMA is the sole GREEN source. `sources.md` and `candidate-sources.csv`
preserve every decision, rights finding and unresolved blocker; unknown counts
are not reported as zero. `promising-source-counts.csv` preserves inspected
coverage. No fallback collection packet was created because the public source
satisfies the frozen panel, and no further source hunt is needed for this pass.

The focused data/preflight suite passed **116 tests**, with no skips, including
23 tests for the new data tooling. It covers exact composition, lexical filtering,
historical exclusions and duplicate rejection, deterministic selection/manifest
bytes, acquisition-order/model-field independence, required provenance, actual
raw-audio ignore behavior, reuse without network access, no model imports, and
exclusive seal creation. Ruff format/check and `git diff --check` pass.
Commands and results are in `validation.json`; environment details are in
`environment.md`. Git's diff check covers tracked changes; the added files remain
untracked and have not been staged.

## Recommended next pass (not executed here)

Implement, test on synthetic fixtures, review and lock an evaluation runner
against this exact manifest/seal, both fitted head hashes and the frozen protocol
before opening any predictions. Then, only in that separately authorized pass,
evaluate the unchanged heads once on **all 720 clips / 18 speakers**, using the
unchanged frozen encoder/preprocessing. Do not refit, tune, replace or drop rows.
Report the protocol's pooled and per-speaker metrics, equal-speaker mean balanced
accuracy, tone confusion/error rates and paired correctness/differences; apply
the preregistered promising rule unchanged. Use the paired speaker bootstrap
(10,000 draws, seed 20261002, 95% percentile intervals). Any permitted native/learner
breakdown is descriptive and additional to the full-panel result. Retain earlier
stress/development sets as separate diagnostics only.
