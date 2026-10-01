# Experiment 3 bounded source audit

No trustworthy fresh panel can be sealed from the audited inventory. This is a
bounded feasibility finding, not a claim that no suitable recording exists online.
The frozen lexical labels remain benchmark truth. No model output, listening,
F0 inspection, cropping or new audio download influenced this audit.

## 1. Existing Lingua Libre / Wikimedia inventory, then bounded live checks

Reverified the cached 2026-09-28 snapshots: 9,363 unique Commons pages and 1,710
single-character revision audits. Audited all 23 Lingua Libre speaker display
names visible in that larger inventory, including names absent from the earlier
single-character ledger. Stable voice IDs come from speakerId/locutorId, never
uploader counts. All original file/revision/license links, source hashes and
attribution are retained in `candidate-items.csv`; source snapshot SHA-256s are in
`source-audit.json`. `exclusions.csv` records every one of 1,792 audited items
(1,710 Commons plus 82 OMPAL sentences). `candidate-speakers.csv` also includes
inventory-only leads and previous speakers, clearly flagged.

Exclude ALL recordings from the seven previously substantial speakers, including
unused recordings by Jouketou, 雲角 and Fake estate. An unseen clip by an inspected
speaker does not satisfy this experiment's fresh-speaker requirement. Conservatively
exclude previous auxiliary/singleton groups too. Do not recycle the opened 118.

| New profile | ID | Inventory / audited items | Eligible T1/T2/T3/T4 | Accepted isolated-file license | Mandarin native status |
| --- | --- | --- | --- | --- | --- |
| Vickylin77amis | Q19761 | 25 / 8 | 1/0/2/0 | CC BY-SA 4.0 | UNKNOWN |
| Assassas77 | Q4250 | 19 / 12 | 0/0/1/1 | CC BY-SA 4.0 | UNKNOWN; see below |
| BlueCamille | Q927785 | 27 / 1 | 0/1/0/0 | CC BY-SA 4.0 | UNKNOWN |
| Yug | Q480 | 11 / 2 | 0/0/1/0 | CC BY-SA 4.0 | UNKNOWN |
| Yihsiangyang | Q190194 | 3 / 1 | 0/0/0/0 | CC BY-SA 4.0 on audited file | UNKNOWN; polyphonic reading excluded |
| Shangkuanlc | unresolved | 240 / 57 | 0/0/0/0 | None accepted by inherited strict parser | UNKNOWN; unresolved stable voice ID |

Seven eligible isolated items across four profiles are insufficient. No profile
has eight items in every tone. These are metadata counts, not downloaded or
acoustically certified clips, and not newly discovered people relative to the
previous metadata audit. They are candidates new to the model's speaker history.

Shangkuanlc warrants a precise distinction: cached file revisions explicitly name
the speaker, but leave speakerId blank. Their license blocks use
`{{ cc-by-sa-4.0 }}` with whitespace, which the inherited narrow license parser does
not accept. This is a parser limitation, **not evidence that the recordings lack
a license**. Independent raw-metadata inspection supports a CC BY-SA 4.0 grant.
The 57 audited targets contain 34 unambiguous readings (13/8/6/7) and 23 ambiguous
readings. Even resolving the license parser and voice-ID issue would leave T3 and
T4 below the fixed minimum, and supply only one prospective substantial speaker.
Do not invent a stable ID or silently relax the threshold. The current
[Commons profile](https://commons.wikimedia.org/wiki/User:Shangkuanlc) does not
establish a Mandarin-native declaration or a stable Lingua Libre profile mapping.

The bounded live check comprised two search queries (Commons Mandarin Lingua
Libre speakers; the OMPAL owner repository), the Shangkuanlc, Assassas77 and
Vickylin77amis user-page opens, and one Shangkuanlc file-page open. Vickylin77amis
and the file-page open failed in the browser tool. No broad category refresh,
automated scrape, authenticated access or identity investigation followed.

[Assassas77's public profile](https://commons.wikimedia.org/wiki/User:Assassas77)
self-reports native French and intermediate Chinese. Retain this evidence; it
argues against treating the profile as native-Mandarin-verified but does not
explicitly establish Mandarin acquisition history. Native status remains UNKNOWN.
Names, geography and broad Chinese proficiency are not substituted for evidence.
A search also surfaced a newer [Yug 谁 recording](https://commons.wikimedia.org/wiki/File:LL-Q9192—Yug—谁.wav)
with CC0. It was not promoted into the eligible ledger: this is one existing
candidate profile, with insufficient all-tone coverage and no newly audited
singleton reading/revision. A search result is not a sealed asset.

Additional inventory-only names, all with zero **audited eligible** T1–T4 items:

| Display name | Inventory items | API license short field (not independently accepted per-file grant) | Blocker |
| --- | ---: | --- | --- |
| Cookai1205 | 29 | CC0 | Latin-letter names and multi-character targets |
| XtexChooser | 7 | CC BY-SA 4.0 | Multi-character targets |
| Aa087159 | 4 | CC BY-SA 4.0 | No unqualified single-character candidate in cached audit |
| Liang | 3 | CC0 | Multi-character targets; recorder is MichaelSchoenitzer |
| KhawaChenpo | 3 | CC BY-SA 4.0 | No unqualified single-character candidate in cached audit |
| Bakerkobe | 1 | CC BY-SA 4.0 | Multi-character singleton |
| Lim Natee | 1 | CC BY-SA 4.0 | Qualified 車 (chē), not conservative singleton reading |
| Zhjiang1103 | 1 | CC0 | Hello, not Mandarin isolated lexical tone target |
| Kokhanloong2019 | 1 | CC BY 4.0 | Broad zho language code and multi-character singleton |

Native status is UNKNOWN for these nine leads. Zero eligible counts mean no
eligible audited asset, not a claim that their unaudited audio contains no tones.
There is also one unresolved non-Lingua-Libre record, with no reliable voice ID;
it is not counted as a new person. Exact titles and source metadata remain in the
hash-pinned local inventory. Tiny groups are not promoted to satisfy a quota.

## 2. Previously documented GREEN sources

Reviewed the existing reconnaissance dataset/licensing documents and the
feasibility source audit. The existing permissive Shtooka groups are Wei Gao and
Yue Tan; both are previously inspected. Other unidentified Commons voices still
lack individual voice/label provenance. The documented additional GREEN corpus
is OMPAL. Common Voice, FLEURS, AISHELL, THCHS and FSI/DLI retain their previously
documented conditional rights, identity or segmentation blockers; this pass does
not reclassify them from a web snippet or obtain a large archive. A proposed new
native micro-corpus is not an existing licensed collection.

## 3. OMPAL feasibility under the no-cropping constraint

Verified cached README, LICENSE, tree and native annotations against their saved
SHA-256 receipts and the pinned Git blobs at
[`c3aaa9e892e4b1c2a25b637401f52f6e35b53e74`](https://github.com/phantomhsieh/OMPAL-corpus/tree/c3aaa9e892e4b1c2a25b637401f52f6e35b53e74).
The [owner README](https://github.com/phantomhsieh/OMPAL-corpus) corroborates the
three native speakers, 46 French-L1 learners and distinction between tone
correctness and lexical tone identity. Preserve Hsieh et al.'s attribution and
[CC BY 4.0 license](https://github.com/phantomhsieh/OMPAL-corpus/blob/c3aaa9e892e4b1c2a25b637401f52f6e35b53e74/LICENSE).

| Native speaker ID | Original sentence files, previously locally acquired | Eligible isolated T1/T2/T3/T4 |
| --- | ---: | --- |
| SPEAKER01001 | 20 | 0/0/0/0 |
| SPEAKER01002 | 29 | 0/0/0/0 |
| SPEAKER01003 | 33 | 0/0/0/0 |

These 82 recordings have sentence transcripts without syllable timestamps. Four
retain upstream word/text mismatches (00100217, 00100218, 00100222, 00100322).
Whole sentences have no single lexical class. A segmentation study would require
a separate boundary/context protocol and would change the present no-cropping,
isolated-target design. Do not manufacture class labels from correctness scores
or silently assign a sentence's first character tone. There is no defensible
OMPAL isolated panel under this pass's constraints. The 46 learner folders remain
inventory-only; their tone coverage has not been audited and is not reported as
zero. OMPAL anonymous IDs also do not prove absence of cross-source aliases.

## Decision and untouched material

No new manifest or seal was created; no SHA-256 is represented as a fresh-panel
seal. A future bounded acquisition pass needs at least three new independently
identified speakers, with eight eligible targets per tone each, and exact licenses,
provenance, duplicate checks and decode verification before deterministic selection.
Human realized-tone listening is optional, not a prerequisite for fitting the head.

All candidate audio remains untouched by either Experiment 3 head. The seven
sparse Commons assets were not acquired here. OMPAL's previously cached original
waveforms were not decoded, cropped, embedded or predicted in this pass. Neither
head accessed the opened 118 or Luilui in this pass; those sets remain historically
inspected. Only original training/Levi waveforms are used for linear reproduction.
The nonlinear head sees synthetic fixtures only during preflight.
