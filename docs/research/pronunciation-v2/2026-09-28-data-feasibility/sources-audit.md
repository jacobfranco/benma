# Source audit — 2026-09-28

Scope: concrete zero-budget acquisition, without reopening the model architecture. Counts below derive from this pass's API snapshots, not search snippets. Cache: `/tmp/benma-pronunciation-v2-pilot/`. The aggregate hashes are in [inventory-summary.json](inventory-summary.json).

## Wikimedia Commons and Lingua Libre

Six direct category inventories were exhausted using `categorymembers` continuation, then merged by Commons page ID:

| Category | Direct file members |
|---|---:|
| [Chinese pronunciation](https://commons.wikimedia.org/wiki/Category:Chinese_pronunciation) | 5,160 |
| [Mandarin pronunciation](https://commons.wikimedia.org/wiki/Category:Mandarin_pronunciation) | 45 |
| [Lingua Libre pronunciation-cmn](https://commons.wikimedia.org/wiki/Category:Lingua_Libre_pronunciation-cmn) | 4,122 |
| [Lingua Libre pronunciation-zho](https://commons.wikimedia.org/wiki/Category:Lingua_Libre_pronunciation-zho) | 4 |
| [Shtooka Mandarin](https://commons.wikimedia.org/wiki/Category:Audio_files_from_Shtooka_Project_(Mandarin)) | 3 |
| [Tones of Standard Chinese](https://commons.wikimedia.org/wiki/Category:Tones_of_Standard_Chinese) | 38 |

The union is **9,363 pages**, not 9,372 independent clips. This is an explicitly bounded category inventory, not proof that all Mandarin audio anywhere on Commons was found. The broad Chinese category includes other varieties and non-audio diagrams. Their inclusion in discovery never establishes eligibility.

The [current Lingua Libre project announcement](https://commons.wikimedia.org/wiki/Commons:Lingua_Libre) establishes Commons as its primary metadata store after the 2026 migration. Old `lingualibre.org/api.php` returned an application shell, and one old speaker-profile request returned HTTP 426; neither was treated as valid metadata or bypassed. The current gallery's own data endpoint reported an older aggregate of **3,864 Mandarin recordings / 20 speakers**. That is not the current file count and is not added to Commons totals. Endpoint used by the official gallery: [published gallery data](https://hugolpz.github.io/Sparql2Data/data/languages-gallery.json).

The live Commons Lingua Libre subset has **4,126 files**: 4,122 `cmn`, four broader `zho`. Filename language IDs are 3,875 Q9192, 247 Q727694, four Q7850. [Q727694](https://www.wikidata.org/wiki/Q727694) denotes Standard Chinese and is eligible for Mandarin inspection; broad Q7850 alone is insufficient. Actual `speakerId` / legacy `locutorId`, `transcription`, `languageId`, qualifier and license blocks are inspected for single-character candidates. Both labels and license options can be lost if only filenames or the API short license are used.

Commons imageinfo's `user` identifies an uploader, not necessarily a speaker. Lingua Libre's recorder and speaker can differ (for example, Yug recording Wang Cheng or Jun Da). Stable profile IDs group speakers; no inference from voice, nationality or ethnicity is made. Public `zh-N` declarations from some contributors explicitly say native **Chinese**, without resolving the Mandarin variety. They are preserved as supporting evidence locally, but do not automatically set `speaker_native_status=NATIVE`. [Commons imageinfo API](https://www.mediawiki.org/wiki/API:Imageinfo), [User zh template](https://commons.wikimedia.org/wiki/Template:User_zh).

Licensing is per file. Particularly, Shtooka is not uniformly permissive, and Lingua Libre is not uniformly ShareAlike. See [licensing.md](licensing.md), the revision links in the pilot manifest, and the complete single-character [candidate audit](candidate-audit.csv).

## FSI / DLI — deferred, zero audio downloaded

The inspected course is **Standard Chinese: A Modular Approach**, specifically its resource modules (Pronunciation and Romanization, Numbers, Classroom Expressions, Time and Dates). The original scan identifies U.S. and Canadian government sponsorship and an interagency project involving FSI and DLI. Sponsorship is not by itself proof that every contributor's sound recording is a U.S. government employee work.

The [course mirror index](https://fsi-languages.yojik.eu/languages/FSI/fsi-chinese-mandarin.html) links six Pronunciation and Romanization tapes and a [resource-module scan](https://fsi-languages.yojik.eu/languages/FSI/Chinese/Standard%20Chinese/0002-FSI-StandardChinese-ResourceModule-StudentText.pdf). PDF page 2 was downloaded, rendered and visually inspected: DLIFLC warns it may lack complete rights and that acquisition does not authorize reproduction/resale/profit uses. This contradicts treating the mirror's public-domain footer as comprehensive commercial clearance. Source scans and their hashes remain in the local `sources/` cache; no audio was fetched.

The textbook contains pronunciation/romanization and tone instruction, but tapes are long lessons, not speaker-keyed one-syllable examples. No verified timestamps, native-speaker roster or reliable mapping of each voice to a person was obtained. Scripted prompts would still require segmentation and realization audit. **YELLOW for this edition; defer before experiment #1.** A later resolved original edition might serve OOD listening evaluation, not automatic training truth.

Separately, [current DLIFLC field-support terms](https://caa.dliflc.edu/security.html) expressly restrict commercial reuse. Those terms establish that “DLI” is not a universal public-domain license; they are not retroactively asserted to govern all old FSI files. The [U.S. government-work rule](https://www.law.cornell.edu/uscode/text/17/105) is not a substitute for asset-specific authorship evidence. Rewritten transcriptions and mirror editorial additions also need their own rights provenance.

## OMPAL — held out, verified inventory, zero audio downloaded

The [owner repository](https://github.com/phantomhsieh/OMPAL-corpus) Git tree was inspected at commit `c3aaa9e892e4b1c2a25b637401f52f6e35b53e74`, with `truncated=false`: **1,850 WAV files, 345,523,674 bytes, 49 speaker folders**. Native folders contain 20, 29 and 33 files (82 total); the remaining 1,768 belong to 46 learner folders. The [author README](https://github.com/phantomhsieh/OMPAL-corpus/blob/c3aaa9e892e4b1c2a25b637401f52f6e35b53e74/README.md) documents native status and transcript/correctness annotations; the [LICENSE](https://github.com/phantomhsieh/OMPAL-corpus/blob/c3aaa9e892e4b1c2a25b637401f52f6e35b53e74/LICENSE) is CC BY 4.0. Its correctness field is never a T1–T4 identity label. Preserve the entire source for separately audited learner/native challenge evaluation; no head fitting, calibration or layer selection on it.

## Existing Benma recordings

Read-only local inspection found **201 objects** under `services/api/var/audio/`, including **120 RIFF/WAV signatures**. These are objects, not 120 independent human utterances; original/canonical/derived copies may coexist. The historical 67-recording inventory remains at `docs/calibration/2026-09-25-f0-tracking/corpus-inventory.json`. `/tmp/benma-f0-corpus` is absent. No DB query, export function, object mutation or production provider call occurred. Local audio objects are accessible, but exact mapping to the historical challenge recordings is unverified. Wholesale recapture is not established as necessary; authorized attempt-to-object mapping and hash checks remain for the held-out challenge pass. Synthetic benchmark fixtures are not human training data.

No additional corpus was needed for this pass. Shtooka is investigated as Commons asset provenance, not a separately added or double-counted corpus. No volunteer or paid recruitment was used.
