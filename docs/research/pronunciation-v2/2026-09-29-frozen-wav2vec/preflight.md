# Corpus preflight — stopped before modeling

The acquired corpus is byte-valid but its source/speaker grouping is not reliable enough to freeze the requested experiment. The user's explicit rule applies: **“If evidence suggests multiple actual voices are mixed inside the shtooka:wei-gao group: STOP before training and report that finding.”** No model fitting, feature extraction, dependency installation, or checkpoint download occurred. No files were relabeled, excluded, reassigned, or replaced.

## Integrity and counts

All **500** original files are present under `/home/jacob/.cache/benma/benma-pronunciation-v2-pilot/audio/`. All match source byte length, source SHA-1, local SHA-256, and freshly decoded PCM SHA-256. Re-extracted tags match the existing manifest. Cached source revision metadata reproduces each manifest's text, pinyin, lexical tone, group, license, source hash and revision ID. There are zero duplicate asset IDs, paths, source hashes, file hashes or PCM hashes. No neutral/out-of-range labels, missing paths, schema failures or cached metadata mismatches were found. This verifies faithful acquisition, not that the source page correctly describes its current audio.

| Manifest source group | N | T1 | T2 | T3 | T4 | Proposed role only |
|---|---:|---:|---:|---:|---:|---|
| shtooka:wei-gao | 327 | 84 | 72 | 81 | 90 | Train; grouping conflict |
| CanonNi / Q1431140 | 60 | 15 | 12 | 9 | 24 | Train |
| Levi Highway / Q1573006 | 49 | 7 | 11 | 14 | 17 | Validation |
| Luilui6666 / Q301531 | 60 | 11 | 15 | 13 | 21 | Test |
| Four singletons | 4 | 1 | 0 | 3 | 0 | Auxiliary only |
| All acquired | **500** | **118** | **110** | **120** | **152** | Not a training-clearance claim |

The proposed 387/49/60 primary allocation has disjoint group IDs and leaves four singletons auxiliary. It is **not frozen**: source-level identity evidence contradicts a group assignment. A nominally disjoint set of IDs is not sufficient evidence of valid speaker grouping. No usable-for-training count is certified in this stopped pass.

The older data-feasibility prose still includes its initial 14-file state; the committed final JSON reports and on-disk files establish 500. Neither historical prose nor the existing count-based readiness flags override this new provenance finding.

## Decisive Shtooka conflict

`commons:3052714`, **File:Zh-wéi.ogg**, local `commons-3052714.ogg`, is assigned to `shtooka:wei-gao`, with text 为, pinyin `wei2`, and CC BY 2.0 France. Actual freshly inspected file tags say:

| Field | Actual embedded value |
|---|---|
| SWAC_SPEAK_NAME / ARTIST | Tan |
| COPYRIGHT / SWAC_COLL_COPYRIGHT | (c) 2009 Yue Tan |
| SWAC_SPEAK_GENDER | F |
| SWAC_TECH_DATE | 2009-07-08 |
| SWAC_TEXT / TITLE | 围 |
| SWAC_PRON_PHON | wéi |
| LICENSE / SWAC_COLL_LICENSE | Creative Commons BY-SA 3.0 U.S |

Its source SHA-1 is `79cf7408586572ba9a9aebfa70f3bf6d94777a80`; local SHA-256 is `87b18b2d2187018a3461ef957814ce2a23e30de5a06153023c42fc6ca2853244`. The source snapshot already describes a female voice but credits Wei Gao and Vion Nicolas and retains a 2006 date. All 326 other members of this group explicitly name Wei Gao in `SWAC_SPEAK_NAME`, with 2006 recording metadata. That is positive evidence suggesting mixed actual voices, not merely uncertainty over the recorder role. It is documentary evidence, not a listening or biometric determination.

The [Commons file history](https://commons.wikimedia.org/wiki/File:Zh-w%C3%A9i.ogg), available through indexed primary-page text, records a 2025-09-24 replacement upload motivated by a tone disagreement; a 2018 entry had reverted a version because of a different license. This corroborates an audio-version/description mismatch. Direct page and oldid retrieval failed in this session; the locally cached revision **1238115258** and the hash-matched actual audio are the principal evidence. The uploader's tone claim is not adopted as gold and no historical replacement audio was downloaded.

The text discrepancy is between two characters with the same supplied `wei2` reading; it does not by itself prove the tone is wrong. The embedded ShareAlike grant conflicts with the selected grant and requires provenance review; this report does not adjudicate copyright or assume one tag automatically overrides another grant.

## Wei Gao versus Nicolas Vion

For **326/327** group files, actual `SWAC_SPEAK_NAME=Wei Gao` supports Wei Gao as the voice. Collection-author/copyright fields jointly credit Wei Gao and Vion Nicolas. The representative [Commons chū record](https://commons.wikimedia.org/wiki/File:Zh-ch%C5%AB.ogg) and cached revision **447922193** likewise jointly credit them. Those fields support Nicolas Vion as a credited contributor, but do not independently establish that he operated the recorder for every file. The current `recorder_id` came from a source-specific mapping in `pilot.py`, not an explicit operator field in these tags.

The [Commons Shtooka overview](https://commons.wikimedia.org/wiki/Commons:Shtooka) states that collections have separate licenses. The original Shtooka collection endpoint was unavailable. Do not upgrade the recorder assignment to verified provenance or split the original group across partitions. All native-Mandarin statuses remain **UNKNOWN**.

## Additional review items

- **commons:3053212 / Zh-zhǒng.ogg**, an auxiliary Yue Tan singleton: embedded license also says CC BY-SA 3.0 U.S while the selected page grant is CC BY 2.0 France. Speaker and text tags agree with its manifest. This second licensing discrepancy should be resolved or the file excluded in a subsequent corpus repair.
- **commons:3052537 / Zh-nǎ.ogg**, Wei Gao, 哪 / `na3`: embedded `SWAC_PRON_PHON` is unmarked `na`. The file description supplied the T3 label. This is incomplete corroboration, not affirmative evidence of a different tone. The audit explicitly preserves that distinction.

Full original rows and redecoded evidence are in [provenance-conflicts.json](provenance-conflicts.json). None of these discoveries used F0, V1 output, or ASR.

## Bounded content and signal audit

The [38-item audit list](human-listening-audit.csv) contains the shortest and longest clip in every substantial-group/tone cell (32 selections), all four singletons, and remaining anomalous items. Reviewed text/pinyin/tone combinations and cached provenance for these entries are plausible except for the documented contradictions. All 500 received automatic metadata/hash/decode checks. Metadata and file duration can establish plausibility, not that the recorded utterance perceptually matches its label.

Durations span **0.600–1.650 seconds**. All signals are finite; RMS spans **0.02121–0.25889**, absolute peak **0.12796–0.97743**; every clip has zero samples reaching the inherited clipping proxy of `abs(x)>=0.999`. Maximum low-amplitude-window fraction is **0.63934** on CanonNi's 笨 / `ben4` (0.605 s), which has ordinary nonzero speech energy. No waveform-integrity rejection occurred. This is signal-level inspection, not an inference of perceptual quality or correct pronunciation.

**Direct listening was not available and none was performed.** Every audit row says `NOT_LISTENED` and retains the exact local path for later human review. Labels remain conservative isolated lexical-pronunciation labels, not listening-audited surface-tone gold. No claim about connected speech or verified native-Mandarin speakers follows.

## Reproduction and stop behavior

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/preflight.py \
  --manifest docs/research/pronunciation-v2/2026-09-28-data-feasibility/pilot-manifest.jsonl \
  --cache /home/jacob/.cache/benma/benma-pronunciation-v2-pilot \
  --output docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec
```

Expected exit status: **2**, with `STOP_BEFORE_TRAINING`. The script reads the corpus/cache and writes only these audit artifacts. Its conservative diagnostics are not a general licensing adjudicator or a substitute for listening. Deterministic ordering uses asset ID; no random seed is needed for this audit. The manifest hash is `fcdacce34f9894356fa9549b9fb3d06ffb1d4427bed5153f996f9ad736e42b43`; the source-evidence snapshot hash is `31bd676c452e2893a33a4b1ed48e4dad704d669fd0f9b04b4cd6d6a7c505f46d`.

Full machine-readable results: [preflight-summary.json](preflight-summary.json), [corpus-diagnostics.csv](corpus-diagnostics.csv). The CSV's partition field is explicitly **proposed_partition_only**, not a locked split manifest.
