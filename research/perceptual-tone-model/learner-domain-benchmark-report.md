# Learner-domain benchmark construction — 2026-10-18

**Alignment QA ready; human review pending. No learner-domain model evaluation, training, release, commit, push or deployment.**
The preserved native conclusion remains **STRONGLY REPLICATED**. This pass does not answer whether a native-to-learner domain gap remains.

## Inventory and role decisions

The complete local inventory contains **740 audio artifacts**, resolving to **174 distinct capture/source recordings**. These are archive candidates, **not 174 verified learner recordings**. There are **175 original-recording files before deduplication** (171 upload originals plus four sentence-study WAVs). Source files comprise 168 canonical captures, 171 upload originals and four original sentence-study WAVs; normalization and lineage merge their representations. All original bytes are retained.

The source-level roles are **3 natural, 2 diagnostic, 169 unsuitable/unknown**. The latter combines documented controls with captures whose identity or intent cannot be established. The source inventory retains all 174 rows before selection. No missing canonical reference was found in the scanned metadata. No live database or external service was queried; completeness is scoped to the available local archives, not every historical recording ever made.

| Set | Recordings | Syllable instances | Status |
| --- | ---: | ---: | --- |
| Natural, explicit study instructions S01/S02/S03 | 3 | 32 | Proposed, awaiting alignment QA |
| Diagnostic, S13 substitution and documented U-shape take | 2 | 12 | Separate diagnostic stratum, awaiting QA |
| Historical supplemental alignment review | 17 | 79 | Provenance quarantine; never admitted automatically |
| Total playback QA | **22** | **123** | 246 human decisions, 369 clips |
| Other source candidates retained in inventory | 152 | — | Excluded with reasons; alignment not attempted |

The proposed benchmark is **5 recordings / 44 units**, below the requested target because trustworthy provenance is scarce. It has five reading hypotheses, 33 distinct toneless pinyin syllables and no repeated take of a reading phrase. The broader QA set has nine reading phrases, 37 distinct toneless pinyin syllables and 13 repeated takes beyond the first per phrase. This preserves multiple takes for later use without inventing their natural/diagnostic role.

Only S01–S03 have explicit natural-production instructions. S13 instructs 贵州 in place of intended 广州; the U-shape take is documented as a diagnostic test. The three separately documented human comparison captures still lack explicit natural-versus-deliberate intent. The short 我想买 recordings explicitly lack stored capture intent. All such uncertainty remains visible; no family prediction, confidence, grade, acoustic difficulty or alignment success decides admission. An unanswered provenance question is not confirmation.

Complete inventories and reasons:

- [Source inventory JSONL](data/generated/learner-alignment-v1/inventory.jsonl)
- [Readable complete source inventory](data/generated/learner-alignment-v1/inventory.md)
- [Audio artifacts and duplicate/clip lineage](data/generated/learner-alignment-v1/audio-artifacts.jsonl)
- [Metadata source hashes](data/generated/learner-alignment-v1/discovery-sources.json)
- [Every excluded or suspicious source](data/generated/learner-alignment-v1/exclusion-and-suspicion-report.jsonl)
- [Missing audio reference audit](data/generated/learner-alignment-v1/missing-audio-references.jsonl)

## Phrases and historical cases

The nine QA reading hypotheses are 今天天气不错我们出去走走吧, 我昨天晚上跟朋友去吃饭了, 你想买哪种水果, 我要去贵州, 我想买五把雨伞, 我想买这个, 我想买, 我要一个苹果, and 我有一个苹果. S13's **intended** phrase remains 我要去广州. Unknown intended phrases stay null; historical ASR is retained separately. S01 and S02 disagree with historical ASR and are flagged across their units rather than silently accepting either transcript as actual phonetic truth.

The broader archive has 23 normalized Hanzi phrase strings. Raw strings, including non-Hanzi text and malformed ASR, remain in the inventory; excluded malformed transcripts are not promoted to verified readings.

| Normalized archive phrase | Unique source takes |
| --- | ---: |
| 今天天气不错我们出去走走吧 | 1 |
| 你想买哪种水果 | 1 |
| 其实我不行 | 1 |
| 我上马 | 1 |
| 我也啊 | 1 |
| 我们去吧 | 4 |
| 我们要去贵州 | 1 |
| 我想买 | 6 |
| 我想买五把雨伞 | 9 |
| 我想买五部 | 1 |
| 我想买这个 | 7 |
| 我昨天晚上朋友去吃饭了 | 1 |
| 我昨天晚上跟朋友去吃饭了 | 1 |
| 我是讲 | 1 |
| 我有一个苹果 | 2 |
| 我要一个苹果 | 13 |
| 我要去贵州 | 1 |
| 所以 | 1 |
| 所以我感觉我把改了很多 | 1 |
| 本来我想去 | 1 |
| 现在是下午两点半 | 1 |
| 贵州 | 3 |
| 这不是我的 | 2 |

**Seven 我想买这个 takes** were recovered: five non-control historical takes enter supplemental QA, and two documented TTS/noise controls are excluded. The seventh take, bb27924c, came from the measurement-fidelity fixtures; its provenance, rather than its system behavior, motivated inclusion in supplemental QA.

| Canonical take prefix | Historical provenance | Current role |
| --- | --- | --- |
| 89cee47e | Historical saved physical take | Unknown intent; supplemental QA |
| 19d8333b | Saved numeric physical smoke | Unknown identity/intent; supplemental QA |
| bb27924c | Measurement-fidelity physical fixture 430fcc2e | Unknown intent; supplemental QA |
| d7b27845 | Explicitly documented human | Intent unconfirmed; supplemental QA |
| 4f1ab9ed | Explicitly documented human | Intent unconfirmed; supplemental QA |
| b8049b3e | Google TTS physical playback | Excluded |
| cad88597 | Google/background-noise control | Excluded |

Both requested frozen deterministic **我 → T4** examples were recovered with original/canonical audio: **8faf1a90 / 我要一个苹果** and **a5acd04c / 我有一个苹果**. Their 12 units undergo the same alignment procedure; they remain supplemental because capture intent is unconfirmed. [Historical Benma metadata](data/generated/learner-alignment-v1/historical-benma.jsonl) preserves existing family, support, grading, abstention and source hashes after selection. Historical segmentation and saved analyses are separately preserved. No deterministic replay was used for selection.

## Duplicates and derivatives

There are **130 byte-identical artifact groups**, containing **247 copies beyond the first**; these counts include saved copies and symlink references. The audit also finds **81 exact PCM clips** and **one additional PCM duplicate**. The original/canonical source pairs are joined by stored asset lineage or exact ffmpeg-decoded 16 kHz PCM, never by a similar-sounding phrase. One source has two canonical files (991a86ab and d04cfdd1) and two upload originals; it counts once. **57 source records have multiple metadata references**, retained without adding takes. All 22 QA sources have distinct source PCM identities.

The inventory separately retains 51 generated reference/assistant artifacts and 39 unlinked research artifacts. Unlinked transformations, synthetic controls and uncertain lineage are not counted as independent learner takes. Exact matching cannot identify arbitrary lossy or pitch-modified derivatives; unresolved artifacts stay excluded rather than being asserted independent.

## Frozen recognizers and alignment method

| Role | Artifact | SHA-256 |
| --- | --- | --- |
| primary | research/perceptual-tone-model/models/generated/aishell3-multispeaker-fixed-v2/experiment_B.joblib | `b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b` |
| secondary | research/perceptual-tone-model/models/generated/aishell3-first-four-tone-v1/model2_hubert.joblib | `c20cc46ed715ce5ed1f3a76f405014069f4a98c0b9e6e467ce28635b4df725d9` |

The primary is the expanded fixed Chinese HuBERT model: frozen encoder, layer 9, connected context, owned nucleus/coda mean pooling, balanced multinomial logistic regression, C=0.1. The original pilot is secondary. Both hashes match the pre-existing fitted-model seals; neither model was deserialized. [Frozen artifact registry](data/generated/learner-alignment-v1/frozen-models.json) hashes 7,839 native artifacts, including existing releases/results. Hashing does not read predictions into selection or alignment code.

Research-only MFA 3.3.9 uses the same cached mandarin_mfa acoustic model and native methodology: lexical reading tokens, word/phone ownership, complete phone coverage, pinned pronunciations, unchanged native diagnostic thresholds, and ±250 ms context. Missing na3/cuo4/san3 entries use exact segmentally appropriate pronunciations verified in the pinned dictionary; no timestamp or pronunciation was selected using recognizer output. The pronunciation supplement is recorded explicitly. No unknown phone role is guessed.

Read units and nucleus/coda spans are distinct. Onsets and medials are excluded from the tone-bearing pool; the owned coda is retained. Adjacent intervals use the same nearest-sample, half-open boundary. Canonical research audio is 16 kHz mono PCM16; original files and historical segmentation remain intact. All 369 exported clips are sample-exact slices of their hashed canonical research inputs. No timestamp was hand-edited. The MFA folder name is an alignment grouping only: unknown-provenance candidates have null speaker identity in the candidate manifest.

**22 successful recording alignments; 0 recording or unit reconstruction failures; 123 nucleus/coda spans derived.** Derivation is not human acceptance. **37 units have alignment concerns**: 21 have a final under 60 ms, four exceed the native read-unit duration range, one has an extreme phone duration, and 25 belong to prompt/ASR-disagreement recordings. These flags overlap. Native duration thresholds only flag learner material; they do not shorten it. Confidence is unavailable where MFA does not provide it; available likelihood/SNR/duration diagnostics are retained.

**79 units are provenance-quarantined; 108 units have either a provenance hold or an alignment flag**, including overlap. The remaining 15 are merely structurally eligible candidates pending human QA. No unit has a human PASS yet. [Suspicious units](data/generated/learner-alignment-v1/suspicious-units.jsonl) and the source-level exclusion report preserve all reasons, audio/transcript availability, reconstruction status and span derivability. Not-attempted alignment is null, not a failure or a success.

## Label separation and descriptive counts

Intended lexical tone, alignment reading/pinyin, expected surface tone, documented actual-reading hypothesis, realized-tone ground truth, model prediction, human perceptual judgment and historical Benma outputs are separate. Realized-tone ground truth, current predictions and perceptual judgments are all null. For S13, intended 广 guang3 remains T3 while the documented reading hypothesis 贵 gui4 is aligned as gui4. Lexical 个 is T4; contextual neutral expectation is recorded separately. Consecutive T3 chains retain unresolved grouping and alternatives {T2,T3}; no acoustic realization is inferred from text.

| Description | T1 | T2 | T3 | T4 | Neutral | Unresolved / unavailable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Proposed benchmark: intended lexical | 8 | 2 | 15 | 9 | 3 | 7 |
| Proposed benchmark: alignment reading lexical | 8 | 2 | 21 | 10 | 3 | 0 |
| Proposed benchmark: expected surface | 8 | 3 | 7 | 7 | 6 | 13 |
| All QA: alignment reading lexical | 8 | 14 | 68 | 30 | 3 | 0 |
| All QA: expected surface | 8 | 15 | 30 | 16 | 17 | 37 |

Seven intended lexical values are unavailable because the U-shape take has no recovered independent intended-target snapshot. Expected tones for unknown-intent rows are expressly based on their alignment reading hypothesis. Counts describe text/context only; they cannot serve as realized-tone accuracy denominators.

## Exact review instructions

Open [the QA page](data/generated/learner-alignment-v1/qa/index.html) directly in a browser:

`/home/jacob/benma/research/perceptual-tone-model/data/generated/learner-alignment-v1/qa/index.html`

1. Enter your reviewer name. For each of **123 items**, listen through **PLAY CONTEXT**, **PLAY WHOLE TARGET**, and **PLAY TONE-BEARING TARGET**. Replaying is encouraged. Check only whether the target owns the interval and whether the boundaries preserve its material.
2. Whole target: **PASS / START ISSUE / END ISSUE / BOTH / WRONG UNIT**.
3. Tone-bearing target: **PASS / CLIPPED / CONTAMINATED / WRONG UNIT / TOO LITTLE MATERIAL**.
4. Confirm you listened to all three clips. Add boundary/ownership notes for every non-PASS. **Do not classify T1/T2/T3/T4, rate pronunciation, or judge the model.** Pinyin is an independent reading hypothesis.
5. Use **Save draft** to pause; **Resume saved review** restores a packet-bound draft. When all 246 decisions are complete, choose **Export completed QA** and supply `learner-alignment-QA.json` in the next continuation. Export requires all three playbacks and rejects incomplete responses. Browser engineering checks used synthetic events in disposable profiles only, without writing human-answer files.

[Candidate benchmark manifest](data/generated/learner-alignment-v1/candidate-manifest.jsonl):

`/home/jacob/benma/research/perceptual-tone-model/data/generated/learner-alignment-v1/candidate-manifest.jsonl`

The manifest contains both proposed and supplemental units, explicitly distinguished by `selection`; every unit remains ineligible for training/evaluation. Candidate/packet hashes bind the review without claiming a frozen benchmark release.

Candidate SHA-256: `1ce3b7ab9c0c3a4d6d2d4b9f7a78cc5f0c12f2ad6e5e678f8353d7245dc66ba4`

QA packet SHA-256: `bb19f2e047d66bb6b1901c2db0e9d4d21b6a97d8ef9ba2b2f86b3e97e806c24a`

## Validation and production freeze

- 101 Python research tests passed; the 10 learner-specific tests also passed after final release-metadata changes. Coverage includes discovery, duplicate/clip lineage, phrase reconstruction, lexical/surface/hypothesis separation, ownership import, nucleus/coda extraction, contexts, exact sample crops, blinded QA generation, provenance, output-independent selection, release quarantine, duplicate review rejection, and tamper rejection.
- Three existing Node regression files passed; frozen Stage-0 replay is byte-identical.
- Chromium loaded all 123 cards and 369 WAVs, verified exclusive playback, required listening acknowledgment, incomplete export rejection, issue-note requirements and wrong-packet rejection; no horizontal overflow at 390/1280 px. The initial sandbox socket restriction was resolved by approved local browser execution. Narrow-screen control overflow found during the first run was fixed before final validation.
- Ruff and `git diff --check` passed. All **413 deterministic baseline hashes** match; the baseline manifest remains `23177e44e58a3f7c991ee51ac5b4677899ddd71f5a6ef73ecf47a8213d59a52e`.
- 343 original/canonical source-file references and 7,839 native research artifacts match their captured hashes. The production pronunciation path, learner grading, app UI, native test and deployment files are unchanged. The new HTML is an offline research review page only.
- No training on native or learner data, calibration, new learner predictions, native model search, production integration, commit, push or deployment occurred. The existing regression suite includes a disposable synthetic numeric logistic-regression test; it does not load learner/native audio or alter either frozen head.

[Validation details](data/generated/learner-alignment-v1/verification.json) and [construction summary](data/generated/learner-alignment-v1/alignment-summary.json).

## Reproduction and later release

From repository root; use a **new** destination for a new candidate build. Preparation writes the complete archive inventory before alignment. Audio and private artifacts remain ignored.

```sh
P=research/perceptual-tone-model
PY=benchmark/pronunciation_v2/.venv/bin/python
D="$P/data/generated/learner-alignment-next-version"
$PY "$P/scripts/learner_benchmark.py" prepare --root "$D"
sh "$P/scripts/aishell3_mfa.sh" align "$D/corpus" "$D/read-units.dict" \
  mandarin_mfa "$D/aligned" --no_tokenization --num_jobs 2 --no_use_mp \
  --clean --output_format long_textgrid
$PY "$P/scripts/learner_benchmark.py" build --root "$D"
$PY "$P/scripts/learner_benchmark.py" verify --root "$D"
```

**Next step after human QA:** validate the exported packet-bound decisions; preserve non-PASS, unresolved provenance and automatic diagnostic flags as quarantines. Any boundary repair or documentary adjudication requires a new candidate version and affected-unit QA. Then create the versioned evaluation-only release, copying discovery/provenance/exclusion context and recording source, manifest and QA hashes. The release command refuses incomplete/duplicate reviews, altered clips/grids/sources, missing provenance and an existing release directory. It never trains or evaluates.

Only in that later continuation, after the release exists, evaluate the expanded frozen HuBERT model, original frozen pilot and frozen deterministic Benma on the accepted spans. Keep diagnostic and natural strata separate. Without independent realized-tone judgments, report comparisons descriptively; do not compute realized-tone accuracy against intended tones.

```sh
# LATER ONLY, after actual human review; not executed in this pass:
$PY "$P/scripts/learner_benchmark.py" release \
  --root "$P/data/generated/learner-alignment-v1" \
  --answers /path/to/learner-alignment-QA.json --version learner-evaluation-v1
```

## Changed research files

- `configs/learner-benchmark.json`: provenance roles, selection policy, transcript hypotheses, dictionary supplements and release policy.
- `perceptual_tone/learner_benchmark.py`: inventory, deduplication, preparation, alignment import, crops, QA packet, validation and later release gate.
- `scripts/learner_benchmark.py`: prepare/build/verify/release CLI; no inference action.
- `scripts/learner_review.js`: playback, draft/import/export and alignment-only decisions.
- `scripts/learner_review_smoke.cjs`: isolated browser QA regression.
- `scripts/learner_verify.py`: source/native preservation, exact crop and research-only audit.
- `tests/test_learner_benchmark.py`: ten contract/regression tests.
- `learner-domain-benchmark-report.md`: this report.

Generated private artifacts are under `data/generated/learner-alignment-v1/`; superseded local construction drafts are retained separately and are not benchmark releases. All tracked production files remain untouched.

Learner-domain benchmark alignment QA is ready for developer review.
