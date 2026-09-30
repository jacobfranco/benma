# Experiment 2 preflight outcome

**Acquisition finished: 118/118 preselected Wikimedia clips are locally present,
integrity-verified and eligible for the sealed evaluation panel.** The resumed pass
found that the earlier conservative downloader had already completed. It made no
additional network requests and did not restart selection. This is a fresh-speaker
lexical-target evaluation, with native status UNKNOWN; it is not a certified native
Mandarin or acoustically verified realized-tone benchmark.

| New evaluation speaker | Explicit profile ID | Native status | T1 | T2 | T3 | T4 | Total |
|---|---|---|---:|---:|---:|---:|---:|
| Jouketou | lingualibre:Q1332695 | UNKNOWN | 10 | 10 | 10 | 10 | 40 |
| 雲角 | lingualibre:Q19614 | UNKNOWN | 10 | 10 | 10 | 10 | 40 |
| Fake estate | lingualibre:Q812770 | UNKNOWN | 10 | 9 | 9 | 10 | 38 |
| **Total** | **3 speakers** | | **30** | **29** | **29** | **30** | **118** |

The complete panel is `sealed-test-manifest.csv`; its successful finalization and
UTC sealing timestamp are recorded in `seal.json`. Exact manifest SHA-256:

```text
7e9ba24601a1199ad07f721e9ca9cb22ef5736095a0fdb2b44091aa143dce75d
```

Source audio totals 9,819,598 bytes and 106.711651 seconds, with clip durations
0.620862–1.221678 seconds. Raw audio remains ignored, local/cache-only under
`benchmark/corpus/recordings/original/experiment-2-preflight/commons/`. No raw audio
is staged. No commit or push was made.

## License, labels and contamination

Every selected recording has an exact per-file **CC BY-SA 4.0** grant. The user
explicitly authorized evaluation-only use during this resumed pass. Preserve
speaker/recorder attribution, source and revision URLs, license metadata and notices;
state any future audio modifications and meet ShareAlike obligations for distributed
adaptations. This is **not permission for training use or released model weights**;
those require a separate license review. Source metadata and grants are preserved
in `selected-source-evidence.jsonl`, with per-row attribution in the manifest.

Labels derive from the exact Lingua Libre single-character Mandarin transcription,
cross-checked against its filename and language ID. pypinyin **0.55.0**, TONE3,
heteronym=True and neutral_tone_with_five=True, must return exactly one reading;
only its lexical tone 1–4 qualifies. Multiple readings, even same-tone alternate
readings, are excluded. No pronunciation-correctness field, V1 output, wav2vec
output or expected-tone-aware pooling informs labels or selection. Dictionary
labels do not certify connected-speech surface tones or that a speaker realized
the target correctly.

The three explicit source-profile IDs and known names are disjoint from Wei Gao,
CanonNi, Levi Highway and Luilui6666, plus all four prior auxiliary/singleton groups.
There are no source-ID, source SHA-1, original SHA-256 or decoded-PCM SHA-256
duplicates within the panel or against all 500 historical corpus rows. There are
no duplicate speaker/text/pinyin triples. Lexical overlap across distinct speakers
is permitted. This establishes source-record speaker independence with no known
alias overlap; public pseudonyms cannot guarantee distinct biological identities,
and exact hashes cannot detect every transformed copy.

Selection remains exactly the pre-acquisition rule in `selection.json`: use the
existing 1,710-item cached Commons audit; retain speakers with at least eight
unambiguous candidates in every tone; rank each speaker-tone cell by SHA-256 of its
source asset ID, then ID; take up to ten. The original 118 IDs and original
`candidate-items.csv` bytes are unchanged. Audio verification fields are added to
the separate `audited-items.csv`. No replacements occurred after the initial 429.
The final CSV sorts by `(speaker_id, source_asset_id)` with fixed columns, UTF-8 and
LF newlines. The tool refuses to overwrite a seal; incomplete acquisition produces
a blocked status and no sealed manifest.

## Exclusions and reserve speakers

The item audit contains 1,792 records: 1,710 Commons candidates plus 82 OMPAL native
sentences. Exactly **1,674 records are outside the 118-row final test**. Reason counts
below overlap because an item can have multiple issues; they are not additive.

| Exclusion category | Records |
|---|---:|
| Previous experiment speaker or audited singleton | 1,202 |
| ShareAlike grant outside this narrowly accepted evaluation policy | 543 |
| Ambiguous/polyphonic dictionary reading | 447 |
| Filename/template conflict | 109 |
| Outside fixed speaker coverage or per-tone cap | 97 |
| Connected speech without syllable boundaries | 82 |
| Unknown speaker association | 58 |
| Unknown pronunciation | 10 |
| Unresolved label | 10 |
| OMPAL word-text/transcript mismatch | 4 |
| Metadata/dictionary conflict | 3 |
| Non-Lingua-Libre identity requiring individual audit | 1 |

There are **zero** missing selected files, decode failures, duplicate hashes,
neutral-tone inclusions or unresolved label/licensing exclusions among the final
118 clips. The 543 ShareAlike exclusions are not a claim that ShareAlike forbids
research: they retain the earlier source-specific deferral for CC BY-SA 3.0 US or
insufficiently corroborated grants, while selected Lingua Libre CC BY-SA 4.0 files
pass the explicit evaluation-only policy. Four tiny new Lingua Libre reserves have
seven metadata-valid items total: Vickylin77amis (T1=1,T3=2), Assassas77 (T3=1,T4=1),
BlueCamille (T2=1), Yug (T3=1). Native status remains UNKNOWN; none was acquired or
promoted into the final test. Yihsiangyang's candidate is ambiguous. See
`candidate-speakers.csv`, `exclusions.csv` and [sources.md](sources.md) for exact IDs
and provenance, including unresolved speaker records.

**OMPAL reserve:** all 82 unchanged native sentence WAVs from explicitly native
SPEAKER01001/01002/01003 (20/29/33 files) are local, hash-verified and decoded,
under CC BY 4.0. None enters this test; all lack trustworthy syllable timestamps.
The four transcript mismatches remain recorded: `00100217`, `00100218`, `00100222`,
`00100322`. No syllable crops or labels were manufactured. These are the best next
explicitly native source for a separate manual segmentation/contextual-label audit.
The 46 explicitly identified French-L1 learners and their 1,768 WAVs are inventoried
only; their audio and item annotations were not acquired in this pass.

## Frozen comparison and next execution

The authoritative, hashed specification is [protocol.md](protocol.md). Both arms
use frozen `facebook/wav2vec2-base` revision
`0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`, CPU FP32, layer 8, identical mono
16-kHz preprocessing, no trimming/augmentation, one unpadded clip per forward,
training-only StandardScaler, and multinomial L2 logistic regression C=0.1.

* **A:** valid-frame whole-clip mean, 768 dimensions.
* **B:** for N valid chronological frames, boundaries are
  `(0, N//3, (2*N)//3, N)`; mean each half-open bin and concatenate first/middle/final
  means, 2,304 dimensions. N<3 stops both arms; no empty-bin padding, repetition or
  denominator mismatch. The model-free boundary reference and synthetic tests are
  in the new preflight tooling. No temporal representation was computed on real
  evaluation audio.

Keep seed=20260929, lbfgs, no class weights, max_iter=3000 and tol=1e-8; no tuning.
The 386 original training clips remain fixed. Future reporting keeps development /
source-held-out diagnostics, new pristine speakers, and Luilui's inspected stress
set separate. Predeclared metrics include accuracy, balanced accuracy, macro F1,
per-tone precision/recall/F1 and confusion matrices, with directed T2/T3 and T3/T4
confusions and per-speaker results. Fresh-speaker performance and absence of a major
new per-tone regression determine whether B is promising. Luilui improvement alone
cannot justify model selection. No arbitrary numeric success threshold is added.

**Untouched by models:** all 118 new evaluation clips and all 82 acquired OMPAL
native sentences. No encoder was loaded, classifier trained, predictions opened,
F0 extracted or listening-based selection performed. Luilui remains unchanged as a
named, previously inspected diagnostic/stress set; production/API/mobile behavior
is untouched. Neural F0 is only a separate future proposal, not part of Experiment 2.

Next execution pass: first run the offline seal verifier below; implement and test
the isolated A/B extraction against synthetic frames, reproduce A on development,
then fit/hash the two fixed heads using only original training data. Only after
those locks should that next pass open the new test once and report all three panels
separately. This preflight does not authorize or perform that model execution.

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/evaluation_preflight.py verify
```

## Reproduction and validation

Historical preparation and acquisition commands, **not needed again now**:

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/evaluation_preflight.py prepare --allow-sharealike-evaluation-only
services/api/.venv/bin/python benchmark/pronunciation_v2/evaluation_preflight.py acquire --source ompal
services/api/.venv/bin/python benchmark/pronunciation_v2/evaluation_preflight.py acquire --source commons
services/api/.venv/bin/python benchmark/pronunciation_v2/evaluation_preflight.py acquire --source commons --resume-after-stop
```

The initial Commons invocation stopped on HTTP 429 after three clips. One explicit
resume waited at least 60 seconds, then spaced new requests 60 seconds apart and
completed all 118. The preserved stop JSON is historical and resolved, not a current
missing-data claim. Successful files and receipts are preserved; there were no
substitutions, rotated identities or alternate mirrors. No acquisition remains to
resume. All network activity belongs to the acquisition pass, not resumed sealing.

Focused validation uses the existing research environment, without production
tests or model imports:

```sh
PYTHONPATH=benchmark/pronunciation_v2 services/api/.venv/bin/python -m pytest benchmark/pronunciation_v2/test_evaluation_preflight.py benchmark/pronunciation_v2/test_pilot.py benchmark/pronunciation_v2/test_preflight.py -q
.venv/bin/ruff check benchmark/pronunciation_v2/evaluation_preflight.py benchmark/pronunciation_v2/test_evaluation_preflight.py
.venv/bin/ruff format --check benchmark/pronunciation_v2/evaluation_preflight.py benchmark/pronunciation_v2/test_evaluation_preflight.py
```

Results: **93 tests passed**, Ruff lint and formatting passed. This research tooling's
established static checks are Ruff; it has no existing strict mypy invocation for
the standalone acquisition scripts. No broad production typecheck is represented
as having passed. Provenance records the research code and source input hashes.
