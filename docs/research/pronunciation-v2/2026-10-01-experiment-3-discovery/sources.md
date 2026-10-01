# Experiment 3: public source and audio-rights audit

The bounded search covered **21 source entries: one GREEN, four YELLOW, sixteen
RED**. GREEN means a source appears capable of the frozen panel and its audio
rights pass; the seal separately requires complete acquisition and integrity.
See `candidate-sources.csv` for all required rights, identity, structure, size,
acquisition and blocker fields. Unknown counts are not presented as zero.

## Source decisions

| Source | Decision | Evidence and controlling reason |
| --- | --- | --- |
| [SAIT-EMA](https://zenodo.org/records/17506802) | GREEN | 18 explicitly defined speaker IDs; individually distributed WAVs; exact numbered prompts; full word-tier transcript checks; audio-specific CC BY 4.0 grant. |
| [MCAE-Monosyllable](https://osf.io/h3uem/) | RED | Six documented actor IDs and individual WAVs, but CC BY-NC 4.0 and pinyin-only prompt metadata. No invented Hanzi mapping. |
| [Tone Perfect](https://tone.lib.msu.edu/) | YELLOW | Six source voice identities and isolated syllables; permission scope, current access and lexical transcript mapping unresolved. |
| [Yali-Voice](https://huggingface.co/datasets/real-ssb22/yali-voice) | RED | GPL grant explicitly covers recordings, but one voice, pinyin-only metadata and documented pitch processing. |
| [Yali-Lower](https://huggingface.co/datasets/real-ssb22/yali-lower) | RED | A transformed version of the same Cheng Ya Li speaker, not a second independent voice; same transcript problem. |
| [ManDi](https://osf.io/fgv4w/) | RED | Real participant IDs, but WAVs contain whole word lists; supplied TextGrids do not make those files isolated tokens. CC BY-NC 3.0. |
| [CASS-AGING](https://www.isca-archive.org/speechprosody_2024/li24b_speechprosody.html) | YELLOW | 210-speaker, 1,156-monosyllable design is promising; no verified downloadable speaker manifest or audio license found. |
| [CN_Mono](https://aclanthology.org/W12-5805.pdf) | YELLOW | Paper describes 45,000 monosyllables from 56 speakers, but no public audio license or acquisition manifest established. |
| [EdUHK](https://corpus.eduhk.hk/mandarin_pronunciation/?page_id=7) | YELLOW | 40 learner reading sets and workshop clips; access invitation is not a clear audio reuse grant; isolated coverage remains unresolved. |
| [THCHS-30 Segment](https://huggingface.co/datasets/changelinglab/thchs30-segment) | RED | Schema explicitly embeds full sentences alongside phone boundaries. No cropping permitted. |
| [THCHS-30](https://openslr.org/18/) | RED | Apache-2.0 corpus grant; no qualifying already-isolated target distribution established. |
| [AISHELL-1](https://openslr.org/33/) | RED | Apache-2.0, 400 speakers; documented utterance corpus does not establish the required isolated pool. |
| [AISHELL-3](https://openslr.org/93/) | RED | Apache-2.0, 218 speakers; TTS utterances do not establish a presegmented single-token subset. |
| [Mandarin Chinese Syllable Dataset](https://github.com/danielwei0214/Mandarin-Chinese-Syllable-Dataset) | RED | Repository API and README expose linguistic prompt text/dictionaries, not audio. |
| [Prosodic ABX](https://huggingface.co/datasets/HaitongSUN/prosodic-abx) | RED | Mandarin subset is Google TTS; four synthesis voice IDs are not independent new human participants. |
| [twsyllables](https://huggingface.co/datasets/taiwan-corpora/twsyllables/blob/main/NOTICES.md) | RED | Explicitly contains no audio. Its CC BY measurement grant does not license upstream recordings. Institutional voice codes also are not verified individual identities. |
| [Beijing tones since 1900](https://zenodo.org/records/10983070) | RED | CC BY measurement tables, not a waveform release. No F0-derived labels used. |
| [Chinese tone ECoG](https://zenodo.org/records/926082) | RED | CC BY stimulus archives are tiny tone-continuum sets. Six neural participants are listeners, not six recording speakers. |
| [Lin et al. supplement](https://asha.figshare.com/articles/dataset/28098206) | RED | Complete Figshare API list contains four PDFs, not the 82 students' recordings. |
| [Chang et al. supplement](https://plos.figshare.com/articles/dataset/22563377) | RED | API exposes an 86 MB RTF, not an audio inventory; not blindly downloaded. |
| [EMA-MAE](https://speechlab.eece.mu.edu/emamae/) | RED | Advertised contrast material is Mandarin-accented English; access additionally requires an email request. No contact made. |

RED is a decision for this experiment on the audited evidence, not a claim that
no useful token could ever exist inside an unexamined ASR archive. No full ASR
archive was downloaded to search for incidental one-character utterances.

## SAIT-EMA: the qualifying source

The [dataset README](https://zenodo.org/records/17506802/files/README.txt) explicitly
licenses the data CC BY 4.0 and defines the speaker directories and numbered
WAVs. The [paper's Data Records section](https://www.nature.com/articles/s41597-026-07237-9)
independently states the dataset grant and describes one utterance token per
`wav/` file. **The article itself has an NC-ND publication license; that is not
the audio dataset license.** The GitHub reader's code license is not used as an
audio grant. We neither imported nor ran that reader.

All 18 ZIP central directories were inspected through verified HTTP 206 ranges.
The complete source is 40,620,026,475 bytes; individual speaker ZIPs are roughly
1.7–2.8 GB. Only metadata plus the selected WAV members were acquired. Range
payloads may include up to 1,024 adjacent archive bytes to cover a local ZIP
header, but only the exact selected member is extracted and decoded. Published
ZIP MD5s are retained as source metadata, **not claimed verified for the whole
archive**. Selected member sizes and CRC32 are checked against both headers and
the indexed directory, then source SHA-256/SHA-1 and decoded PCM hashes are
computed locally. HTTP receipt URLs, byte ranges, dates, sizes and hashes survive.

The 962 prompt IDs occur in every speaker archive. UTF-16 prompt text is preserved
in `exact_prompt`, with an exact source character in `text` when supplied. Pinyin-only
prompts, multi-character prompts, every dictionary heteronym (including alternate
readings with the same tone), neutral/unresolved readings and source/dictionary
conflicts are excluded. The pypinyin 0.55.0 singleton reading must also match the
source's tone-marked pinyin and the complete nonempty word-tier transcript. The
corpus word tier uses numbered pinyin; its alignment boundaries are never used.
No source segmentation, forced alignment, cropping or transcript correction occurs.

There are 228 eligible recording IDs per speaker before within-speaker character
deduplication and **215 unique targets: 161/20/13/21**. Across 18 speakers, 4,104
eligible recording IDs have mutually distinct CRC32/byte-size pairs. Unequal pairs
prove unequal source bytes; equal pairs would have stopped selection for actual
byte comparison, never been assumed duplicates. After text deduplication there
are 3,870 candidates. All 18 speakers enter the hash-ranked pool; 40 clips each
are selected before acquisition. Selection does not use file duration, perceived
quality, expected difficulty, native status, model predictions or acoustic features.

Speaker identity is `sait-ema:<source folder>`. The original paper explicitly
identifies 12 native controls and six L2 learners; `L_` denotes the latter cohort.
Native status is not inferred from the README's nationalities. The known
historical speaker IDs and normalized names do not match these source identities.
Pseudonymous public identities cannot guarantee biological uniqueness or reveal
all cross-corpus aliases; no voice recognition, accent inference or listening is
used to claim otherwise.

## Rights applied to audio

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) permits copying,
redistribution and adaptation, including commercial purposes, with attribution,
license/notices and change disclosure. SAIT-EMA's grant explicitly covers its
synchronized audio data. No ShareAlike or special training-versus-evaluation term
was found. This pass uses evaluation rights only, retains original distributed
WAVs locally, and identifies the separate full-waveform decode. Attribution is to
Jia, Xie, Fang and Sun with title, source DOI/URL and license in every selected row.
Raw audio is neither staged nor committed.

[CC BY-NC](https://creativecommons.org/licenses/by-nc/4.0/) grants noncommercial
research use; evaluation is not an exemption from its commercial restriction.
The repository's existing `2026-09-28-data-feasibility/licensing.md` excludes NC
from this commercial-compatible workflow. The user added an evaluation-only
exception for CC BY-SA 4.0, not a blanket NC exception. MCAE's OSF API license name
is misleadingly prefixed “CC-BY”; its linked legal text unambiguously says
Attribution-NonCommercial 4.0. ManDi's `license.txt` states BY-NC 3.0. Neither is
silently converted to BY. Both also have independent structure/label blockers.

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) remains acceptable
under the authorized evaluation policy, with attribution and ShareAlike for
shared adapted material; it was not needed for this panel. No training-rights
conclusion is inferred. Yali's GPL explicitly covers recordings and permits
commercial use subject to GPL obligations; it is not called a noncommercial
license. Those sources fail current transcript/identity coverage independently.

Tone Perfect's [owner-authored account](https://ideah.pubpub.org/pub/hh90jpsu/release/2)
describes educational-use permission and controlled batch access. The
[MSU institutional page](https://cal.msu.edu/news/professor-creates-unique-teaching-and-research-tool/)
confirms six native voices and individual downloads. Neither is a blanket CC
license. GitHub projects that train on these recordings do not establish rights
for us; no mirror was used to route around the primary site's 403 response.

## Evidence and limitations

`retrieval-receipts.jsonl` records primary API/document responses, UTC retrieval
times, HTTP outcomes and successful-body SHA-256s. Full responses remain in the
ignored local evidence cache. `web-evidence.jsonl` preserves the few additional
web-rendered primary-source findings. `selection.json` pins the complete metadata
inputs and speaker ZIP indexes before audio acquisition. Final source receipts
are in `selected-source-evidence.jsonl` alongside the seal.

The original cached Lingua Libre/Wikimedia/OMPAL discovery audit was not rerun.
Historical manifests and audio were read only for exclusions and duplicate checks.
No corpus or license assessment was based solely on a search-result snippet.
