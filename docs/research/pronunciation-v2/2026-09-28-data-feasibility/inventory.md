# Actual metadata inventory

Snapshot date: 2026-09-28. The API snapshot covers six named direct categories and **9,363 unique Commons file pages**, including non-audio and non-Mandarin discovery results. Scope and primary links: [sources-audit.md](sources-audit.md). Machine counts: [inventory-summary.json](inventory-summary.json). Do not add the Lingua Libre subset to the Commons union.

| Stage | Other Commons | Lingua Libre-origin Commons | Total |
|---|---:|---:|---:|
| Per-file metadata inspected | 5,237 | 4,126 | 9,363 |
| Focused single-character candidates / wikitext revisions inspected | 843 | 867 | 1,710 |
| GREEN asset-license candidates in that focused audit | 357 | 360 | 717 |
| Eligible after label and speaker metadata gates | 345 | 171 | 516 |
| Eligible T1 | 85 | 33 | 118 |
| Eligible T2 | 72 | 38 | 110 |
| Eligible T3 | 82 | 38 | 120 |
| Eligible T4 | 106 | 62 | 168 |

The complete accepted pool is [eligible-metadata.csv](eligible-metadata.csv), with 516 rows. “Eligible” above is a **metadata result**, before download/decode checks. It does not mean native-verified or observed-tone gold. GREEN refers to the audio grant; UNKNOWN native status is a separate disclosed limitation.

## Per-file API license distribution

| API short license | Other Commons | Lingua Libre |
|---|---:|---:|
| CC BY-SA 3.0 US | 3,598 | 0 |
| CC BY-SA 4.0 | 77 | 2,980 |
| CC0 | 18 | 1,145 |
| CC BY 2.0 France | 926 | 0 |
| CC BY-SA 3.0 | 463 | 0 |
| Public domain | 96 | 0 |
| CC BY-SA 2.0 UK | 20 | 0 |
| CC BY 2.5 | 19 | 0 |
| CC BY 3.0 | 7 | 0 |
| CC BY-SA 2.5 | 6 | 0 |
| GFDL | 3 | 0 |
| CC BY 2.0 UK | 1 | 0 |
| CC BY 2.0 | 1 | 0 |
| CC BY 4.0 | 0 | 1 |
| FAL | 1 | 0 |
| Missing | 1 | 0 |

These are **API short fields**, not resolved grants. For 130 single-character Lingua Libre candidates the inspected license block supplies an optional CC0 grant despite a ShareAlike short field. Sixty of those pass the subsequent pronunciation gates. No assertion about optional grants on uninspected phrase license blocks is made. The eligible 516 use 171 CC0, 344 CC BY 2.0 France and one CC BY 2.0.

## Speaker coverage before download

| Speaker/group ID | Display name | Eligible clips | T1 | T2 | T3 | T4 |
|---|---|---:|---:|---:|---:|---:|
| shtooka:wei-gao | Wei Gao source group | 343 | 84 | 72 | 81 | 106 |
| lingualibre:Q1431140 | CanonNi | 60 | 15 | 12 | 9 | 24 |
| lingualibre:Q301531 | Luilui6666 | 60 | 11 | 15 | 13 | 21 |
| lingualibre:Q1573006 | Levi Highway | 49 | 7 | 11 | 14 | 17 |
| lingualibre:Q1832 | Wang Cheng | 1 | 0 | 0 | 1 | 0 |
| lingualibre:Q1845 | Jun Da | 1 | 0 | 0 | 1 | 0 |
| shtooka:yue-tan | Yue Tan source group | 1 | 0 | 0 | 1 | 0 |
| commons:wyverald | Xudong Yang | 1 | 1 | 0 | 0 | 0 |

There are eight proposed speaker groups but only **four with all-tone coverage**. Shtooka grouping conservatively keeps all matching credited-source recordings together, instead of splitting its import bots into fictitious speakers; exact performer/recorder roles require corroboration from embedded metadata when acquired. Do not describe an uploader count as human speaker count. The broad inventory has 128 distinct uploader accounts overall (109 non-LL; 21 LL, with overlaps). Lingua Libre file metadata exposes 23 speaker display names, including 20 legacy profile IDs across 3,869 files and 257 files without that old profile-link form; display names are not a verified census of distinct people. The accepted Lingua Libre candidates use five explicit stable profile IDs, with recorder identity separate.

At the metadata stage all 516 have native status UNKNOWN. Some contributors declare native Chinese without Mandarin specificity; no location/ethnicity/voice inference fills the gap. Largest metadata group: 343/516 = 66.47%. Tone maximum/minimum is 168/110 = 1.53; all tones exceed 100, but speaker/source concentration is substantial.

## Actual downloaded pilot

At completion: **14 files, 1,297,498 original audio bytes**, T1/T2/T3/T4 = **4/3/5/2**, six metadata speaker IDs, all native-Mandarin UNKNOWN. CanonNi and Levi Highway contribute four each; Luilui6666 contributes three; Wang Cheng, Jun Da and Xudong Yang contribute one each. All pass source size/SHA-1, SHA-256 and decoding checks, with zero clipping flags and no exact audio/PCM duplicates. Throttling left 502 eligible candidates outside the local pilot; those are not label/license rejections.

The authoritative **downloaded**, decoded and accepted counts, bytes, class distribution, speaker distribution and native-status distribution are in [pilot-summary.json](pilot-summary.json) and [review.md](review.md). `pilot-manifest.jsonl` has exactly one row per accepted local file, with canonical URL, file hash, explicit label provenance and signal diagnostics. Those counts must not be replaced by the larger 516-row metadata pool.

Exact duplicate checks use the unique Commons ID first, source SHA-1 for inventory audio, and SHA-256/decoded-PCM hashes after acquisition. No source-hash duplicate was found in the 9,363-page inventory. Different takes of the same normalized text by one speaker are repetitions, not automatically exact duplicates. No expensive acoustic fingerprinting was performed.
