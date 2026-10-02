# Real-evidence replay results

Timing improves **30/36 → 36/36**; reading resolution remains **27/36 → 27/36**. All 36 provider grapheme entries pass the mapping checks. **Zero** provider/perceived-text, grapheme-sequence or timing conflicts occur in these four captures. This is coverage of supplied evidence, not 100% boundary accuracy. No new inference, audio decoding, Praat extraction, F0 selection, threshold tuning or learned-model work was performed.

The exact per-recording tables, including all F0 counts, are generated in [coverage-before-after.md](coverage-before-after.md). [coverage.json](coverage.json) retains recording IDs, source-record/audio hashes, counts, unresolved reading alternatives and recovered region evidence. “Before” is counted from original saved v1 units, not a reconstruction using the new algorithm. “After” is counted from validated v2 replay units.

## Recovered regions and unchanged pitch policy

| Recording/unit | Character | Exact provider span, ms | Usable selected F0 / total frames |
| --- | --- | --- | --- |
| S01/u3 | 气 | 3210–3460 | 0/25 |
| S01/u10 | first 说 | 5810–5900 | 5/9 |
| S01/u11 | second 说 | 5910–6000 | 2/9 |
| S02/u4 | 上 | 2200–2550 | 3/35 |
| S02/u9 | 吃 | 4430–4810 | 0/38 |
| S03/u6 | 果 | 3130–3590 | 0/46 |

The recovered spans expose **10 additional usable selected frames**, but only one additional unit reaches the existing five-frame descriptive flag. Totals: timed units **30→36**; ≥5 usable **19→20**; heavy raw-F0 missingness **23→28**; zero usable F0 among timed units **7→10**; instability **1→1 units / 5→5 frames**. These flags overlap. Increased missingness counts reflect newly visible regions, not worse extraction. The same saved whole-recording frame dictionaries are sliced at `[start,end)` with the existing policy.

## Requested phrases: timing and reading are separate

| Perceived word | Accepted character spans, ms | Reading outcome |
| --- | --- | --- |
| 天气 (S01) | 天 2930–3200; 气 3210–3460 | tiān; 气 unresolved |
| 晚上 (S02) | 晚 1960–2190; 上 2200–2550 | wǎn; 上 unresolved, no supported neutral choice |
| 吃饭 (S02) | 吃 4430–4810; 饭 4820–5250 | 吃 unresolved; fàn |
| 水果 (S03) | 水 2830–3120; 果 3130–3590 | shuǐ; 果 unresolved |
| 说说 (S01) | first 说 5810–5900; second 说 5910–6000 | both unresolved; no fabricated reduplication/neutral rule |

Nine remaining ambiguous units: S01 气 and both 说; S02 上 and 吃; S03 哪, 种 and 果; S13 要. The exact dictionary alternatives and missing context capabilities are listed in [mapping-audit.md](mapping-audit.md). All nine now have timing. No additional readings were forced; 贵 guì / 州 zhōu remain resolved from perceived 贵州, with their existing dictionary source and exact perceived-word context.

## Learner semantics and truth boundaries

- **S01:** “perceived substitutions on a user-reported imperfect attempt; cause unresolved.” 进去/说说 are not called ASR bugs, or diagnosed as tone/vowel/consonant/lexical errors. Low Azure scores/Mispronunciation flags are preserved as perceived-reference-conditioned evidence, not a cause label.
- **S02:** 饭 is a “user-reported possible pronunciation issue.” This is not a gold wrong-pronunciation annotation. ASR recognition and the positive reference-conditioned score do not prove correct production. The word score and `fan 4` label remain provider evidence only.
- **S03:** perceived punctuation differs from the intended punctuation; lexical characters match. 果 now retains its explicit interval despite unresolved reading and zero usable saved F0 there.
- **S13:** exact perception/alignment stays `我要去贵州。`; target stays `我要去广州。`. 贵 is timed 2550–2900 ms, reading guì; 州 is timed 2910–3370 ms, reading zhōu. The target layer contains 广→贵 substitution and expected target guǎng. No target 广州 phone/reading enters the perceived layer, and no acoustic cause is inferred.

Generated reports: [S01](reports/S01/report.md), [S02](reports/S02/report.md), [S03](reports/S03/report.md), [S13](reports/S13/report.md). The note input is [study-notes.json](study-notes.json), supplied separately from provider captures. Every unit continues to abstain from pronunciation judgment.

## Reproduction and provenance

From repository root, use the existing API environment (pypinyin 0.55.0). The following command makes **no provider or audio calls** and refuses an existing output directory:

```sh
services/api/.venv/bin/python -m benchmark.pronunciation_v2.connected_replay \
  --record S01=services/api/var/connected-study/source-records/S01.json \
  --record S02=services/api/var/connected-study/source-records/S02.json \
  --record S03=services/api/var/connected-study/source-records/S03.json \
  --record S13=services/api/var/connected-study/source-records/S13.json \
  --annotations docs/research/pronunciation-v2/2026-10-01-connected-speech-mapping/study-notes.json \
  --output services/api/var/connected-study/mapping-v2-next-replay
```

Original captures remain unchanged at `/tmp/benma-study-S{01,02,03,13}/record.json`. Byte-identical local preservation copies live in the ignored `services/api/var/connected-study/source-records/`. Reviewed v2 full records live in the ignored `services/api/var/connected-study/mapping-v2-reviewed/`. No audio was copied. No full raw study record was added to tracked docs.

Replay preserves original recording IDs, audio hashes/path/duration/provenance (`recorded_audio`), complete perception/raw ASR and request configuration, complete Azure raw response/status, intended text, and full acoustics. It records the source byte hash, original versions/configuration/issues and library version. Old mapping issues remain in replay metadata rather than being mistaken for current mapping outcomes. Repeated replays from the same inputs are deterministic; source records are never overwritten. Report generation is separately repeatable from a saved v2 record using `markdown(record)`.

The committed-candidate test data [connected-real-mapping-excerpts.json](../../../../benchmark/pronunciation_v2/fixtures/connected-real-mapping-excerpts.json) are clearly labeled **derived real provider mapping excerpts**, with source hashes and only mapping-relevant structures. They are neither full real-study captures nor synthetic recordings. Separate adversarial tests use deliberately constructed structural payloads. Neither kind supplies pronunciation gold.

## Largest remaining blocker and exact next step

The strongest blocker to answering **what the learner actually produced** is the absence of independently grounded segmental/phonetic evidence and its validation. With all available provider timing now mapped, the system still has no observed vowel/consonant identity: Azure's reference labels cannot fill that role, particularly for S02 饭. For the narrower pitch route, missing evidence is already a major limit: **16/36 units have fewer than five usable selected frames, 10/36 have zero, and 28/36 have heavy raw-F0 missingness**. Only one unit shows tracker-instability flags, so these data do not justify treating unstable tracking as the dominant cause. Nine unresolved readings additionally limit contextual expectations, but resolving them would not establish physical production.

Next, conduct a **small blinded phonetic evidence audit of these same four recordings**, with no new recording or model experiment: review the six recovered intervals plus S02 饭 and S13 贵/州 (nine focal units), listening with neighboring context and inspecting waveform/spectrogram against the existing saved pitch trace. First hide intended text, Azure reference labels/scores and learner self-report; separately annotate boundary plausibility, audible segment identity, whether periodic voicing is present where selected F0 is missing, and uncertainty. Reveal the text/self-report layer only afterward for comparison. Preserve disagreements and unavailable judgments. This establishes whether missing F0 reflects unvoiced material, extraction loss or boundary placement, and what independent evidence a future segmental path must capture. It does not authorize F0 tuning or turn the review into a tone-accuracy score.
