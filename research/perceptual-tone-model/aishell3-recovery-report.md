# AISHELL-3 QA-gate resolution — 2026-10-16

**Historical recovery report. Superseded for human QA status on 2026-10-17:**
Round 1 returned 18 PASS and eight non-PASS. Training remains blocked.
See the [boundary remediation report](aishell3-boundary-remediation-report.md)
and [Round-2 review instructions](aishell3-qa.md). The measurements below describe
the preserved acquisition/alignment pass, before human decisions were received.

**The AISHELL-3 automatic data-quality gate passes, but human playback QA is still required before model training.**

The existing 32-utterance pilot was reused without rerunning MFA. All 157 remaining
recovered utterances were aligned once with the same pinned model and rejection
thresholds. Of 789 units across 189 utterances and 16 verified speakers, **787 pass
automatic QA; two are quarantined**. The first four-tone dataset has **729 candidates**.
No classifier was trained, selected, evaluated or run on the physical Benma probe.

The [26-target review page](data/generated/aishell3/pilot/audit/review/index.html)
is finished and browser-tested. It asks about read-unit ownership and boundaries,
not tone quality or tone relabeling. **Human playback: 0/26, pending.**
See [review instructions and commands](aishell3-qa.md),
[machine-readable results](reports/aishell3-summary.json),
[source hashes](reports/aishell3-provenance.json),
[environment lock](reports/aishell3-environment-lock.json), and
[changed files](reports/aishell3-changed-files.txt).

## Source, acquisition and format

The primary source is the [official OpenSLR93 release](https://www.openslr.org/93/),
AISHELL-3 v1.0 dated 2020-10-18. It declares Apache-2.0. The corpus is connected
Mandarin read speech from 218 native Mandarin speakers. The
[authors' paper](https://arxiv.org/html/2010.11567), section 2, describes listening-based
pinyin transcription of actual readings, including sandhi, homographs, erhua and
pronunciation variation. These are the primary targets, not lexical reconstructions.
This does not imply every individual annotation is correct.

The release is a **gzip-compressed tar archive**, 19,057,141,777 bytes, with a
2020-11-18 Last-Modified header. The previous session downloaded byte ranges
0–4,194,303 and 4,194,304–16,777,215. This continuation downloaded **no further
corpus audio**. Concatenation produces a contiguous 16,777,216-byte prefix starting
at the gzip header. Sequential decompression from byte zero yields complete tar
members. Arbitrary interior ranges are not independently extractable.

The extractor validates tar headers, whitelists regular-file paths, requires
complete payloads and decodable PCM, and stops before the incomplete final
`test/wav/SSB0139/SSB01390306.wav`. The complete archive's gzip footer/CRC and full
checksum cannot be verified from a prefix. Local source/member/PCM SHA-256 hashes
are preserved; none is presented as a publisher-verified full-archive checksum.
The concatenated prefix SHA-256 is
`0257991d71764aaa7114587b9b397d829b634b3fa4c8c99767e369121e9a5f0c`.

Recovered: **189 complete WAVs, 25,648,750 WAV bytes, 290.647 seconds, 16 verified
speakers and 789 corpus read units (now aligned)**. Metadata includes `ChangeLog`,
`ReadMe.txt`, `phone_set.txt`, `spk-info.txt` and complete `test/content.txt`.
The registry has 218 records (176 female/42 male; 165 north/51 south/2 others).
Use actual metadata records: the readme's gender totals and age-range description
are not entirely consistent with the paper/metadata headers. Age groups remain
raw A/B/C/D codes, not inferred numeric ages or exact birthplaces.

116 WAVs have stale outer RIFF lengths. Every RIFF subchunk payload, PCM data
length, sample format and frame count was independently checked. For MFA, a valid
WAV container was written around the **identical original 44.1 kHz mono PCM16
samples**. Original bytes/hashes remain preserved. No sample repair, interpolation,
cropping or resampling was performed by preparation. Acoustic truncation remains
part of listening QA. The initial overly strict outer-size rejection was retained
under `data/generated/aishell3/preflight-v1/`; it is not the final result.

| Field | Verified parsing rule |
| --- | --- |
| Utterance/audio | `SSB00090030.wav` in `test/content.txt` maps to `test/wav/SSB0009/SSB00090030.wav`. IDs match exactly. |
| Speaker | First seven ID characters, confirmed against both the archive speaker directory and an exact `spk-info.txt` record; no heuristic grouping. |
| Read units | After filename and whitespace, alternating `Hanzi/read-unit pinyin` pairs. Preserve each pair in sequence; do not index by character count. |
| Actual reading | Real `碗 wan2 碗 wan3 香 xiang1` retains T2/T3/T1; `我 wo2 想 xiang3` retains corpus T2 before T3. |
| Tone | Final ASCII digit 1–5; neutral is 5, stored as T5. Invalid/missing tone digits are errors. |
| Erhua | `点儿 dianr3`, `孩儿 hair2`, `哪儿 nar3`: one read unit each. `儿 er2` remains a separate syllable when separately annotated. |
| Atypical multi-Hanzi | Three transcript pairs are flagged for review, including `哪儿 lang3`, `点儿 dian3`, `的儿 er2`; preserve their original text/labels. None is in the acquired audio subset. |
| Lexical metadata | Kept separately as null/not derived. Neither pypinyin nor Benma rules regenerates corpus targets. |
| Prosody | Separate `id|pinyin with markers|Hanzi with markers`. `%` follows a prosodic word/minor phrase; `$` marks a major phrase boundary. Markers consume no read unit or audio interval. |
| Prosody attachment | Require exact utterance, Hanzi and pinyin sequence agreement, plus matching marker positions at whole read-unit boundaries. Never overwrite content labels. |
| Punctuation | No punctuation is silently removed from content pairs; unsupported content characters are rejected. The inspected content has none requiring token insertion. |

All **24,773 real content rows parsed**, with zero pair/ID/pinyin failures. The
separate 7,738,375-byte prosody file contains 63,262 rows, all parsed. It came from
the [AISHELL/aishelltech account](https://huggingface.co/datasets/AISHELL/AISHELL-3),
revision `f20d5db4a31fe779ef07bb1af4ea92da5c786622`, path
`train/label_train-set.txt`. It is used only for format inspection and fixtures:
**none of the 189 acquired test recordings has a matching train-prosody entry**.
It has not been compared with the unacquired train portion of the official archive.
Internal phrase locations therefore remain unknown; utterance ends are identified.

## Local alignment and reconstruction

Installed and usable: **MFA 3.3.9**, Python 3.14.8, Kaldi 5.5.1172, kalpy 0.10.5,
Pynini 2.1.7, micromamba 2.9.0. This is an isolated research environment under
`.cache/mfa-env`, not a production install. Its 284-package installation completed
from the preceding session; it occupies about 5.5 GiB plus 2.4 GiB of package cache.
Although the installed Kaldi build includes CUDA dependencies, this run used CPU.

MFA's model manager downloaded the official `mandarin_mfa` acoustic model and
`mandarin_china_mfa` dictionary, both **v3.0.0**. The acoustic ZIP is 92,103,335
bytes. The old rejected raw GitHub curl command/30 MB cap was not repeated.
Model asset IDs, exact byte counts and SHA-256 hashes are in the provenance report.
These resources are attributed to Montreal Corpus Tools / McAuliffe and
Sonderegger, CC-BY-4.0; they do not inherit the corpus's Apache license.

The stock dictionary has no tone-numbered pinyin entries. G2P became necessary
to generate phones from the corpus pronunciations. Inspection established that
`mandarin_china_mfa` G2P v3.0.0 is a Hanzi model; it was downloaded but **not used**.
The used model is **`mandarin_china_pinyin_mfa` v3.0.0**, whose grapheme inventory
expects diacritics. `wo3 → wǒ`, `nv3 → nǚ`, `de5 → de` are notation conversions,
not Hanzi-derived pronunciations.

Unreviewed G2P output was insufficient: `wo2` produced /m o/, neutral `de5`
produced a /di4/ pronunciation, and `le5` produced /liao3/. The pilot used nine bounded entries, explicitly corrected in [aishell3-pronunciations.json](configs/aishell3-pronunciations.json).
Every donor phone sequence is checked against the pinned stock dictionary.
Six neutral entries reuse exact stock neutral pronunciations; `sheng5` removes
the donor's tone; `wo2` and `de1` apply the **corpus** tone to verified segmental
phones. The rejected G2P outputs and exact transformations remain in the audit.
No corpus label is rewritten. Future OOVs or incompatible phone/tone mappings
fail closed rather than inheriting a guessed lexical pronunciation.

Each corpus pair gets one ASCII alignment token, e.g. `wo2 → aiswotoneb`, with
an explicit phone pronunciation in a research-only dictionary. There are **152
distinct tokens, zero unresolved OOVs**, and no phone inventory violations.
The token encodes the pronunciation for MFA only and is forbidden as an ML input.
Production and upstream dictionaries are unchanged. MFA tokenization is disabled.

The pilot selects **32 utterances / 200 units across all 16 acquired speakers**:
speaker round-robin, longer connected utterances first, label-independent hash
tie-breaks. It aligned in **19.107 seconds**, with 32/32 outputs, zero warnings,
zero errors, zero token-sequence mismatches, and no new aligner training.

Reconstruction consumes actual `words` and `phones` TextGrid tiers. It requires
the exact original token sequence; every non-silence phone must belong to exactly
one token interval; its ordered phones must match that token's supplied dictionary
pronunciation; and phone spans must cover the word span without gaps/overlaps.
Zero-initial syllables, finals, initials, rhotics and neutral phones are validated
through the same pronunciation sequence, not a fixed two-phone assumption.
Inter-unit silence contributes no example. No proportional timing is used.

Thresholds were fixed before alignment: unit duration 60–800 ms, no phone over
500 ms, no more than half a unit's phones at the approximately 10 ms floor,
finite mean alignment likelihood above -100, and timing within audio bounds.
These are conservative gross-error filters, not a calibrated accuracy guarantee.
The likelihood range was -49.918 to -37.581, duration-deviation range 0.876–2.660,
and SNR range 9.467–25.844. Diagnostic values and null confidence are retained.

**200 units reconstructed; zero automatic unit exclusions; one incomplete archive
tail excluded. All 200 pilot candidates pass automatic QA; training still awaits playback QA.**
Their labels, exact spans, phones, neighbors, source audio, speaker, original
transcript provenance and diagnostics are in the candidate JSONL. Sequence
agreement is a consistency check, not independent proof of what was pronounced.

## Expansion and fixed rejection policy

The expansion uses a separate `expansion/corpus-expansion` MFA working directory,
so pilot TextGrids, source WAVs, candidate rows and review-item hashes are unchanged.
The expansion dictionary contains 312 tokens: **83 validated pilot pronunciations
are reused**, and 229 new pronunciations were inspected. The G2P batch emitted all
312 spellings; regenerated overlap was discarded in favor of the validated pilot.
The original pilot dictionary still has 152 entries and its original hash.

Seventeen new explicit dictionary corrections address `a5`, `bao2`, `dao5`, `fan5`,
`gei2`, `guang2`, `jiu2`, `ma5`, `men5`, `shuo2`, `ya4`, `ya5`, `zi5`, `nai2`, `hai2`,
`dou1`, `shui2`. Every donor sequence exists in the pinned dictionary. Corrections
preserve the annotated pinyin's segmental identity and apply only the corpus tone
for alignment. For example, raw G2P `bao2` used /p w o/ instead of /p aw/, `nai2`
used /l aj/ instead of /n aj/, and `hai2` used /xʷ a n/ instead of /x aj/.
The corpus annotation remains authoritative even where Hanzi has a different usual
reading. No Hanzi-derived target labels or lexical-tone rules were introduced.
There are 26 total explicit overrides across both stages; 23 occur in expansion.

The new MFA run took **20.115 seconds**: 157/157 utterances, 589 units, zero OOVs,
zero failed utterances, zero sequence/ownership failures. It accepts 587 new units;
the reused pilot contributes 200. Models remain MFA 3.3.9 and mandarin_mfa 3.0.0;
no encoder or aligner was trained. No additional corpus or model download occurred
in this QA-gate continuation.

The same 60–800 ms read-unit and <=500 ms individual-phone limits were retained.
Two quarantines, both T1 in train:

| Target | Unit span | Long phone | Reason |
| --- | --- | --- | --- |
| `aishell3:SSB00090179:0`, 一 yi1 | 0.240–0.750 s, 510 ms | /i˥/ 510 ms | `extreme_phone_duration` |
| `aishell3:SSB00570318:1`, 花 hua1 | 0.660–1.350 s, 690 ms | /a˥/ 530 ms | `extreme_phone_duration` |

They remain in `continuation/scaled-rejected.jsonl` and cannot enter the release.
No thresholds were relaxed to increase yield. The incomplete archive tail is a
source exclusion, separate from these two aligned-unit quarantines.

## Automatic audit and human gate

All 200 pilot and all 789 combined target crops decode, are non-empty and contain
nonzero PCM. Source and canonical WAV hashes, byte-equivalent PCM, original
transcript rows, speaker metadata and pinned model hashes were rechecked.
Every reconstructed unit matches the supplied pronunciation and corpus ordering;
all speech phones have one owner, contiguous coverage, in-bounds times and no
internal silence. No order inversions, collapsed syllables, missing phones,
pathological floor-phone fractions or structural failures were found.
Reconstruction repeats deterministically without invoking MFA.

| Duration (ms) | Pilot: 200 | Combined: 789 before quarantine | Accepted: 787 |
| --- | ---: | ---: | ---: |
| min | 80 | 60 | 60 |
| p1 | 99.9 | 108.8 | 108.6 |
| p5 | 140 | 130 | 130 |
| p25 | 180 | 180 | 180 |
| median | 220 | 230 | 230 |
| p75 | 280 | 300 | 300 |
| p95 | 410 | 440 | 437 |
| p99 | 520.1 | 540 | 531.4 |
| max | 550 | 690 | 570 |

The 26-item packet contains 5 T1, 5 T2, 6 T3, 5 T4 and 5 T5 targets. All 78
media files were hash-checked and compared to exact source samples. Chromium
loaded all 78 audio references, exercised context/target playback, blocked
incomplete exports and required notes for non-PASS. Synthetic browser answers
were confined to an isolated test profile and never saved as human QA.
All 26 plots were visually inspected in the preceding pass. Visual and decode
checks do not constitute human playback or independently establish speech content.

| Gate | Evidence/status |
| --- | --- |
| A, source/provenance | Pass: official retained prefix, member hashes, unchanged source. Full-archive checksum unavailable. |
| B, speakers | Pass: directory, filename and official metadata agree for 16 speakers. |
| C, read-unit parsing | Pass: deterministic corpus pairs, no tone regeneration. |
| D, MFA sequence | Pass: all 189 sequences match, no drops or OOVs. |
| E, reconstruction | Pass: 789 reconstructed; 787 automatically accepted; two quarantined. |
| F, timing diagnostics | Pass: no systemic defect under unchanged rules. |
| G, representative ownership | Plots plausible; required human playback is pending for 26 targets. |
| H, transcript/audio mismatch | None discovered automatically; playback checks remain pending. |

Automatic QA and coverage permit scaling and partitioning. **The combined training
release gate remains closed pending complete human playback PASS decisions.**
All 26 must be reviewed with name, timestamp and explicit listening confirmation.
A non-PASS is retained as evidence and blocks release until the issue is investigated;
no decision silently moves a boundary or changes a label. The importer verifies
packet, row and media hashes and rejects unknown/duplicate targets or incomplete
reviews. A release re-audits saved alignments and media rather than trusting an
editable summary's `passed` flag.

## Dataset, T3 and fixed split

| Tone | Acquired | Pilot accepted | Combined accepted | Train | Validation | Test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T1 | 177 | 41 | 175 | 98 | 35 | 42 |
| T2 | 183 | 36 | 183 | 98 | 35 | 50 |
| T3 | 147 | 37 | 147 | 80 | 36 | 31 |
| T4 | 224 | 70 | 224 | 119 | 51 | 54 |
| T5 | 58 | 16 | 58 | 31 | 13 | 14 |
| Total | 789 | 200 | 787 | 426 | 170 | 191 |
| First four-tone experiment |  |  | 729 | 395 | 157 | 177 |

Neutral labels are preserved. The first model excludes T5 because held-out neutral
coverage is sparse; T5 does not block the four-tone gate. All four core classes
have >=20 test examples and >=10 train/validation examples. There are 31 test T3s.

The initial pure hash partition would have left only 64 test units and 10 test T3s.
Before any model training, a fixed size-only partitioner chose disjoint speaker
groups minimizing squared deviation from 60/20/20 **read-unit totals**, with
10/3/3 speaker quotas and seed 20261015 to break ties. It receives only per-speaker
unit counts, never labels, features or model metrics. The large speaker imbalance
prevents exact 60/20/20 unit totals under these speaker quotas. The resulting split
is frozen in `continuation/scaled-candidates.jsonl`; it is a modeling candidate
manifest, not permission to train before playback.

- **Train:** SSB0009, SSB0011, SSB0012, SSB0016, SSB0018, SSB0057, SSB0073, SSB0080, SSB0122, SSB0139.
- **Validation:** SSB0005, SSB0033, SSB0112.
- **Test:** SSB0038, SSB0043, SSB0133.

No speaker, utterance, source-PCM, target-crop or context-crop overlap crosses
partitions. Same-utterance neighboring windows remain in the same partition.
The original corpus's `test` partition is preserved as source provenance; it is
not confused with the new experiment's held-out test partition.
The subset is small and uneven: SSB0043 supplies 177/191 accepted test units and
SSB0112 supplies 148/170 validation units. Later metrics must report this speaker
concentration and cannot establish broad speaker generalization on their own.

T3 neighboring surface labels: **T1 38, T2 23, T3 1, T4 29, T5 18**.
Utterance-final/known phrase-final: **38**. Utterance-medial: **109**; their internal
phrase positions are unknown, so confirmed phrase-medial is **0**, not 109.
Pilot T3 counts remain 9/7/0/8/3 by following T1–T5, 10 final and 27 internal-unknown.
Corpus surface T2 remains T2 even when it may reflect a lexical T3 realization.

## Training and interpretation

Training **did not occur**. No selected encoder, layer, window, pooling or classifier
exists. Deterministic corpus-baseline coverage/abstentions/accuracy/confusion,
learned accuracy/balanced accuracy/macro-F1/per-class metrics, T3 recall, T3→T4
and T3→T2 comparisons are **unavailable, not zero**. External `我想买这个`
probabilities were not run. Whether a learned model fixes natural 我→T4 errors
is unknown. No model-quality conclusion or claim that Benma is solved is supported.

After playback passes, the released 729-example manifest is the input to the next
training stage: frozen Benma baseline, nonleaking acoustic-feature logistic model,
frozen HuBERT and WavLM logistic models, and best-embedding small MLP. Keep the
existing encoder revisions; search only layers 6/9/12, target/context and mean
pooling; select on validation only and evaluate test and physical probes afterward.
The command below releases data; it does not pretend that a training runner already
exists. Implementing/running that bounded comparison is the next gated stage.

## Validation and production freeze

**65 Python tests (32 AISHELL-specific), both existing Node test files, scoped
Ruff checks and the Chromium playback/export smoke test pass.** Tests retain
parser, multi-Hanzi, neutral, erhua, speaker, TextGrid, ownership, dictionary, RIFF,
label-input isolation, embedding-cache and reproducibility checks. Ten new tests
exercise complete/incomplete and non-PASS reviews, timestamp/listening requirements,
stale rows, duplicate IDs, tampered packets/media, ingestion, blocked release,
size-only partitioning and optional neutral coverage.

All **413 pinned files remain unchanged**. The **63-example deterministic replay
is byte-identical**, SHA-256
`63ae919eb27c5b053ca74195bf631de544c2e4649e1ef97e72f1aac78f723ee0`.
`git diff --check` passes. Production, frozen baseline and inherited THCHS artifacts
remain unchanged. No commit, push or deployment occurred.

## Next step and reproduction

Open and complete the [26-target playback packet](data/generated/aishell3/pilot/audit/review/index.html).
The exact open/serve, ingest and continuation commands are in [aishell3-qa.md](aishell3-qa.md).
No source download, pilot re-alignment or model installation is required.
The legacy unanswered JSONL template is not the ingestion entry point; use the
page's JSON export so the whole packet hash is included.

Recorded expansion commands (already completed; do not rerun to obtain new boundaries):

```sh
P=research/perceptual-tone-model
D="$P/data/generated/aishell3"
PY=benchmark/pronunciation_v2/.venv/bin/python
$PY "$P/scripts/aishell3_continue.py" prepare-expansion
sh "$P/scripts/aishell3_mfa.sh" g2p "$D/expansion/pinyin.txt" \
  mandarin_china_pinyin_mfa "$D/expansion/pinyin.dict" \
  --num_pronunciations 1 --num_jobs 2 --no_use_mp --clean
$PY "$P/scripts/aishell3_prepare.py" lexicon --stage expansion
sh "$P/scripts/aishell3_mfa.sh" align "$D/expansion/corpus-expansion" \
  "$D/expansion/read-units.dict" mandarin_mfa "$D/expansion/aligned" \
  --no_tokenization --num_jobs 2 --no_use_mp --clean --output_format long_textgrid
$PY "$P/scripts/aishell3_continue.py" audit-scaled
```

Generated artifacts are write-once or checked for exact agreement on repetition.
`audit-scaled` reuses TextGrids; it does not invoke MFA. The pilot candidate SHA-256
remains `6bed0435ff9c15fc78b47fbd5946c09b579a6e837e11ae1c3659819e9f51f763`.
The previous stopped-pilot report is retained under
`data/generated/aishell3/continuation/prior-pilot-report.md` as history.
