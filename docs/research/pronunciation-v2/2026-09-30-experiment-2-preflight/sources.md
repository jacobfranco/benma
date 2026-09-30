# Bounded source and label audit

This pass reuses the 2026-09-28 Commons inventory (9,363 unique page IDs) and its
1,710 cached single-character revision audits. It does not launch another inventory
or broad scrape. Exact input hashes and local acquisition receipts are in
`provenance.json`. `candidate-items.csv` preserves the original preselection bytes;
`audited-items.csv` adds local audio verification to that item-level ledger;
`candidate-speakers.csv` separates metadata-eligible, locally available and sealed
counts. A missing accepted license in an excluded row means no grant accepted under
this pass's policy; it does not assert that the source has no published license.

## OMPAL

Author-owned repository, pinned to
[`c3aaa9e892e4b1c2a25b637401f52f6e35b53e74`](https://github.com/phantomhsieh/OMPAL-corpus/tree/c3aaa9e892e4b1c2a25b637401f52f6e35b53e74).
The [README](https://github.com/phantomhsieh/OMPAL-corpus/blob/c3aaa9e892e4b1c2a25b637401f52f6e35b53e74/README.md)
explicitly identifies three native Mandarin speakers and 46 French-L1 learners.
The [LICENSE](https://github.com/phantomhsieh/OMPAL-corpus/blob/c3aaa9e892e4b1c2a25b637401f52f6e35b53e74/LICENSE)
grants CC BY 4.0. Preserve Hsieh et al.'s author credit, repository/revision links,
license notices and modification notices for any future crops. The
[CC BY deed](https://creativecommons.org/licenses/by/4.0/) permits copying and
adaptation, including commercial use, subject to attribution and other terms.

| Native source ID | Repository WAVs / locally verified | Valid isolated T1/T2/T3/T4 clips |
|---|---:|---|
| SPEAKER01001 | 20 / 20 | 0 / 0 / 0 / 0 |
| SPEAKER01002 | 29 / 29 | 0 / 0 / 0 / 0 |
| SPEAKER01003 | 33 / 33 | 0 / 0 / 0 / 0 |

Direct inspection of the pinned `native_scores.json` finds sentence transcripts of
5–21 characters for all 82 records. Word arrays give written units, not pinyin or
time boundaries. There is no trustworthy single T1–T4 class for a complete sentence.
The existing `tone` values are human correctness annotations and are never consulted
by the label/selection code. The audio tree, README, LICENSE and native annotations
are verified against pinned Git blob hashes; all 82 native WAVs (8,085,124 source
bytes) are locally copied unchanged and decoded. Their `source_sha1` values are Git
blob SHA-1s, unlike the raw-file Commons SHA-1s; audio SHA-256s are ordinary file hashes.

Four native records additionally have mismatching sentence text versus concatenated
word text: `00100217`, `00100218`, `00100222`, `00100322`. Preserve both upstream
forms in the local original JSON; do not silently repair them. All 82 are excluded
from the isolated test, with these four carrying a second exclusion reason.
Unambiguous dictionary readings for individual characters would still need verified
syllable boundaries and contextual/sandhi handling before becoming cropped examples.
No alignment, crop, forced pronunciation, model inference or listening occurred.

The 46 learners / 1,768 WAVs are inventoried by folder only. They are explicitly
LEARNER, not UNKNOWN; item labels and audio were not acquired/audited. Blank tone
counts in those speaker rows mean **not audited**, not absence of those tones.
Do not import the corpus's own train/test partitions into Benma's split.
Anonymous corpus IDs cannot independently resolve aliases to Wikimedia accounts.

## Lingua Libre / Wikimedia

The file revision's `speakerId` or legacy `locutorId` identifies the voice; uploader
is not assumed to be the speaker. Audit languageId Q9192/Q727694, transcription,
qualifier and filename/template agreement. Every accepted label comes from one
unambiguous pypinyin 0.55.0 numbered reading (heteronym=True, neutral tone as 5).
Multiple readings are excluded, including same-tone alternate pronunciations.
These are lexical target labels, not claims about acoustic correctness.

| New substantial profile | Native status | Metadata-valid T1 / T2 / T3 / T4 | Fixed selected T1 / T2 / T3 / T4 |
|---|---|---|---|
| Jouketou — Q1332695 | UNKNOWN | 27 / 20 / 19 / 26 | 10 / 10 / 10 / 10 |
| 雲角 — Q19614 | UNKNOWN | 18 / 13 / 15 / 14 | 10 / 10 / 10 / 10 |
| Fake estate — Q812770 | UNKNOWN | 21 / 9 / 9 / 17 | 10 / 9 / 9 / 10 |

All 208 eligible items from these three speakers have explicit per-file CC BY-SA 4.0
grants in the cached revisions. Relevant examples are the actual
[Jouketou 等 file](https://commons.wikimedia.org/wiki/File:LL-Q9192_(cmn)-Jouketou-%E7%AD%89.wav),
[雲角 你 file](https://commons.wikimedia.org/wiki/File:LL-Q9192_(cmn)-%E9%9B%B2%E8%A7%92-%E4%BD%A0.wav)
and [Fake estate 砸 file](https://commons.wikimedia.org/wiki/File:LL-Q9192_(cmn)-Fake_estate-%E7%A0%B8.wav).
Grants rest on exact revision URLs and templates in the cached evidence, never a
category. All selected assets' individual revision URLs are retained in the ledger
and their source metadata is copied into `selected-source-evidence.jsonl`.

The [CC BY-SA 4.0 terms](https://creativecommons.org/licenses/by-sa/4.0/) permit
copying/adaptation with attribution, license/change notices and applicable
ShareAlike obligations when distributing adaptations. This pass makes an explicit
**evaluation-only** policy distinction: the earlier pilot deferred ShareAlike over
learned-weight questions. No such asset enters fitting, tuning or calibration here,
and this pass does not change that training policy or settle learned-weight rights.
Keep unchanged originals and attribution together. Future distributed derived audio
must preserve the applicable license. The repository's proprietary code license
does not relicense these source recordings.

The native-status lookup of the three public Commons user pages was unavailable
through the browser tool. No explicit Mandarin-native declaration was established
from the inspected cached records. Names, locations and accent are not evidence.
The profile IDs are distinct from every prior corpus speaker, and the names reveal
no known alias collision. Public pseudonyms are not proof of unique biological
identity; there is no known overlap, not a biometric guarantee.

Additional sparse, audited new Lingua Libre groups:

| Profile | Metadata-valid T1 / T2 / T3 / T4 | Role |
|---|---|---|
| Vickylin77amis — Q19761 | 1 / 0 / 2 / 0 | Sparse metadata reserve |
| Assassas77 — Q4250 | 0 / 0 / 1 / 1 | Sparse metadata reserve |
| BlueCamille — Q927785 | 0 / 1 / 0 / 0 | Sparse metadata reserve |
| Yug — Q480 | 0 / 0 / 1 / 0 | Sparse metadata reserve |
| Yihsiangyang — Q190194 | 0 / 0 / 0 / 0 | Ambiguous reading excluded |

Native status is UNKNOWN for each. The seven eligible sparse items have CC BY-SA
4.0 grants; they fail the predeclared per-speaker coverage rule and were not acquired.
Shangkuanlc entries lack a resolvable speaker-profile association in this cache and
remain excluded, regardless of uploader/author names. No singleton is promoted by
assuming the uploader is the voice.

## Previously used speakers, Shtooka and other researched sources

Exclude Wei Gao, CanonNi, Levi Highway and Luilui6666 in every final-manifest path.
Also exclude the four historical auxiliary/singleton groups (Xudong Yang/Wyverald,
Wang Cheng, Jun Da, Yue Tan) conservatively, because they were already audited in
Experiment 1. The historical Yue Tan/Wei Gao metadata conflict remains quarantined;
no existing clip is deleted or relabeled. Shtooka's otherwise large second group is
Yue Tan, not a newly unexamined speaker. Its CC BY-SA 3.0 US records are not covered
by the narrowly implemented Lingua Libre CC BY-SA 4.0 evaluation grant.

The bounded existing reconnaissance documents OMPAL as the other usable corpus.
FSI/DLI still has rights/authorship and speaker/segmentation blockers; FLEURS,
Common Voice, AISHELL and other conditional sources are not newly cleared here.
See the existing [dataset audit](../2026-09-28-reconnaissance/datasets.md) and
[asset licensing audit](../2026-09-28-data-feasibility/licensing.md).
No paid data, new platform integration or broad internet scrape was used.

For explicitly native material, the strongest next source is the acquired OMPAL
native reserve after a separate manual boundary, transcript and contextual-reading
audit. It would remain a connected-speech-derived evaluation with that limitation;
it cannot be silently substituted for this isolated-target panel.
