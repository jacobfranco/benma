# Learner QA acceptance, frozen release and transfer evaluation — 2026-10-19

**MIXED TRANSFER, provisionally.** The expanded model has useful signal but substantial disagreement with expectations and the pilot. Legitimate nucleus/coda pooling does not demonstrate a general material improvement over the earlier whole-syllable probe. A separate blinded realized-tone annotation stage is necessary before judging acoustic correctness or product utility. No model was trained, adapted or reselected.
This report supersedes the earlier pending-QA handoff reports. The finishing continuation reuses all completed release, inference, comparison and reproduction artifacts; it performs no new encoder extraction, native-corpus work or model selection.

The completed learner QA was accepted from the draft using substantive judgments as authoritative and playback telemetry as provenance-only.

**Ingestion and acceptance.** Schema, packet hash, all 123 unique item IDs, item hashes, unit/source identity, reviewer Jacob, 123 whole judgments, 123 tone judgments, and notes for every non-PASS were validated. Zero substantive decisions are missing. Raw draft SHA-256: `64621bed541ddf561c66c0a06ad1b83a1671015f4ec48b919dffa5757afd9908`. The byte-identical draft and original developer request are preserved in the release. All note strings and recorded flags remain unchanged.

| Telemetry false | Count |
| --- | --- |
| context | 86 |
| heard_all | 86 |
| tone | 3 |
| whole | 16 |

`accepted_by_developer_attestation = true`; `playback_telemetry_complete = false`. Every heard_all=false item also has context=false; whole=false and tone=false overlap that set. Context was optional in actual use, and whole/tone telemetry did not reliably register. No missing playback event is inferred. No flag excludes an evaluation unit. The research validator and new research review page require reviewer, whole decision, tone decision, and non-PASS notes. Missing-field errors identify the exact field and item. The original reviewed page is preserved; the updated page is under `data/generated/learner-transfer-v1-20261019/review-with-optional-telemetry/qa/index.html`. Production UI is unchanged.

| Whole decision | Count |
| --- | --- |
| PASS | 102 |
| START ISSUE | 7 |
| END ISSUE | 2 |
| BOTH | 9 |
| WRONG UNIT | 3 |

| Tone-bearing decision | Count |
| --- | --- |
| PASS | 102 |
| TOO LITTLE MATERIAL | 17 |
| WRONG UNIT | 3 |
| CONTAMINATED | 1 |
| CLIPPED | 0 |

**Adjudication and alignment audit.** 21 whole non-PASS and 21 tone non-PASS produce 22 unique units. Q037 (不) has a whole onset objection and tone PASS: PASS_AS_IS. Q073 (去) has whole PASS and tone TOO LITTLE MATERIAL: QUARANTINE_UNIT. All 21 tone non-PASS units are quarantined. Of 32 natural candidates, **17 are implicated**, including Q037; 16 are quarantined and 16 accepted. Automatic flags are review evidence, not automatic exclusions. No timestamps or source clips were changed.

**Systematic bug found: no demonstrated general defect. Repaired: 0.** All 123 saved units reconstruct from existing TextGrids with exact word/phone ownership, nested spans, and nucleus/coda projection; all 369 clips equal source samples. This checks representation integrity, not acoustic correctness of forced alignment. The high natural quarantine rate and wrong-unit judgments show substantial crop usability problems. Their cause remains unresolved between alignment limitations and learner production; no general correction is established. Short spans do not prove a bug, and no span was widened to preserve N. No re-review packet is needed because no crop changed.

**Full 22-unit adjudication inventory.** Labels are intended lexical / expected surface; unknown/unresolved is not a realized-tone judgment. Notes below are the developer's original strings; the immutable JSONL preserves exact whitespace. Durations are milliseconds.

| QA | Source / take | Phrase | Target / pinyin | Intended / contextual | Provenance | Whole / tone decision | Developer note (verbatim) | Automatic flags | Whole / tone ms | Adjudication |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q007 | 39e33220c5dec271b192f561 / S02 | 我昨天晚上跟朋友去吃饭了。 | 吃 / chi1 | T1 / T1 | PRIMARY_NATURAL_CANDIDATE | END ISSUE / TOO LITTLE MATERIAL | The whole target is only the "ch" sound.  The tone bearing target might be technically acceptable as far as the result it would produce, but i think its short enough to not inspire confidence. | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading | 210 / 30 | QUARANTINE_UNIT |
| Q013 | 8ad8f3aeeaf7e24bddf0a052 / bb27924c | 我想买这个 | 个 / ge4 | unknown/unresolved / neutral | UNKNOWN_PROVENANCE | BOTH / TOO LITTLE MATERIAL | Pretty much unusable.  Too short to meaningfully deduce.  The recording quality is bad, but still clear enough that its clippable.   | experimental_final_under_60ms | 60 / 30 | QUARANTINE_UNIT |
| Q014 | 4cf712ee935667d1ab00dd9f / S01 | 今天天气不错，我们出去走走吧。 | 气 / qi4 | T4 / T4 | PRIMARY_NATURAL_CANDIDATE | END ISSUE / TOO LITTLE MATERIAL | The whole target is mostly the "q".  There is little vowel.  As a result, the tone bearing target seems unusable.   | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading | 130 / 30 | QUARANTINE_UNIT |
| Q016 | 983caebc345dff8da92ef921 / d7b27845 | 我想买这个 | 个 / ge4 | unknown/unresolved / neutral | UNKNOWN_PROVENANCE | BOTH / TOO LITTLE MATERIAL | Whole target is like the throaty part of the "g" only, not even the full "g" sound, much less the "e".  Tone bearing target therefore is really nothing usable.   | experimental_final_under_60ms | 120 / 30 | QUARANTINE_UNIT |
| Q037 | 4cf712ee935667d1ab00dd9f / S01 | 今天天气不错，我们出去走走吧。 | 不 / bu4 | T4 / T2 | PRIMARY_NATURAL_CANDIDATE | START ISSUE / PASS | This is difficult, but i think the "whole target" needs a little more of the "b".  This was a really quick and soft "bu", so the "tone-bearing target" might be all that the system could possibly get from this, so I mark it a pass.   | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading | 70 / 30 | PASS_AS_IS |
| Q040 | 4cf712ee935667d1ab00dd9f / S01 | 今天天气不错，我们出去走走吧。 | 走 / zou3 | T3 / neutral | PRIMARY_NATURAL_CANDIDATE | START ISSUE / TOO LITTLE MATERIAL | The "whole target" for this one might be better for the tone bearing target.  The actual whole target should have included more of the "z" sound.   | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading; implausible_read_unit_duration | 60 / 30 | QUARANTINE_UNIT |
| Q045 | 4cf712ee935667d1ab00dd9f / S01 | 今天天气不错，我们出去走走吧。 | 今 / jin1 | T1 / T1 | PRIMARY_NATURAL_CANDIDATE | BOTH / TOO LITTLE MATERIAL | "Whole target" doesn't contain the "j" or "n", and the "i" is barely even noticeable either.  And the tone-bearing target reflects that as well.   | historical_ASR_disagrees_with_documented_reading | 150 / 120 | QUARANTINE_UNIT |
| Q054 | 39e33220c5dec271b192f561 / S02 | 我昨天晚上跟朋友去吃饭了。 | 昨 / zuo2 | T2 / T2 | PRIMARY_NATURAL_CANDIDATE | START ISSUE / TOO LITTLE MATERIAL | This is very minor I think, but the whole target could use a little more "z", and the tone-bearing target needs to retain a little more material.  But otherwise this would be borderline pass.   | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading | 180 / 40 | QUARANTINE_UNIT |
| Q057 | 0b44eac1332ea0859ac54d67 / S03 | 你想买哪种水果？ | 哪 / na3 | T3 / unknown/unresolved | PRIMARY_NATURAL_CANDIDATE | BOTH / TOO LITTLE MATERIAL | The context sounds like "mai", not "na".  Then, both the whole target and tone bearing target are really unidentifiable at all.   | experimental_final_under_60ms; implausible_read_unit_duration | 60 / 30 | QUARANTINE_UNIT |
| Q062 | 4cf712ee935667d1ab00dd9f / S01 | 今天天气不错，我们出去走走吧。 | 去 / qu4 | T4 / T4 | PRIMARY_NATURAL_CANDIDATE | BOTH / TOO LITTLE MATERIAL | The "whole target" is "chu qu", not just "qu".  Then the tone-bearing target just sounds like a very short white noise, probably more of a consontant sound that a vowel sound too.   | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading | 490 / 30 | QUARANTINE_UNIT |
| Q071 | 0b44eac1332ea0859ac54d67 / S03 | 你想买哪种水果？ | 果 / guo3 | T3 / T3 | PRIMARY_NATURAL_CANDIDATE | BOTH / TOO LITTLE MATERIAL | the "whole target" is like the throaty "g" part and no actual "g", as well as no vowel.  the "tone-bearing target" also has the same issue.   | experimental_final_under_60ms | 140 / 40 | QUARANTINE_UNIT |
| Q073 | e6126f9dcaee765c29a5b499 / S13 | 我要去广州。 | 去 / qu4 | T4 / T4 | DOCUMENTED_DIAGNOSTIC | PASS / TOO LITTLE MATERIAL | The tone bearing target might be correct, but it still feels like it has a little less material than it should.   | experimental_final_under_60ms | 310 / 40 | QUARANTINE_UNIT |
| Q081 | 0b44eac1332ea0859ac54d67 / S03 | 你想买哪种水果？ | 你 / ni3 | T3 / unknown/unresolved | PRIMARY_NATURAL_CANDIDATE | START ISSUE / TOO LITTLE MATERIAL | We do not get enough "n" at the beginning of the whole target.  The "whole target" might have been an acceptable "tone-bearing target", but the real tone bearing target is too short as a result. | experimental_final_under_60ms; implausible_read_unit_duration | 60 / 30 | QUARANTINE_UNIT |
| Q086 | 4cf712ee935667d1ab00dd9f / S01 | 今天天气不错，我们出去走走吧。 | 们 / men5 | neutral / neutral | PRIMARY_NATURAL_CANDIDATE | BOTH / TOO LITTLE MATERIAL | Just not clipped initially correct, only a short segment of audio, i cant tell if its the "m" or the "n", but its not enough.   | historical_ASR_disagrees_with_documented_reading | 90 / 60 | QUARANTINE_UNIT |
| Q090 | 39e33220c5dec271b192f561 / S02 | 我昨天晚上跟朋友去吃饭了。 | 友 / you3 | T3 / neutral | PRIMARY_NATURAL_CANDIDATE | BOTH / TOO LITTLE MATERIAL | We just don't get enough of the "y" for the "whole target", so both targets seem to not carry enough info.   | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading | 60 / 30 | QUARANTINE_UNIT |
| Q094 | 39e33220c5dec271b192f561 / S02 | 我昨天晚上跟朋友去吃饭了。 | 上 / shang4 | T4 / neutral | PRIMARY_NATURAL_CANDIDATE | BOTH / TOO LITTLE MATERIAL | I think this is technically acceptable, but i would like for there to be more "s" and "g" for the whole target, and the tone bearing target is a little truncated as a result.   | historical_ASR_disagrees_with_documented_reading | 210 / 70 | QUARANTINE_UNIT |
| Q095 | 4966e43af7d8a3fb1e682966 / 89cee47e | 我想买这个 | 个 / ge4 | unknown/unresolved / neutral | UNKNOWN_PROVENANCE | START ISSUE / TOO LITTLE MATERIAL | We don't get enough of the "g".  The "whole target" here might have been acceptable for "tone-bearing target".   | experimental_final_under_60ms | 60 / 30 | QUARANTINE_UNIT |
| Q105 | 1719cb43aa6532d8b7e0b17e / a5acd04c | 我有一个苹果 | 一 / yi2 | unknown/unresolved / T2 | UNKNOWN_PROVENANCE | START ISSUE / CONTAMINATED | I think we get a little noticeable contamination at the beginning to where it really doesn't feel like a "yi".   | none | 280 / 280 | QUARANTINE_UNIT |
| Q107 | 39e33220c5dec271b192f561 / S02 | 我昨天晚上跟朋友去吃饭了。 | 朋 / peng2 | T2 / T2 | PRIMARY_NATURAL_CANDIDATE | WRONG UNIT / WRONG UNIT | I don't think its even measuring peng here, I think it might be "you".  Regardless, it doesn't sound right for both.   | historical_ASR_disagrees_with_documented_reading | 90 / 60 | QUARANTINE_UNIT |
| Q111 | 39e33220c5dec271b192f561 / S02 | 我昨天晚上跟朋友去吃饭了。 | 了 / le5 | neutral / neutral | PRIMARY_NATURAL_CANDIDATE | WRONG UNIT / WRONG UNIT | i'm pretty sure this is like "fan le" in the context.  and the whole target feels more like fan.  and the tone bearing target feels wrong as a result.   | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading | 80 / 50 | QUARANTINE_UNIT |
| Q121 | 39e33220c5dec271b192f561 / S02 | 我昨天晚上跟朋友去吃饭了。 | 饭 / fan4 | T4 / T4 | PRIMARY_NATURAL_CANDIDATE | START ISSUE / TOO LITTLE MATERIAL | i dont think we clearly clip it right.  its more like "ifa" from "chifan" basically.  i would still say the tone bearing target could be correct but its too little | historical_ASR_disagrees_with_documented_reading | 310 / 60 | QUARANTINE_UNIT |
| Q122 | 4cf712ee935667d1ab00dd9f / S01 | 今天天气不错，我们出去走走吧。 | 出 / chu1 | T1 / T1 | PRIMARY_NATURAL_CANDIDATE | WRONG UNIT / WRONG UNIT | The context clearly sounds like "women ch".  So both targets seem unusable.   | experimental_final_under_60ms; historical_ASR_disagrees_with_documented_reading | 60 / 30 | QUARANTINE_UNIT |

**Frozen sets.**

| Set | Candidates | Accepted | Quarantined |
| --- | --- | --- | --- |
| diagnostic | 12 | 11 | 1 |
| primary | 32 | 16 | 16 |
| unknown | 79 | 75 | 4 |

Release: `benma-learner-natural-v1-20261019`. Manifest SHA-256: `8024a51df91e60b9e336189cd9b04dfbf2d5d8c530fd0656778c731e1306f4ae`. Write-once creation, read-only artifact files, a manifest inventory and per-file hash checks enforce release integrity. The manifest covers source hashes, original spans, context, take provenance, labels, raw review, attestation, all adjudications and quarantines. Its three sets are disjoint; historical-special-cases.jsonl is a labeled view of supplemental records, not extra independent data. All six short 我想买 recordings retain UNKNOWN_PROVENANCE. Unknown human identity/intent is not upgraded. Controls remain excluded.

**Frozen inference.** Expanded AISHELL-3 Chinese HuBERT and the original pilot: frozen encoder, context input, layer 9, owned nucleus/coda frame-center mean, balanced logistic regression C=0.1. The existing encoder preprocessing and 200-sample edge padding are unchanged. Text, expected labels, QA notes and provenance never enter the encoder. Primary results were sealed before diagnostic/unknown inference or representation comparisons. Four-way outputs do not model neutral tone. All confidence values are maximum classifier probabilities, not validated learner calibration. Frozen deterministic Benma uses the unchanged Praat analyzer and acoustic-family functions on accepted whole spans; it can abstain. These are fresh research acoustic outputs, not production grading or historical saved crops.

| Model | SHA-256 |
| --- | --- |
| expanded | b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b |
| pilot | c20cc46ed715ce5ed1f3a76f405014069f4a98c0b9e6e467ce28635b4df725d9 |

**Every accepted primary-natural syllable.** Take IDs and phrases are mapped in the next table; # is the original one-based syllable position, so quarantined gaps remain visible. Probabilities are displayed to six decimals; full precision is in primary/predictions.jsonl. No disagreement is removed.

| QA / unit ID | Take / # | Target / tone-stripped pinyin | Lexical / surface | Whole / tone ms | P(T1) | P(T2) | P(T3) | P(T4) | Expanded / confidence | Pilot / confidence | Deterministic / reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q100 / learner:4cf712ee935667d1ab00dd9f:1 | S01 / 2 | 天 / tian | T1 / T1 | 250 / 100 | 0.004553 | 0.476921 | 0.475556 | 0.042970 | T2 / 0.476921 | T4 / 0.766571 | ABSTAIN / missing_critical_support |
| Q051 / learner:4cf712ee935667d1ab00dd9f:2 | S01 / 3 | 天 / tian | T1 / T1 | 250 / 90 | 0.000084 | 0.000112 | 0.026031 | 0.973774 | T4 / 0.973774 | T4 / 0.975817 | ABSTAIN / missing_critical_support |
| Q037 / learner:4cf712ee935667d1ab00dd9f:4 | S01 / 5 | 不 / bu | T4 / T2 | 70 / 30 | 0.000002 | 0.994593 | 0.000369 | 0.005037 | T2 / 0.994593 | T4 / 0.576046 | ABSTAIN / insufficient_support |
| Q027 / learner:4cf712ee935667d1ab00dd9f:5 | S01 / 6 | 错 / cuo | T4 / T4 | 370 / 100 | 0.008315 | 0.007965 | 0.090925 | 0.892794 | T4 / 0.892794 | T4 / 0.740837 | ABSTAIN / insufficient_support |
| Q065 / learner:4cf712ee935667d1ab00dd9f:6 | S01 / 7 | 我 / wo | T3 / T3 | 60 / 20 | 0.101601 | 0.876853 | 0.021542 | 0.000004 | T2 / 0.876853 | T3 / 0.936586 | ABSTAIN / insufficient_support |
| Q047 / learner:4cf712ee935667d1ab00dd9f:10 | S01 / 11 | 走 / zou | T3 / unknown/unresolved | 110 / 60 | 0.600346 | 0.053253 | 0.296591 | 0.049810 | T1 / 0.600346 | T1 / 0.595001 | ABSTAIN / insufficient_support |
| Q064 / learner:4cf712ee935667d1ab00dd9f:12 | S01 / 13 | 吧 / ba | neutral / neutral | 200 / 110 | 0.347255 | 0.005802 | 0.623949 | 0.022993 | T3 / 0.623949 | T3 / 0.561201 | ABSTAIN / insufficient_support |
| Q031 / learner:39e33220c5dec271b192f561:0 | S02 / 1 | 我 / wo | T3 / T3 | 170 / 60 | 0.000383 | 0.006312 | 0.989542 | 0.003763 | T3 / 0.989542 | T3 / 0.981584 | T4 / best_fit |
| Q092 / learner:39e33220c5dec271b192f561:2 | S02 / 3 | 天 / tian | T1 / T1 | 370 / 160 | 0.000926 | 0.893514 | 0.104029 | 0.001532 | T2 / 0.893514 | T1 / 0.427414 | ABSTAIN / insufficient_support |
| Q053 / learner:39e33220c5dec271b192f561:3 | S02 / 4 | 晚 / wan | T3 / T3 | 180 / 110 | 0.000180 | 0.732457 | 0.260991 | 0.006372 | T2 / 0.732457 | T3 / 0.618255 | ABSTAIN / insufficient_support |
| Q091 / learner:39e33220c5dec271b192f561:5 | S02 / 6 | 跟 / gen | T1 / T1 | 130 / 60 | 0.965304 | 0.033194 | 0.000977 | 0.000526 | T1 / 0.965304 | T1 / 0.945347 | ABSTAIN / insufficient_support |
| Q006 / learner:39e33220c5dec271b192f561:8 | S02 / 9 | 去 / qu | T4 / T4 | 230 / 80 | 0.050056 | 0.000035 | 0.014767 | 0.935141 | T4 / 0.935141 | T4 / 0.986245 | ABSTAIN / insufficient_support |
| Q063 / learner:0b44eac1332ea0859ac54d67:1 | S03 / 2 | 想 / xiang | T3 / unknown/unresolved | 290 / 120 | 0.000000 | 0.000290 | 0.999709 | 0.000000 | T3 / 0.999709 | T3 / 0.989959 | ABSTAIN / missing_critical_support |
| Q028 / learner:0b44eac1332ea0859ac54d67:2 | S03 / 3 | 买 / mai | T3 / unknown/unresolved | 260 / 230 | 0.008010 | 0.610345 | 0.381110 | 0.000534 | T2 / 0.610345 | T3 / 0.713496 | ABSTAIN / insufficient_support |
| Q033 / learner:0b44eac1332ea0859ac54d67:4 | S03 / 5 | 种 / zhong | T3 / unknown/unresolved | 160 / 130 | 0.001052 | 0.983803 | 0.000021 | 0.015124 | T2 / 0.983803 | T1 / 0.654064 | T2 / best_fit |
| Q118 / learner:0b44eac1332ea0859ac54d67:5 | S03 / 6 | 水 / shui | T3 / unknown/unresolved | 300 / 90 | 0.797205 | 0.202794 | 0.000001 | 0.000001 | T1 / 0.797205 | T1 / 0.988875 | ABSTAIN / insufficient_support |

**DESCRIPTIVE primary agreement.** Of 16 accepted units, intended lexical labels have 15 numbered tones and one neutral. Expected surface labels have 10 resolved numbered tones, one neutral and five unresolved T3-chain cases. Neutral and unresolved labels are reported but excluded from numbered-tone agreement denominators. All realized acoustic labels remain UNKNOWN.

| Model | Lexical agreement | Expected-surface agreement | Numbered outputs / abstentions |
| --- | --- | --- | --- |
| deterministic | 0/2 covered; 15 resolved | 0/1 covered; 10 resolved | 2 / 14 |
| expanded | 5/15 covered; 15 resolved | 5/10 covered; 10 resolved | 16 / 0 |
| pilot | 10/15 covered; 15 resolved | 7/10 covered; 10 resolved | 16 / 0 |

Expanded vs pilot: 9/16 agree (56.25%). Expanded vs deterministic: 1/2 jointly covered agree; pilot vs deterministic: 0/2. Deterministic has 0/2 lexical matches and 0/1 expected surface matches among covered units; coverage is only 2/16. Abstentions are not counted as numbered-tone errors. None of these quantities measures realized-tone accuracy.

**Each natural take.** Sequences include accepted units in source order only.

| Take / source ID | Phrase | Pre-QA | Accepted / quarantined | Resolved expected numbered | Accepted characters | Expanded sequence | Pilot sequence | Deterministic sequence | Expanded expected agreement | Pilot expected agreement | Expanded/pilot agreement | Mean confidence expanded / pilot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 / 4cf712ee935667d1ab00dd9f | 今天天气不错，我们出去走走吧。 | 13 | 7 / 6 | 5 | 天 天 不 错 我 走 吧 | T2 T4 T2 T4 T2 T1 T3 | T4 T4 T4 T4 T3 T1 T3 | — — — — — — — | 2/5 covered; 5 resolved | 2/5 covered; 5 resolved | 4/7 | 0.777 / 0.736 |
| S02 / 39e33220c5dec271b192f561 | 我昨天晚上跟朋友去吃饭了。 | 12 | 5 / 7 | 5 | 我 天 晚 跟 去 | T3 T2 T2 T1 T4 | T3 T1 T3 T1 T4 | T4 — — — — | 3/5 covered; 5 resolved | 5/5 covered; 5 resolved | 3/5 | 0.903 / 0.792 |
| S03 / 0b44eac1332ea0859ac54d67 | 你想买哪种水果？ | 7 | 4 / 3 | 0 | 想 买 种 水 | T3 T2 T2 T1 | T3 T3 T1 T1 | — — T2 — | N/A; 0 resolved | N/A; 0 resolved | 2/4 | 0.848 / 0.837 |

S01: both models disagree with expected T1 for both accepted 天 syllables. Expanded 不→T2 agrees with the contextual 不-before-T4 expectation; pilot 不→T4 agrees with lexical tone. Expanded 我→T2 differs from pilot T3. The accepted 30 ms 不 remains supported by human tone PASS, not by its high model confidence. Its whole onset objection remains recorded. S02: both models produce 我→T3 while frozen deterministic returns T4; expanded 天→T2 and 晚→T2 disagree with expected T1/T3, while pilot matches those expectations. S03: none of its four accepted expected surface tones is resolved because prosodic T3 grouping was not adjudicated. Expected-tone agreement is therefore N/A, not zero. 种 differs between expanded T2 (also deterministic T2) and pilot T1; 水 is T1 in both learned models despite lexical T3. These require realized-tone evidence.

**Confidence.**

| Model | Min / median / mean / max | [.25,.5) / [.5,.8) / [.8,.9) / [.9,1] | Count ≥ .80 / ≥ .90 | Expected disagreements at confidence ≥ .8 |
| --- | --- | --- | --- | --- |
| expanded | 0.477 / 0.893 / 0.834 / 1.000 | 1 / 5 / 3 / 7 | 10 / 7 | 3 |
| pilot | 0.427 / 0.754 / 0.779 / 0.990 | 1 / 8 / 0 / 7 | 7 / 7 | 1 |

Expanded confidence is higher despite lower expected-tone agreement. Three expanded expected-numbered disagreements have confidence ≥0.8 (S01 second 天 and 我; S02 天), versus one for the pilot (S01 second 天). These are disagreements, not established errors. No confidence threshold was fitted. Deterministic family supports are not probabilities.

**Confidence on expected-tone disagreements, separately.**

| Model | Subset | N | Mean | Median | Min | Max | ≥.80 | ≥.90 | Disagreement items / confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expanded | all accepted primary | 16 | 0.834 | 0.893 | 0.477 | 1.000 | 10 | 7 | see full primary table |
| expanded | resolved expected-tone disagreements | 5 | 0.791 | 0.877 | 0.477 | 0.974 | 3 | 1 | Q100 天 0.477; Q051 天 0.974; Q065 我 0.877; Q092 天 0.894; Q053 晚 0.732 |
| pilot | all accepted primary | 16 | 0.779 | 0.754 | 0.427 | 0.990 | 7 | 7 | see full primary table |
| pilot | resolved expected-tone disagreements | 3 | 0.773 | 0.767 | 0.576 | 0.976 | 1 | 1 | Q100 天 0.767; Q051 天 0.976; Q037 不 0.576 |

**All seven expanded/pilot disagreement syllables.**

| QA / take | Target / pinyin | Expected surface | Tone span ms | Expanded / confidence | Pilot / confidence | Deterministic |
| --- | --- | --- | --- | --- | --- | --- |
| Q100 / S01 | 天 / tian | T1 | 100 | T2 / 0.477 | T4 / 0.767 | ABSTAIN |
| Q037 / S01 | 不 / bu | T2 | 30 | T2 / 0.995 | T4 / 0.576 | ABSTAIN |
| Q065 / S01 | 我 / wo | T3 | 20 | T2 / 0.877 | T3 / 0.937 | ABSTAIN |
| Q092 / S02 | 天 / tian | T1 | 160 | T2 / 0.894 | T1 / 0.427 | ABSTAIN |
| Q053 / S02 | 晚 / wan | T3 | 110 | T2 / 0.732 | T3 / 0.618 | ABSTAIN |
| Q028 / S03 | 买 / mai | unknown/unresolved | 230 | T2 / 0.610 | T3 / 0.713 | ABSTAIN |
| Q033 / S03 | 种 / zhong | unknown/unresolved | 130 | T2 / 0.984 | T1 / 0.654 | T2 |

Disagreements span S01 (3/7), S02 (2/5), and S03 (2/4), rather than concentrating in one take. All seven are expanded T2 predictions; the pilot predicts no T2 anywhere in the primary set. Their lexical tones are four T3, two T1 and one T4; resolved expected tones are two T1, two T3 and one T2, with two unresolved. 天 recurs in two takes; the other targets differ. Disagreement tone spans range 20-230 ms (median 110 ms), compared with 60-120 ms (median 90 ms) for model agreements. Both accepted spans under 60 ms disagree, but five disagreements have 100-230 ms spans. Four of seven expanded predictions have confidence ≥.80, versus one pilot prediction. Disagreement is neither limited to short spans nor exclusively low confidence. These are descriptive patterns from N=16, not learned rules. Exact computational reproduction establishes numerical repeatability; robustness across repeat recordings or acoustic perturbations was not tested.

**Per-take confidence detail.**

| Take | Model | Mean | Median | Min | Max | ≥.80 | ≥.90 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | expanded | 0.777 | 0.877 | 0.477 | 0.995 | 4 | 2 |
| S01 | pilot | 0.736 | 0.741 | 0.561 | 0.976 | 2 | 2 |
| S02 | expanded | 0.903 | 0.935 | 0.732 | 0.990 | 4 | 3 |
| S02 | pilot | 0.792 | 0.945 | 0.427 | 0.986 | 3 | 3 |
| S03 | expanded | 0.848 | 0.891 | 0.610 | 1.000 | 2 | 2 |
| S03 | pilot | 0.837 | 0.851 | 0.654 | 0.990 | 2 | 2 |

**Exploratory supplemental results, frozen after primary.**

| Set | Model | Expected agreement | Coverage / abstentions |
| --- | --- | --- | --- |
| diagnostic | deterministic | 0/2 covered; 5 resolved | 5 / 6 |
| diagnostic | expanded | 2/5 covered; 5 resolved | 11 / 0 |
| diagnostic | pilot | 2/5 covered; 5 resolved | 11 / 0 |
| unknown | deterministic | 21/31 covered; 43 resolved | 49 / 26 |
| unknown | expanded | 26/43 covered; 43 resolved | 75 / 0 |
| unknown | pilot | 23/43 covered; 43 resolved | 75 / 0 |

Many supplemental intended labels are unknown. Contextual expectations may use recorded reading hypotheses, not independently verified intended text. Diagnostic intended targets can deliberately differ from the spoken unit. None of these rows enters primary statistics.

**Historical 我 and 我想买这个.** All five non-control 我想买这个 takes are separately reported; three 个 units are quarantined. The five takes contribute 22 accepted / 3 quarantined units. The two prior 我→T4 takes contribute 11 accepted / 1 quarantined unit across their phrases (contaminated 一 is quarantined). The seven-take historical view therefore has 33 accepted / 4 quarantined units, already included in unknown provenance. The two TTS/control takes are excluded. Full historical accepted sequences follow.

| Take | Phrase | Accepted characters | Expanded | Pilot | Fresh deterministic | Quarantined |
| --- | --- | --- | --- | --- | --- | --- |
| 19d8333b | 我想买这个 | 我 想 买 这 个 | T2 T3 T3 T4 T1 | T2 T1 T3 T4 T4 | T3 ABSTAIN ABSTAIN T4 ABSTAIN | 0 |
| 4f1ab9ed | 我想买这个 | 我 想 买 这 个 | T3 T3 T2 T4 T3 | T3 T4 T2 T4 T3 | T3 ABSTAIN T3 T4 ABSTAIN | 0 |
| 89cee47e | 我想买这个 | 我 想 买 这 | T2 T2 T3 T4 | T3 T2 T1 T4 | T3 ABSTAIN T3 T4 | 1 |
| 8faf1a90 | 我要一个苹果 | 我 要 一 个 苹 果 | T3 T4 T2 T4 T4 T2 | T3 T4 T2 T4 T4 T2 | T4 ABSTAIN T4 T4 T4 T3 | 0 |
| a5acd04c | 我有一个苹果 | 我 有 个 苹 果 | T4 T3 T4 T4 T2 | T3 T3 T4 T4 T2 | T1 T3 T4 ABSTAIN T3 | 1 |
| bb27924c | 我想买这个 | 我 想 买 这 | T2 T2 T3 T4 | T2 T2 T3 T4 | T2 T3 T4 T4 | 1 |
| d7b27845 | 我想买这个 | 我 想 买 这 | T3 T1 T3 T4 | T3 T1 T2 T4 | T3 ABSTAIN T3 T4 | 1 |

| Every accepted supplemental 我: take / source | Phrase | Provenance | Intended / expected tone | Archived deterministic 我 | Prior pilot whole / confidence | Same-context pilot whole / confidence | Pilot nucleus/coda / confidence | Expanded nucleus/coda / confidence | Fresh deterministic 我 | Prior→reviewed pilot argmax changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0b194cf9 / c5ab3a5086e7587d5a3fbade | 我想买 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | TONE_3 | T2 / 0.794 | T2 / 0.818 | T2 / 0.974 | T2 / 0.982 | T3 | no |
| 19d8333b / 9be2abae8812996a15c34742 | 我想买这个 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | ABSTAIN / UNAVAILABLE | T2 / 0.505 | T2 / 0.715 | T2 / 0.967 | T2 / 0.998 | T3 | no |
| 40357072 / b4006022088e4b9f86c4bc49 | 我想买五把雨伞 | DOCUMENTED_DIAGNOSTIC | unknown/unresolved / unknown/unresolved | TONE_3 | T3 / 0.759 | T3 / 0.793 | T3 / 0.814 | T2 / 0.667 | T3 | no |
| 4b9dbd2b / 1900a0b54946dd6fc129d7e3 | 我要一个苹果 | UNKNOWN_PROVENANCE | unknown/unresolved / T3 | TONE_3 | T3 / 0.423 | T2 / 0.575 | T2 / 0.929 | T2 / 0.451 | T3 | YES |
| 4f1ab9ed / 6411e08e10f9f527b02ca28a | 我想买这个 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | TONE_3 | T3 / 0.653 | T3 / 0.818 | T3 / 0.999 | T3 / 0.885 | T3 | no |
| 5c70f317 / 4b638d24a879d540857bd45e | 我想买 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | TONE_3 | T3 / 0.745 | T3 / 0.908 | T3 / 0.978 | T3 / 0.949 | T3 | no |
| 6b5b2135 / bc9a3d301cf536e250b43ccc | 我想买 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | UNCLEAR | T3 / 0.666 | T3 / 0.758 | T3 / 0.701 | T2 / 0.681 | T2 | no |
| 7e6b6fe9 / e0b8592e23d631090f632b14 | 我想买 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | TONE_3 | T2 / 0.438 | T2 / 0.649 | T2 / 0.893 | T2 / 0.837 | T3 | no |
| 89cee47e / 4966e43af7d8a3fb1e682966 | 我想买这个 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | TONE_3 | T2 / 0.600 | T3 / 0.534 | T3 / 0.722 | T2 / 0.583 | T3 | YES |
| 8d252264 / d29b73b2d231596503e96c5d | 我要一个苹果 | UNKNOWN_PROVENANCE | unknown/unresolved / T3 | TONE_3 | T2 / 0.475 | T2 / 0.498 | T2 / 0.493 | T2 / 0.970 | T3 | no |
| 8faf1a90 / 2b04d5f7ab74227e20646647 | 我要一个苹果 | UNKNOWN_PROVENANCE | unknown/unresolved / T3 | TONE_4 | T3 / 0.596 | T3 / 0.879 | T3 / 0.989 | T3 / 0.811 | T4 | no |
| S13 / e6126f9dcaee765c29a5b499 | 我要去贵州 | DOCUMENTED_DIAGNOSTIC | T3 / T3 | not archived | not in prior probe | T3 / 0.904 | T3 / 0.848 | T4 / 0.724 | T4 | no prior comparison |
| a5acd04c / 1719cb43aa6532d8b7e0b17e | 我有一个苹果 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | TONE_4 | T4 / 0.394 | T2 / 0.720 | T3 / 0.397 | T4 / 0.866 | T1 | YES |
| b9067bec / d1508ce809d1a42b0a6bfa4e | 我想买 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | UNCLEAR | T3 / 0.780 | T3 / 0.925 | T3 / 0.990 | T3 / 0.613 | ABSTAIN | no |
| bb27924c / 8ad8f3aeeaf7e24bddf0a052 | 我想买这个 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | not archived | not in prior probe | T2 / 0.990 | T2 / 0.985 | T2 / 0.900 | T2 | no prior comparison |
| d11c8332 / 27879f6717d9c5973d562c61 | 我要一个苹果 | UNKNOWN_PROVENANCE | T3 / T3 | not archived | not in prior probe | T3 / 0.593 | T3 / 0.777 | T2 / 0.869 | T3 | no prior comparison |
| d47274bc / 21e32f11642844a12d98e631 | 我有一个苹果 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | not archived | not in prior probe | T3 / 0.795 | T2 / 0.734 | T2 / 0.996 | T3 | no prior comparison |
| d7b27845 / 983caebc345dff8da92ef921 | 我想买这个 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | T3 | T3 / 0.804 | T3 / 0.975 | T3 / 0.988 | T3 / 0.970 | T3 | no |
| ee8a8b32 / 3d14f466f01acf1798f8467a | 我想买 | UNKNOWN_PROVENANCE | unknown/unresolved / unknown/unresolved | TONE_3 | T3 / 0.629 | T3 / 0.824 | T3 / 0.990 | T3 / 0.701 | ABSTAIN | no |

Pilot a5acd04c 我 changes from prior T4 (.394) to T3 (.397); its probabilities remain diffuse and the expanded model predicts T4 (.866). Pilot 8faf1a90 我 was already T3 (.596), and remains T3 (.989), with expanded T3 (.811) and fresh deterministic T4. For 89cee47e 我, pilot changes prior T2 (.600) to T3 (.722), while expanded predicts T2 (.583). This is a changed conclusion for particular exploratory outputs, not proof that the earlier perceptual conclusion was wrong or that natural T3 is now reliably recognized. Fresh deterministic a5acd04c is T1 on the new whole span; the archived T4 remains preserved as a separate result on earlier timing. bb27924c was not in the earlier learned probe.

**Representation question.** No general material improvement is demonstrated. 64 accepted units overlap the prior pilot probe (59 unknown-provenance, 5 diagnostic). 15/64 pilot argmaxes change. Among 32 matched units with resolved numbered expectations, prior expected agreement is 19/32 and current nucleus/coda agreement is 15/32; intended lexical labels are unknown for all 64. These are not primary natural results. Prior source segmentation and context also differ, so this comparison cannot isolate pooling.

A controlled exploratory comparison keeps the newly reviewed whole span and context fixed and changes only pooling. It excludes Q037 from aggregate comparisons because its whole crop is non-PASS. On the remaining 15 primary units (9 resolved expected numbered tones), expanded expected agreement stays 4/9 and pilot stays 7/9. Expanded changes 4/15 argmaxes; pilot changes 1/15. Lexical agreement changes 7/14→5/14 for expanded and 10/14→9/14 for pilot. This does not justify switching the frozen configuration. All controlled whole outputs, including Q037 marked unsuitable for aggregate whole comparison, are retained. On unknown supplemental units, same-context whole→nucleus expected agreement changes 30/43→26/43 for expanded and 21/43→23/43 for pilot.

**Domain-transfer question: MIXED TRANSFER (provisional).** Coherent examples exist, including S02 我, 跟 and 去, and some historical cases. But expected agreement, cross-model agreement and take behavior do not support a strong transfer claim. Expanded is below pilot on this descriptive comparison, with several high-confidence disagreements. Neither model was reselected based on learner results. Three takes from one documented speaker, only 16/32 surviving units, unresolved sandhi, neutral outside the model and absent realized-tone labels make both generalization and calibration claims premature. The accepted subset is selected for crop usability, not a representative random sample.
The sealed native-domain expanded-model result remains strong: 90.38% corpus-test classification accuracy and 90.17% balanced accuracy in `aishell3-multispeaker-generalization-report.md`. Those native corpus metrics are not learner realized-tone metrics and were not rerun. The hypothesis that mixed learner results were caused mainly by approximate whole-syllable pooling is not supported. A native-to-learner domain-transfer uncertainty therefore remains.

**Exact next research step: BLINDED LEARNER REALIZED-TONE ANNOTATION / PERCEPTUAL VALIDATION.** Design that stage separately under the project's zero-budget constraint; do not assume paid annotators. Establish perceived/realized tone families independently of intended phrase, expected lexical tone and either model's output. Avoid model-output leakage. This stage is necessary because learner production may itself differ from expectations, and current agreement cannot separate learner production from model failure. No annotation protocol or new annotation UI is implemented here. Realized-tone ground truth is the main bottleneck; do not train learner models before resolving it.

**Reproduction and validation.** Both frozen classifiers were independently reloaded for all 102 accepted nucleus/coda units and all 102 whole-pooling controls. Maximum probability delta was 0.0. Fresh encoder extraction without cache reuse on one accepted unit per each of the 22 takes had maximum vector delta 0.0. Full deterministic extraction and classification reproduced exactly for all 102 accepted units. No fitting was performed. Phase result seals link primary-before-supplemental execution to the immutable release. The initial primary attempt stopped on a missing dependency in the research Python environment before deterministic output or result sealing; it is preserved separately. The successful run uses the existing service Python environment, matching the native workflow.

All 413 deterministic baseline hashes, 7,839 pinned native artifacts, 343 source-file references, 847 construction files and the original review-v2 packet/page are unchanged. Production pronunciation inference, learner grading, application UI, backend API and deployment files are unchanged. No commit, push or deployment occurred. Focused Python and Chromium checks cover draft/attestation, optional telemetry, required decisions, notes, all 22 adjudications, separation/quarantine, immutability, inference reproduction, no training and descriptive naming. See validation.json and test logs for exact test counts. Ruff, JavaScript syntax and git diff --check also pass.

**Research files changed in this continuation.** Updated `perceptual_tone/learner_finalization.py`, `scripts/learner_review_v2.js`, `scripts/learner_review_v2_smoke.cjs`, and `tests/test_learner_finalization.py`. Added `perceptual_tone/learner_release.py`, `perceptual_tone/learner_transfer.py`, `scripts/learner_transfer.py`, `scripts/learner_transfer_report.py`, `scripts/learner_transfer_verify.py`, `tests/test_learner_release.py`, `tests/test_learner_transfer.py`, and this report. Pre-existing uncommitted construction work remains in place. Private generated artifacts live under the ignored release and run directories.

**Artifact paths and reruns.**

- Release: `/home/jacob/benma/research/perceptual-tone-model/data/generated/releases/benma-learner-natural-v1-20261019`
- Evaluation and verification: `/home/jacob/benma/research/perceptual-tone-model/data/generated/learner-transfer-v1-20261019`
- Full adjudication: release `adjudication.jsonl`; all original notes/telemetry: `raw-draft.json`.
- Full probabilities and deterministic evidence: run `{primary,diagnostic,unknown}/predictions.jsonl`.
- Frozen comparison: run `representation-comparison/predictions.jsonl`.
- Read-only verification: `benchmark/pronunciation_v2/.venv/bin/python research/perceptual-tone-model/scripts/learner_transfer_verify.py`.
- Focused tests: `PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s research/perceptual-tone-model/tests -p 'test_learner_*.py' -v`.

Learner-domain transfer is MIXED and legitimate nucleus/coda pooling does not explain away the earlier external-probe uncertainty. Realized-tone ground truth is now the primary evaluation bottleneck.
