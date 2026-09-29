# Pronunciation V2 zero-cost data-feasibility decision

Inventory snapshot: 2026-09-28; offline completion: 2026-09-29. Work stayed on `pronunciation-v2-research` at `28766bd4608df3321ae55d798c301f269a638e27`. No commit, push, production change, model training, model-weight download, paid service, package installation or volunteer recording occurred. The continuation reused the completed inventory and made no further acquisition requests.

## Decisions

| Decision | Result | Evidence / condition |
|---|---|---|
| A. Zero-cost data-source feasibility | **GO WITH LIMITATIONS** | 516 per-file license/label/speaker-metadata candidates, all four tones, four substantial source/speaker groups. Access throughput, speaker concentration, unknown native-Mandarin status and lexical labels limit the claim. |
| B. Meaningful model training right now | **NO-GO RIGHT NOW** | Only 14 usable files are local. They suffice for a mechanics smoke test, not an informative held-out tone experiment. No model work was performed. |
| C. Training after user-run acquisition | **GO WITH LIMITATIONS**, conditional | At least 300 usable clips from the four substantial groups, at least 50 per tone overall, and each of those groups at least 40 clips with at least five per tone. Confirm speaker roles, spot-audit labels and freeze a speaker-disjoint split before fitting. Completing an arbitrary download count alone is insufficient. |

This is a feasible first falsification experiment: can frozen speech representations carry tone information across these held-out speakers? It cannot establish broad speaker, native-Mandarin, connected-speech or production accuracy.

## Metadata pool versus actual local audio

The completed direct-category inventory has 9,363 unique Commons file pages: 4,126 Lingua Libre-origin and 5,237 other Commons. Of 1,710 single-character candidates with inspected revision evidence, 717 pass the asset-license policy and 516 pass the combined metadata gates. No identical source SHA-1 occurs across the 9,363 files. No inventory was repeated during completion.

| Property | Eligible metadata pool | Acquired pilot |
|---|---:|---:|
| Rows / usable local audio files | 516 candidate rows; local availability not implied | 14 actual files |
| T1 / T2 / T3 / T4 | 118 / 110 / 120 / 168 | 4 / 3 / 5 / 2 |
| Lingua Libre / other Commons | 171 / 345 | 13 / 1 |
| CC0 / CC BY 2.0 France / CC BY 2.0 | 171 / 344 / 1 | 13 / 0 / 1 |
| Metadata speaker/source IDs | 8, only 4 substantial | 6, with 1–4 clips each |
| Explicit native-Mandarin status | UNKNOWN: 516; NATIVE: 0; NON_NATIVE: 0 | UNKNOWN: 14; NATIVE: 0; NON_NATIVE: 0 |
| Actual original audio bytes | Not an acquisition claim | 1,297,498 bytes (1.237 MiB) |

[eligible-metadata.csv](eligible-metadata.csv) is the entire 516-row candidate pool. Its acquisition status explicitly disclaims local availability. [pilot-manifest.jsonl](pilot-manifest.jsonl) contains only downloaded, hash-verified, decoded, accepted audio. Its local paths currently resolve under `/tmp/benma-pronunciation-v2-pilot/audio/`. The remaining **502 candidates are not locally accepted**; offline/cap deferrals are not linguistic or licensing rejections. The acquisition cap is 500 file transfers / 1 GiB total across resumes, so not all 516 can be acquired in this bounded pilot.

All 14 originals match source SHA-1 and byte length, have recorded SHA-256 and decoded PCM hashes, and decode successfully. Signal diagnostics show ordinary levels, zero clipping flags and no exact byte/PCM duplicates. These checks do not certify perceived tone, language, singing or background speech. No Shtooka audio has been acquired yet. The local speaker distribution is CanonNi 4, Levi Highway 4, Luilui6666 3, Wang Cheng 1, Jun Da 1, Xudong Yang 1. The largest local group is 4/14 (28.57%); median is two clips. Six speaker IDs correspond to five recorder IDs, because Yug recorded Wang Cheng and Jun Da.

Historical network acquisition was stopped after repeated Wikimedia HTTP 429 responses, including a full requested 600-second cooldown that yielded only about two more files before renewed throttling. Local recount establishes **14**, replacing the earlier approximate 12. No more cooldown waiting occurred in this continuation. `pilot-summary.json` was regenerated offline; its null stop reason refers to that offline operation and does not erase the observed network limitation.

## Speaker coverage and a provisional split

| Substantial group | Clips | T1 | T2 | T3 | T4 | Share of all 516 | Candidate role |
|---|---:|---:|---:|---:|---:|---:|---|
| Wei Gao source group (`shtooka:wei-gao`) | 343 | 84 | 72 | 81 | 106 | 66.47% | Train |
| CanonNi (`lingualibre:Q1431140`) | 60 | 15 | 12 | 9 | 24 | 11.63% | Train |
| Levi Highway (`lingualibre:Q1573006`) | 49 | 7 | 11 | 14 | 17 | 9.50% | Validation |
| Luilui6666 (`lingualibre:Q301531`) | 60 | 11 | 15 | 13 | 21 | 11.63% | Test |

These four groups supply 512 rows and each covers T1–T4. The remaining four supply one clip each (Wang Cheng T3, Jun Da T3, Yue Tan T3, Xudong Yang T1); they do not establish meaningful additional speaker diversity and do not drive the split. Median clips across all eight groups is 25, versus 54.5 across the four substantial groups. The majority source is 66.47% of the whole pool, so random clip splitting would obscure concentration and invite speaker leakage.

A **provisional** 2-train / 1-validation / 1-test split is feasible: Wei Gao + CanonNi / Levi Highway / Luilui6666, respectively. Full metadata ceilings are 403 / 49 / 60 clips; actual acquired counts will be lower under the cap and any quality rejections. Keep singletons separate. This is not a locked experimental split: first confirm actual retained tone coverage and the Shtooka performer/recorder mapping using embedded tags or equivalent primary provenance. The current Shtooka ID conservatively groups jointly credited source files; it must not be portrayed as an independently verified biometric identity. Recorder and uploader are distinct fields. Avoid splitting one source group into different people based on import accounts.

A single test speaker gives a fragile estimate and the train source is concentrated. Report per-tone and per-speaker results and balance head fitting within the training partition as appropriate. Repeated lexical items across speakers should be disclosed; an unseen-word claim would additionally need text-disjoint evaluation. Do not select layers or hyperparameters on the test speaker.

## Readiness thresholds

| State | Minimum usable acquired audio | Interpretation |
|---|---|---|
| Pipeline smoke test | 8 unique files, at least 2 of each tone, at least 2 speaker IDs | The current 14 satisfy this. Enough to exercise decoding, feature shapes and head-training mechanics; no accuracy claim. |
| Exploratory frozen-wav2vec tone experiment | 300–500 usable files; at least 300 from the four substantial groups; at least 50 of each tone across those groups; each group at least 40 files and at least 5 of each tone | Fits the observed 343/60/49/60 ceilings. This is concentrated rather than perfectly speaker-balanced; all four tone classes and held-out speakers must survive acquisition. |
| Stronger speaker-generalization study | Seek at least 12 substantial speakers, each at least 40 clips and at least 10 of each tone; a possible 6-train / 2-validation / 4-test design | Requires broader sources/recording conditions and documented native-Mandarin holdouts. The current pool cannot satisfy it. Reassess sample size and uncertainty for the chosen claim; these are operational targets, not a power analysis or certification. |

The 300-file gate uses the actual minority-speaker sizes: Levi Highway has only 49 candidates and seven T1s, so losing its coverage cannot be compensated by downloading more Wei Gao. `report.py` emits machine-readable count/coverage readiness in [inventory-summary.json](inventory-summary.json); these flags do not replace provenance and listening review. A balanced 100–200-file subset could support a preliminary debugging probe, but is not the recommended meaningful experiment gate. Do not train a model in this data-feasibility pass.

## Rights, native status and label interpretation

The 516 eligible grants are **171 CC0, 344 CC BY 2.0 France and one CC BY 2.0**. These are per-asset grants with attribution, license and revision links, not project/category assumptions. Some Lingua Libre API short fields say ShareAlike while their inspected license block explicitly offers CC0; that documented option is selected. ShareAlike-only, NC/ND, unsupported public-domain assertions and unresolved grants remain outside the first pilot. Retain CC BY attribution and applicable license terms for reuse. This is a documented research eligibility policy, not blanket clearance of every item in a named collection. Details and primary rights links: [licensing.md](licensing.md).

All 516 native-Mandarin statuses stay **UNKNOWN**. “Native Chinese” is insufficient to establish “native Mandarin”; location, name and perceived voice are not substitutes. These clips can still serve as **open Mandarin pronunciation data** for an exploratory representation probe because the language/pronunciation metadata identifies the intended material. They must not be described as a verified native-Mandarin corpus. Jia is optional later as an independently held-out native-Mandarin sanity test, without head fitting or tuning on her recordings. Her participation is not a prerequisite for the first exploratory run and one person cannot resolve broad generalization.

Labels are conservative **high-confidence lexical pronunciation labels**: isolated single-character material, explicit pinyin compatible with dictionary readings, or a single unambiguous dictionary pronunciation. Ambiguous/polyphonic, neutral/unmarked and multi-syllable material is excluded. `observed_surface_tone` remains null. For citation-style single-syllable recordings, lexical labels are a reasonable first T1–T4 representation-probe target, subject to a stratified listening spot-audit before fitting. They are not listening-audited surface-tone gold, and do not establish connected-speech, sandhi or spontaneous-speech performance. No F0/v1/ASR prediction creates truth.

## Other sources

- **FSI/DLI: YELLOW, deferred.** The inspected original resource-module scan contains rightsholder language inconsistent with assuming mirror public-domain claims clear all audio reuse. No reliable speaker roster/segmentation was obtained; zero audio downloaded. Do not include it in the GREEN pilot.
- **OMPAL: held out.** Verified repository tree: 1,850 WAVs, 49 speaker folders, 82 recordings from three documented native speakers and 1,768 from 46 learners, under CC BY 4.0. Its tone field denotes pronunciation correctness, not T1–T4 identity. Reserve it primarily for separately audited learner/challenge evaluation; no head fitting, calibration or layer selection and no audio acquisition in this pass.
- **Benma historical challenge: mapping unresolved.** Local inspection found 201 audio objects including 120 RIFF/WAV signatures; this does not establish independent utterance counts or the mapping to 67 historical challenge recordings. No DB/export/mutation or wholesale recapture occurred. Resolve mapping later for held-out comparison.

Exact source URLs, repository commit, snapshot provenance and limitations: [sources-audit.md](sources-audit.md), [source-evidence.json](source-evidence.json). Full candidate/rejection breakdown: [inventory.md](inventory.md), [candidate-audit.csv](candidate-audit.csv), [rejected-summary.md](rejected-summary.md).

## Resume outside the agent session

Run exactly from the existing checkout/cache:

```sh
cd /home/jacob/benma
services/api/.venv/bin/python benchmark/pronunciation_v2/pilot.py download \
  --cache /tmp/benma-pronunciation-v2-pilot \
  --output docs/research/pronunciation-v2/2026-09-28-data-feasibility \
  --max-files 500 --max-bytes 1073741824 \
  --request-delay 60 --max-throttles 2
services/api/.venv/bin/python benchmark/pronunciation_v2/report.py \
  --cache /tmp/benma-pronunciation-v2-pilot \
  --output docs/research/pronunciation-v2/2026-09-28-data-feasibility
```

Only `selected.jsonl` assets are fetched. Already downloaded files are locally reverified without fetching again. One request at a time, 60-second interval, full Retry-After, exponential fallback and a global two-throttle stop protect respectful operation; cooldown persists across invocations. Sixty seconds is deliberately conservative after the observed behavior, **not a throughput guarantee**. Do not run concurrent downloaders or an automatic restart loop. Preserve cache, audio, cooldown and budget ledger together; `/tmp` is temporary. Atomic manifest replacement and continued inspection of later cached files after a network stop preserve acquired progress. Caps include previous transfers and partial bytes. See [acquisition.md](acquisition.md) for offline regeneration and diagnostic details.

## Exact next model-pass input and action

After acquisition, regenerate reports and check the **actual** four-group coverage gate, source/speaker provenance, duplicates and a stratified lexical-label listening sample. Retain the manifests, attribution/revision evidence and hash-pinned cache as experiment inputs. Confirm Shtooka speaker/recorder roles before claiming a speaker-disjoint split; defer the experiment if that cannot be resolved. Freeze the provisional train/validation/test membership only then.

Use **HIGH reasoning** for the next model pass. Keep the previously chosen bounded experiment: frozen `facebook/wav2vec2-base`, initial layer 6 with limited layers 4/6/8 comparison on validation, a small linear T1–T4 head, audio-only model features, no ASR text/target leakage and no encoder fine-tuning. Preserve v1 unchanged as the existing baseline (reference `68057aa`); no architecture reopening is needed. OMPAL/Benma challenges and any later Jia recordings remain independent held-outs. Implement and train only in that subsequent authorized model pass after readiness is met.

## Validation and workspace

**31 focused tests passed** in the single final test run after tooling edits (`unittest`, 0.319 seconds). Ruff lint and format checks passed for all four Python files. Offline regeneration revalidated all 14 files. The final artifact audit confirmed 516 unique metadata rows, 14 matching local files with source/content hashes, 1,710 candidate audit rows, snapshot hashes, readiness flags and local Markdown links. The full Benma application suite is intentionally out of scope. All new work is isolated in `benchmark/pronunciation_v2/` and this research directory. Raw audio and large metadata responses remain outside Git. No tracked production file changed.


Created files:

- Tooling: `benchmark/pronunciation_v2/{acquire.py,pilot.py,report.py,test_pilot.py}`.
- Curated reports: `review.md`, `sources-audit.md`, `inventory.md`, `licensing.md`, `rejected-summary.md`, `acquisition.md`.
- Separate manifests: `eligible-metadata.csv`, `pilot-manifest.jsonl`.
- Supporting artifacts: `candidate-audit.csv`, `inventory-summary.json`, `pilot-summary.json`, `source-evidence.json`, `inventory-duplicates.jsonl` (empty because there are no exact source-hash duplicates).

`git diff --stat` is empty because all additions remain untracked; nothing was staged to change that display. Final `git status --short`:

```text
?? benchmark/pronunciation_v2/
?? docs/research/pronunciation-v2/2026-09-28-data-feasibility/
```
