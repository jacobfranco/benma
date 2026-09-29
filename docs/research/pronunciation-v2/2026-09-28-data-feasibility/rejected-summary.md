# Rejected and deferred candidates

The source inventory has **9,363 unique file pages**. The focused one-character metadata audit covers **1,710**. Exactly **717** of those pass the asset-license gate; **516** also pass label/identity metadata gates. Thus **201 GREEN-license candidates fail another gate** (189 dictionary ambiguities; nine unmarked/unresolved pinyin; two metadata/dictionary conflicts; one missing speaker association). The 516 are download candidates, not a claim that 516 recordings were downloaded or listening-audited.

**8,847 inventory pages are rejected/deferred by the conservative initial-pilot selector.** This is not 8,847 definitively unusable recordings. Many are valuable multi-syllable material, broader-language entries or files whose metadata does not match this deliberately narrow selector. Single-character candidates have individual source URLs, revision IDs, licenses, tones where resolvable, eligibility and reasons in [candidate-audit.csv](candidate-audit.csv). Full per-page reasons are retained locally in `/tmp/benma-pronunciation-v2-pilot/rejected.jsonl`.

Primary reasons are mutually exclusive by implementation order and sum to 8,847:

| Primary reason | Pages |
|---|---:|
| ShareAlike/GFDL deferred | 4,674 |
| Not a supported single-character Lingua Libre candidate | 3,259 |
| Multi-syllable description | 569 |
| Ambiguous dictionary reading | 189 |
| Unresolved license restrictions | 79 |
| Insufficient pronunciation metadata | 40 |
| Unknown license or unverified public-domain basis | 19 |
| Unknown/unmarked pronunciation | 9 |
| Non-audio format | 6 |
| File pinyin / dictionary conflict | 2 |
| Unknown speaker association | 1 |

Items may have multiple underlying issues. For example, the all-reasons count includes 447 ambiguous readings, because some also fail licensing. See `rejection_all_reason_counts` in [inventory-summary.json](inventory-summary.json). The primary-order table must not be misread as the complete license distribution; particularly, Lingua Libre phrases stop at the single-character gate and can also carry ShareAlike.

No arbitrary pronunciation is chosen for polyphones. For example, the installed dictionary contains both `ba1` and `ba2` for 八; a Hanzi-only 八 clip fails the singleton rule, while explicit per-file `bā` can resolve the reading if otherwise eligible. Neutral `0/5` and unmarked uncertain syllables never become T1. No source or speaker gets blanket exemptions from these gates.

No exact source-SHA-1 duplicate was found in the union. Nine overlapping category memberships are merged by page ID; Lingua Libre appears only once through its Commons identity. Download-level decode/quality/hash results and eligible-but-unacquired counts are separately reported in [inventory.md](inventory.md), [review.md](review.md) and the local `download-rejected.jsonl`. Network deferral and a download cap are not linguistic or copyright rejections.

Connected speech, music/singing, unverified Chinese varieties and arbitrary educational videos are not accepted as T1–T4 truth. This pass did not attempt forced alignment or use F0/v1 to rescue excluded material.
