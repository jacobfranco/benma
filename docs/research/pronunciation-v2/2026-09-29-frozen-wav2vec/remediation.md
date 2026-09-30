# Bounded corpus remediation

Continuation starts at `5d92c73` on `pronunciation-v2-research`, with a clean working tree. The historical [preflight report](preflight.md) and its original stop evidence remain intact. The user explicitly authorized excluding isolated contradictions and proceeding in the same pass after the corrected readiness gate passes.

**PASS: 495 primary clips, five excluded.** The acquisition manifest was not modified. [clean-corpus-manifest.csv](clean-corpus-manifest.csv) records all 500 originals, inclusion/exclusion, reason, local path, hashes and provenance. [split-manifest.csv](split-manifest.csv) contains only retained primary clips. All 500 files were rechecked against source byte length/SHA-1, local SHA-256 and fresh decoded PCM/tags; all passed. There are no duplicate source/byte/PCM hashes. Original audio remains in the persistent acquisition cache.

## Dispositions

- **commons:3052714 / Zh-wéi.ogg: excluded**, never reassigned. Conflicting speaker, text, date and license, including embedded ShareAlike terms outside the clean pilot policy.
- **All four singleton groups: excluded** from the entire model experiment. This includes `commons:3053212` with its unresolved embedded-license conflict; no repair was attempted. The others are Xudong Yang, Wang Cheng and Jun Da.
- **commons:3052537 / Zh-nǎ.ogg: retained as 哪 / na3 / T3.** Cached primary revision **447926522** explicitly says nǎ and the title/category agree. The embedded spelling `na` supplies no tone and does not contradict T3. Embedded character, speaker, recording date and license agree with the primary record. This resolves the intended lexical reading under the existing label contract; it does not certify perceived tone. No F0, ASR or model output was consulted.

All **326 remaining Shtooka files explicitly identify Wei Gao**. There are **zero contradictory names and zero unknown names**. All have embedded recording date **2006-10-29**, matching cached page dates; all embedded text agrees with manifest text. Both embedded license fields consistently say Creative Commons BY, compatible with the selected CC BY 2.0 France page grant. No additional primary license conflict was found. All other explicit embedded pinyin matches; the one unmarked spelling is resolved above. No residual documentary evidence of mixed voices remains in this cleaned group.

The 326 files jointly credit Wei Gao and Nicolas Vion. Wei Gao's speaker role is explicit; the precise recorder/operator role of Nicolas Vion remains independently unverified. This is a conservative **source/speaker group**, not biometric person-level verification. Native-Mandarin status remains UNKNOWN for every retained file.

## Frozen primary allocation

| Group | Partition | N | T1 | T2 | T3 | T4 |
|---|---|---:|---:|---:|---:|---:|
| shtooka:wei-gao | Train | 326 | 84 | 71 | 81 | 90 |
| CanonNi / Q1431140 | Train | 60 | 15 | 12 | 9 | 24 |
| Levi Highway / Q1573006 | Validation | 49 | 7 | 11 | 14 | 17 |
| Luilui6666 / Q301531 | Final test | 60 | 11 | 15 | 13 | 21 |
| **All primary** | | **495** | **117** | **109** | **117** | **152** |

Train totals: **386**, T1/T2/T3/T4 **99/83/90/114**. Validation **49**; test **60**. Licenses: **326 CC BY 2.0 France + 169 CC0**. No class weighting is warranted or used in the primary experiment.

All readiness gates pass: at least 300 total, at least 50 of each tone, every group at least 40 clips and every group/tone cell at least five clips. Each group maps to exactly one partition. Singletons, the known bad asset and duplicate content are rejected programmatically. This demonstrates zero source-group leakage under the documented grouping; it is not a biometric identity claim or an unseen-word claim.

Manifest SHA-256:

- Original acquisition: `fcdacce34f9894356fa9549b9fb3d06ffb1d4427bed5153f996f9ad736e42b43`.
- All 500 remediation decisions: `591d9a501eb5b79bbdcbcd72123a96e7ba2486082314be8e773f1bd194fb9dc5`.
- Frozen 495-row split: `1ee5ab2d6bbb6739e461c53949d699cef687d8b6e25412717400889f219e6416`.

The earlier bounded 38-item metadata/signal audit and listening list remain evidence of the original preflight. No direct listening was available or performed in either pass. The retained labels are isolated lexical pronunciations, **not listening-audited connected-speech surface-tone gold**.

Exact remediation command:

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/remediate.py \
  --manifest docs/research/pronunciation-v2/2026-09-28-data-feasibility/pilot-manifest.jsonl \
  --cache /home/jacob/.cache/benma/benma-pronunciation-v2-pilot \
  --output docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec
```

Machine counts and readiness evidence: [remediation-summary.json](remediation-summary.json).
