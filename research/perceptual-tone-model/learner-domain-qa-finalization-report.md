# Learner-domain QA and provenance finalization — 2026-10-19

**Human alignment review is ready: 123 units, 369 existing clips, all QA PENDING. The primary natural candidate set is only three takes / 32 units.** No final benchmark release or learner evaluation exists.

This continuation used the saved construction manifests, source references, alignments and clips. It did not repeat archive discovery, forced alignment or AISHELL experiments. The original `learner-alignment-v1` directory remains byte-for-byte intact across 847 sealed files. An intermediate finalization draft is retained at `data/generated/learner-alignment-review-v2-draft-preserved/`; the current review packet is `data/generated/learner-alignment-review-v2/`.

This report supersedes the earlier construction report's combined 44-unit proposed benchmark and automatic diagnostic-flag quarantine policy. The current primary set contains only documented natural attempts. Diagnostic flags require listening review; they are not structural failures. Use the current finalization CLI and packet below. The historical construction CLI's `release` command and its old release instructions are not the release procedure for this candidate version.

**Canonical inventory and source lineage**

The saved discovery contains **740 audio artifacts and 174 distinct source roots**. There are 175 original-recording files before source deduplication: 171 upload originals plus four sentence-study WAVs. The 168 canonical captures are alternate representations, not additional independent takes. All 343 original/canonical source-file references remain unchanged.

The inventory establishes **eight independent human recordings** from explicit documentation. This is a documented minimum, not a claim that only eight recordings contain humans. Human identity remains unconfirmed for 159 source roots; seven are documented controls. Physical capture alone does not establish human speech or natural intent.

| Provenance category | Archive takes | Selected takes | QA units | Role |
| --- | ---: | ---: | ---: | --- |
| PRIMARY_NATURAL_CANDIDATE | 3 | 3 | 32 | Primary candidates, pending alignment QA |
| DOCUMENTED_DIAGNOSTIC | 2 | 2 | 12 | Supplemental; deliberate-error/test material retained |
| UNKNOWN_PROVENANCE | 162 | 17 | 79 | Supplemental, held from the primary benchmark |
| CONTROL | 7 | 0 | 0 | Excluded from learner candidates |
| Total | 174 | 22 | 123 | 32 primary + 91 supplemental units |

Usability is a separate axis: 113 unknown-provenance sources lack a recoverable transcript and have material category `UNUSABLE`. Thus the disjoint material-category counts are 3 natural, 2 diagnostic, 49 usable-but-unknown, 7 control and 113 unusable. The provenance count of 162 unknown includes those 113 unusable sources.

The [canonical master JSONL](data/generated/learner-alignment-review-v2/master-inventory.jsonl) retains source IDs; every original/canonical path and SHA-256 in `sources`; normalized PCM SHA-256; known intended phrase and transcript hypotheses; speaker and human/control status; historical references; documented intent; source/derivative relationships; alignment and benchmark eligibility; and explicit holds. [Readable master inventory](data/generated/learner-alignment-review-v2/master-inventory.md). The normalized eligibility/category fields are authoritative; inherited discovery fields such as the older `selection` describe the construction snapshot.

Stored audio-asset dates were recovered for 57 sources using already-linked metadata. They are explicitly labeled upload/canonicalization creation times, **not exact microphone capture times**. Missing intent, speaker identity and dates remain null.

The [source lineage graph](data/generated/learner-alignment-review-v2/source-lineage.json) contains source, audio-artifact and historical-metadata nodes, with original/canonical, copy, exact-PCM-clip and metadata-reference edges. It records:

- 130 byte-identical groups, with **247 duplicate copies beyond the first**.
- **168 byte-different whole-source representations beyond the first**.
- **81 distinct exact-PCM clip contents**, represented by 223 clip/copy artifact paths, plus one additional PCM duplicate.
- 51 generated reference/assistant artifacts outside the source inventory and 39 unlinked research artifacts, all excluded from independent learner counts.

These overlapping artifact relationships are not additive take counts. Derivative clips are never independent takes. Arbitrary lossy or pitch-modified derivatives cannot be certified by exact matching; unresolved lineage stays excluded. No new discovery was attempted.

**Take-level provenance and special historical material**

The compact [22-take provenance summary](data/generated/learner-alignment-review-v2/selected-take-provenance.md) gives source IDs, phrases, historical locations, explicit notes and assigned categories. Its [JSONL](data/generated/learner-alignment-review-v2/selected-take-provenance.jsonl) includes hashes and all eligibility fields. Provenance is recorded once per take, not asked 123 times. Unknown cases mean: **UNKNOWN — no historical evidence establishes natural vs diagnostic intent**.

| Original sentence-study take | Documented role | Units | Candidate treatment |
| --- | --- | ---: | --- |
| S01, 今天天气不错，我们出去走走吧。 | Natural baseline | 13 | Primary natural |
| S02, 我昨天晚上跟朋友去吃饭了。 | Natural pace | 12 | Primary natural |
| S03, 你想买哪种水果？ | Natural phrasing | 7 | Primary natural |
| S13, intended 我要去广州。 | Deliberate 广州 → 贵州 substitution | 5 | Supplemental diagnostic |

All four original WAVs remain intact under `/home/jacob/benma-study/`. S13 retains intended `guang3` separately from the documented alignment-reading hypothesis `gui4`; no realized tone is inferred. The other diagnostic take, `40357072`, is the documented U-shape test of 我想买五把雨伞, contributing seven supplemental units.

All six short 我想买 takes (`7e6b6fe9`, `6b5b2135`, `0b194cf9`, `ee8a8b32`, `b9067bec`, `5c70f317`) remain **UNKNOWN_PROVENANCE**, with 18 supplemental units. Stored physical-speech labels do not establish natural-versus-diagnostic intent. No new provenance question or assumption was used.

The dedicated [我想买这个 inventory](data/generated/learner-alignment-review-v2/wo-xiang-mai-zhe-ge-inventory.jsonl) contains exactly seven source rows, including two controls. Every phrase below is 我想买这个; original upload hashes and archive paths are also retained in that inventory. The table's SHA-256 is for the canonical source representation, not a derived clip.

| Take alias / source ID | Canonical recording SHA-256 | Human/control and documentary evidence | Category / alignment / benchmark eligibility |
| --- | --- | --- | --- |
| 89cee47e / 4966e43af7d8a3fb1e682966 | `138433436566bd47b4e7731c43333d6dafa9f7e631b7b168ce954e8ca0f2ae4a` | Historical physical capture; identity and intent unconfirmed | UNKNOWN_PROVENANCE; 5 aligned units pending QA; supplemental only |
| 19d8333b / 9be2abae8812996a15c34742 | `b3e0f2964bb4a9831e008475d184fb7db3fb19b9dc2fd59f2d3547d3566d757d` | Saved numeric physical-smoke capture; identity and intent unconfirmed | UNKNOWN_PROVENANCE; 5 aligned units pending QA; supplemental only |
| bb27924c / 8ad8f3aeeaf7e24bddf0a052 | `488e95d6012120b19e55c8c7d975d3283dc932a89c0aa9ea7e88ea394910c84b` | Measurement-fidelity fixture 430fcc2e; identity and intent unconfirmed | UNKNOWN_PROVENANCE; 5 aligned units pending QA; supplemental only |
| d7b27845 / 983caebc345dff8da92ef921 | `63e67070a2ab1937466900dd5a34da1cefe6c521e74f27912736382603bdd7df` | Explicit human label in 2026-10-12 physical provenance; capture intent absent | UNKNOWN_PROVENANCE; 5 aligned units pending QA; supplemental only |
| 4f1ab9ed / 6411e08e10f9f527b02ca28a | `1d42575f8018458b375dd5aface250290901cc4632b9658cead956bcf44fca51` | Explicit human label in 2026-10-13 physical provenance; capture intent absent | UNKNOWN_PROVENANCE; 5 aligned units pending QA; supplemental only |
| b8049b3e / 413af4751945700509669535 | `7f6bccc7ea7354e8d4a4a49c3d0f53f2bdcfb3054a4d3c0c4077ab0d2f56a16c` | Documented Google TTS physical playback | CONTROL; alignment not selected; excluded |
| cad88597 / d12827abf02a3967ef5fdf70 | `46344042d025f43e1a30bc958b305ed6b4e91cab65b517cc756dbba28038f39f` | Documented Google/background-noise control | CONTROL; alignment not selected; excluded |

Historical frozen deterministic outputs remain separately linked in [historical-benma.jsonl](data/generated/learner-alignment-v1/historical-benma.jsonl), including existing family, abstention, learner color/support and old notes where present. They are absent from the review UI and did not decide selection. The two historical 我 → T4 examples (`8faf1a90`, 我要一个苹果; `a5acd04c`, 我有一个苹果) remain supplemental with unknown intent. No cached learned predictions were used or inspected.

**Alignment diagnostics and candidate status**

Existing forced alignment succeeded for **22/22 takes and 123/123 units**. All **123 tone-bearing nucleus/coda spans** were derived. All **369 playback clips** remain exact source-sample slices. No alignment was rerun and no clip was regenerated in this continuation.

There are **37 flagged units**, **zero structural violations**, and **79 provenance-held units**; eight units belong to both flagged and provenance-held sets. Alignment integrity and provenance eligibility remain independent. No automatic alignment quarantine applies to the current 37 flags. Short spans alone are review prompts.

The [37-row diagnostic report](data/generated/learner-alignment-review-v2/alignment-diagnostics.jsonl) gives unit/source IDs, target, intended and alignment pinyin, reasons, whole and tone-bearing durations, prompt/ASR disagreement, structural validity and human-review requirements. Overlapping flags comprise 21 finals under 60 ms, four read-unit duration flags, one extreme-phone-duration flag and 25 units from prompt/ASR disagreement takes. Human listening must resolve crop integrity.

The [candidate manifest](data/generated/learner-alignment-review-v2/candidate-manifest.jsonl) contains 123 rows with source references/hashes, spans, lineage node, provenance and historical roles, alignment flags, separate label fields, and `qa_status = PENDING`. Every row remains ineligible for training and evaluation. `alignment_quarantined` depends on actual structural violations. Legacy reconstruction rejection reasons are retained as `historical_reconstruction_flags`, while current `exclusion_reasons` contains only structural violations. Realized-tone ground truth, model prediction and human perceptual judgment remain null.

**Descriptive tone metadata**

These counts concern intended text, alignment-reading hypotheses and contextual expectations. They are **not realized-tone ground truth**. Missing intended-target snapshots stay unknown; contextual expectations can use the explicitly recorded alignment-reading hypothesis. Consecutive T3 grouping remains unresolved where the text does not determine it.

| Candidate category / label basis | T1 | T2 | T3 | T4 | Neutral | Unknown or unresolved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Natural / intended lexical | 7 | 2 | 13 | 7 | 3 | 0 |
| Natural / alignment reading lexical | 7 | 2 | 13 | 7 | 3 | 0 |
| Natural / expected surface | 7 | 3 | 4 | 5 | 6 | 7 |
| Diagnostic / intended lexical | 1 | 0 | 2 | 2 | 0 | 7 |
| Diagnostic / alignment reading lexical | 1 | 0 | 8 | 3 | 0 | 0 |
| Diagnostic / expected surface | 1 | 0 | 3 | 2 | 0 | 6 |
| Unknown provenance / intended lexical | 0 | 2 | 2 | 2 | 0 | 73 |
| Unknown provenance / alignment reading lexical | 0 | 12 | 47 | 20 | 0 | 0 |
| Unknown provenance / expected surface | 0 | 12 | 23 | 9 | 11 | 24 |
| Controls / all candidate label bases | 0 | 0 | 0 | 0 | 0 | 0 |

Controls have zero candidate units because they are excluded, not because archive controls lack lexical tones. Seven diagnostic intended labels are unknown because no independent intended-target snapshot was recovered for the U-shape take. None of these counts supports realized-tone accuracy claims.

**Exact developer review instructions**

Open [the current QA HTML](data/generated/learner-alignment-review-v2/qa/index.html):

`/home/jacob/benma/research/perceptual-tone-model/data/generated/learner-alignment-review-v2/qa/index.html`

Enter your reviewer name. For every one of the 123 items:

1. Play **CONTEXT** to locate the target.
2. Play **WHOLE TARGET**.
3. Judge whether it basically corresponds to the intended syllable: **PASS / START ISSUE / END ISSUE / BOTH / WRONG UNIT**.
4. Play **TONE-BEARING TARGET**.
5. Judge only whether the target vowel/final region is intact and correctly owned: **PASS / CLIPPED / CONTAMINATED / WRONG UNIT / TOO LITTLE MATERIAL**.
6. **Do NOT judge tone identity.** Confirm all three clips were heard, and add boundary/ownership notes for every non-PASS decision.
7. Export the finished JSON using **Export completed QA**. Save it as `/home/jacob/Downloads/benma-learner-alignment-qa.json`.

Small coarticulatory onset weirdness is not automatically a failure. A clipped vowel/final matters; wrong-unit material in the tone-bearing region matters. **TOO LITTLE MATERIAL** means there simply is not enough trustworthy target nucleus/coda evidence. This is crop-integrity review, not pronunciation grading or T1/T2/T3/T4 classification.

The page preserves the existing layout, shows phrase/target/pinyin/source/category, and uses deterministic randomized ordering independent of flags. Flags are not visually labeled as bad. Predictions, probabilities, historical grades and correct-tone verdicts are absent. Use **Save draft** and **Resume saved review** to pause. Listening flags require each clip to finish. The export includes the packet hash, item hash, unit and source IDs, both decisions, notes, three heard flags, reviewer and per-item timestamp, plus the original diagnostic flags. Unchanged repeated exports and import/export round trips are byte-identical; timestamps change when review content changes.

The browser proposes the filename; choose the Downloads location above when saving. No human review JSON has been fabricated or written there. Browser tests used a disposable profile and synthetic events only.

**Validation and production freeze**

The earlier **101 passing Python tests**, original browser checks, three Node regression files and byte-identical frozen deterministic replay remain preserved in the construction report/logs. Only the new nine focused finalization tests and relevant browser checks were run for this continuation. All nine passed, covering natural-only eligibility, unknown/control handling, review flags versus structural failures, distinct label fields, candidate and packet reproducibility, deterministic lineage, review identity/hash/heard gates, saved-metadata dates, and absence of model/discovery/alignment calls.

Chromium loaded all 123 cards and 369 clips; checked exclusive playback, three listened flags, required issue notes, hidden diagnostic flags, visible source IDs, item-hash tamper rejection, deterministic export and import/export round trips; and found no horizontal overflow at 390 or 1280 pixels. [Browser evidence](data/generated/learner-alignment-review-v2/browser-tests.log), [Python test evidence](data/generated/learner-alignment-review-v2/python-tests.log), [preview](data/generated/learner-alignment-review-v2/qa/browser-preview.png), and [verification](data/generated/learner-alignment-review-v2/verification.json).

Verification confirms all **413 deterministic baseline hashes**, all **343 source-file references**, all **7,839 pinned native artifacts**, and all **847 completed construction files** unchanged. Every existing playback clip was checked against its source samples. Ruff, JavaScript syntax checks and `git diff --check` passed, including whitespace checks for new research files. Production pronunciation inference, learner grading, application UI and deployment files are unchanged; all workspace changes belong to the research package.

The two recognizers remain hash-pinned and were not deserialized for learner scoring:

| Frozen recognizer | SHA-256 |
| --- | --- |
| `models/generated/aishell3-multispeaker-fixed-v2/experiment_B.joblib` | `b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b` |
| `models/generated/aishell3-first-four-tone-v1/model2_hubert.joblib` | `c20cc46ed715ce5ed1f3a76f405014069f4a98c0b9e6e467ce28635b4df725d9` |

No learner inference, probability inspection, training, adaptation, production modification, immutable benchmark release, commit, push or deployment occurred in this continuation. The earlier 101-test suite included a disposable synthetic numeric classifier regression test; no such fitting was repeated here, and neither native nor learner models were trained.

Current candidate SHA-256: `3e341d256fe76fb73c5ba19930866f00b132d2806b58de7984117e8a81419891`.

Current packet SHA-256: `d1a1da3a3dd777c5eceb6ec3bde67fb59235b10f83d13690a5c12a65c4c9c8de`.

Lineage SHA-256: `1dc230dee12ebee4c60f3551615fc4c9ccf1bcea866f31fbfe79f11bdef39da0`.

**Changed research files and next step**

This continuation adds:

- `perceptual_tone/learner_finalization.py`: canonical inventory, lineage, categories, current candidate metadata, packet, reports, review validation and preservation verification.
- `scripts/learner_finalize.py`: build / verify / validate-review only; no release or inference action.
- `scripts/learner_review_v2.js`: source-bound review export, stable timestamps, heard gates and draft import.
- `scripts/learner_review_v2_smoke.cjs`: disposable browser checks.
- `tests/test_learner_finalization.py`: nine focused contracts.
- `learner-domain-qa-finalization-report.md`: this handoff.

The pre-existing uncommitted construction files remain preserved: `configs/learner-benchmark.json`, `perceptual_tone/learner_benchmark.py`, `scripts/learner_benchmark.py`, `scripts/learner_review.js`, `scripts/learner_review_smoke.cjs`, `scripts/learner_verify.py`, `tests/test_learner_benchmark.py`, and `learner-domain-benchmark-report.md`. Generated private artifacts remain under ignored `data/generated/` directories. No tracked production file changed.

After developer QA, return `/home/jacob/Downloads/benma-learner-alignment-qa.json`. First verify inputs and validate that export against the current packet:

```sh
PYTHONPATH=research/perceptual-tone-model \
  benchmark/pronunciation_v2/.venv/bin/python \
  research/perceptual-tone-model/scripts/learner_finalize.py verify

PYTHONPATH=research/perceptual-tone-model \
  benchmark/pronunciation_v2/.venv/bin/python \
  research/perceptual-tone-model/scripts/learner_finalize.py validate-review \
  --answers /home/jacob/Downloads/benma-learner-alignment-qa.json
```

Then adjudicate non-PASS crops and actual structural issues, preserving human decisions independently from automatic flags. Boundary repairs require a new candidate version and affected-unit review. Human PASS may clear an alignment concern; it cannot establish provenance. Keep diagnostic material separate and unknown-provenance takes outside the primary natural set. Once those decisions are complete, a subsequent pass can implement and create the immutable natural/supplemental release with source, candidate and review hashes under this policy. Do not use the legacy release gate. Learner scoring remains a separate later task after an accepted release; this handoff makes no domain-transfer or accuracy claim.

Learner-domain benchmark alignment QA is ready for developer review.
