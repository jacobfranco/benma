# Public Mandarin corpus decision — 2026-10-15

**Primary for this attempted Phase A: THCHS-30 (OpenSLR18).** It has a permissive
published license, connected read speech, 16 kHz audio, and a separately published
alignment release. A bounded archive prefix can be downloaded without retrieving
the full corpus. **This choice did not pass the data-readiness audit.**
AISHELL-1 is the reserved cross-corpus candidate. AISHELL-3 is also a strong option
for a replacement initial corpus because its published pinyin was checked against
actual readings. None of the other candidates was silently substituted mid-run.

“Published” below means verified in the linked publisher/research source;
“unverified” means this pass did not establish the fact. Advertised corpus totals
are not downloaded-subset counts. No paid account, service, annotation, or GPU was used.

| Candidate and official source | Audio, text, size, speaker metadata | License, access, product/feature redistribution | Decision |
| --- | --- | --- | --- |
| [THCHS-30 / SLR18](https://www.openslr.org/18/), [authors' paper](https://arxiv.org/html/1512.01882) | Connected Mandarin news reading, mono 16 kHz/16 bit; transcripts and pronunciation resources. Paper describes fluent standard Mandarin, not independently certified native status. Paper says 50 participants overall; its split table lists 30 train/10 test and 27.23/6.24 hours. Published alignment has 13,388 files. Speaker naming needs reconciliation; do not equate filename prefixes with a verified person count. | Apache-2.0 declaration; page also describes free academic use. Official 6,453,425,169-byte archive returned HTTP 200 to HEAD and supports ranges. Retrieved 16 MiB, not 6.4 GB. Apache terms support commercial use/derivatives with notice obligations; no derived features redistributed in this pass. | Selected for bounded pipeline check; **quarantined** for incomplete syllable ownership, transcript verification, speaker provenance, and class/context coverage. |
| [AISHELL-1 / SLR33](https://www.openslr.org/33/), [authors' paper](https://arxiv.org/html/1709.05522) | Read connected Mandarin, 400 speakers, roughly 170 hours; 16 kHz/16 bit. Released train/dev/test speakers 340/40/20. Gender, age, birthplace/accent metadata. Manual transcripts; publisher reports >95% accuracy. Regional Chinese speakers documented, native status not independently certified here. | Apache-2.0; academic-use wording also present. Official 15 GB audio archive and 1.2 MB resource archive advertised; resource HEAD succeeded. Full archive not fetched. Same notice/derivative conditions as THCHS under the published license. Lexicon has separate CC-CEDICT provenance; do not assume every supplementary resource has identical terms. | Secondary cross-corpus candidate; better speaker documentation, but no verified local syllable alignments. |
| [AISHELL-3 / SLR93](https://www.openslr.org/93/), [authors' paper](https://arxiv.org/html/2010.11567) | 85 hours, 88,035 utterances, 218 explicitly native Mandarin speakers. 44.1 kHz/16 bit, read scripts, age/gender/accent attributes. Hanzi and pinyin transcripts checked by listening, including sandhi, homographs, erhua and actual readings. Publisher reports >98% word/tone transcript accuracy. | Apache-2.0; official 19 GB archive advertised, not fetched. Product research and derivative redistribution supported by published Apache grant subject to notices. Resampling and syllable alignment still required. | Strong fallback if THCHS cannot be repaired. Existing publisher annotations need no newly recruited listeners. |
| [Primewords set 1 / SLR47](https://www.openslr.org/47/) | 100 hours, 296 explicitly native Chinese speakers; smartphone Mandarin speech and JSON utterance/transcript mapping; publisher reports >98% accuracy at 95% confidence. Exact sample rate, speaker-field schema, and reading/conversation mix not verified from downloaded bytes. | **CC BY-NC-ND 4.0**. Official 9 GB archive advertised, not fetched. Noncommercial restriction conflicts with unrestricted product research; do not presume sharing derived features is allowed under ND. | Rejected for this product-directed pass. |
| [Mozilla Common Voice zh-CN](https://commonvoice.mozilla.org/fr/datasets), [Mozilla Data Collective](https://mozilladatacollective.com/) | Crowdsourced scripted speech, MP3, transcripts and pseudonymous client IDs. Catalog reviewed lists v26.0 zh-CN at 21.39 GB; newer v27 entries also exist. Exact hours/speaker count/rates are release-specific and **unverified here**. Locale does not prove native status; account IDs do not prove one human per ID. | Catalog declares CC0-1.0, supporting commercial/derivative use at the content-license level. Access now routes through Data Collective; actual account/API access and current platform conditions not completed. No mirror or old downloadable URL assumed valid. | Not selected: access and identity/native-status checks unfinished. |
| [ST-CMDS / SLR38](https://www.openslr.org/38/) | 102,600 utterances, 855 speakers, 120 utterances each; indoor smartphone Mandarin, transcripts and metadata, manually checked. Native status, exact rate and read/conversation mix not established in this pass. | **CC BY-NC-ND 4.0**. Official 8.2 GB archive advertised, not fetched. Same product/derived-feature restrictions as Primewords. | Rejected. |

License conclusions are based on the [Apache license text](https://www.apache.org/licenses/LICENSE-2.0)
and [CC BY-NC-ND terms](https://creativecommons.org/licenses/by-nc-nd/4.0/), rather
than treating “free download” as a grant of product or redistribution rights.
AISHELL-2's official page was also checked, but its rendered page did not expose
usable licensing/access details in this session; it was not treated as cleared.

## Alignment source and what was actually obtained

[Stefan Taubert's THCHS-30 alignment release](https://zenodo.org/records/7528596),
DOI `10.5281/zenodo.7528596`, reports MFA 2.0.5 with Mandarin MFA 2.0.0a and pypinyin
0.47.1. Its API metadata declares MIT. Downloaded `grids.zip` (40,893,883 bytes),
verified published MD5 `2347227d8f2b72eb40dfb8e869ed014b`, and recorded SHA-256
`9999f175524a5a54103d2c809b89a14f1aae34222031dd3afe515c9b104b675b`.
This is an attributed derived alignment source, not an unofficial audio mirror.
MIT applies to this release; it does not replace the audio's Apache license.

Its `words` and `phonemes` tiers have acoustic alignment timing. The
`transcription` tier has evenly spaced, unaligned timing and is **never** used
for audio crops. Tone-marked phone strings are also **never** model inputs or
perceptual ground truth. The inspected pronunciation dictionary cannot by itself
prove character-to-phone ownership in ambiguous/erhua contexts.

The 16 MiB official audio prefix yielded **68 complete WAVs**, **36 released
speaker prefixes**, and **21 conservative numeric speaker groups**. Those are
identifier counts, not a verified count of distinct native speakers.
The [publisher-authored Kaldi recipe](https://raw.githubusercontent.com/kaldi-asr/kaldi/master/egs/thchs30/s5/local/thchs-30_data_prep.sh)
uses the filename prefix as speaker ID, while the paper describes A/B/C/D as text
groups. This pass groups matching numeric suffixes together to reduce possible
alias leakage, but does not claim that this heuristic proves speaker independence.

No original `.trn` transcript bodies occurred in the retained bounded prefix.
Candidate transcripts are reconstructed from the published alignment's word tier,
explicitly marked as such, and have not been checked against original transcripts
or listened through. The full gzip CRC cannot be checked from a prefix. Only
complete regular-file WAV members are retained, decoded PCM lengths are checked,
and local archive/member/PCM hashes are preserved. These limits are part of the
stop decision, not hidden assumptions.
