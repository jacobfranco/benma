# Source register

Research date: **2026-09-28**. Sources below were inspected through web retrieval unless marked inaccessible or pending. Dynamic pages can change; later acquisition must pin revisions/checksums and retain applicable terms. No audio, checkpoint, large archive or raw scraped corpus was saved. Paper licenses are not dataset licenses. Source-specific conclusions and confidence are in [licensing.md](licensing.md).

## Data, legal grants and provenance

| Source | Why it matters / retrieval limitation |
|---|---|
| [Mozilla zh-CN v27 release](https://mozilladatacollective.com/datasets/cmu5lcunh00qimh078sdd5so8) | Actual release datasheet and conditions, not search badge; release dated 2026-09-17 |
| [MDC consumer terms](https://mozilladatacollective.com/terms/consumers) | Terms dated 2026-05-06; dataset-specific license and platform access rules must be considered together |
| [CV single-word release](https://mozilladatacollective.com/datasets/cmkzhp64p00wlno07elrmt20y) | Narrow vocabulary alternative, multilingual totals and usage conditions |
| [CV spontaneous zh-CN](https://mozilladatacollective.com/datasets/cmu60so4600hto107mg006pl7) | Primary publisher indexed datasheet reports negligible current size; not a substantive benchmark |
| [AISHELL-1 OpenSLR](https://www.openslr.org/33/), [paper](https://arxiv.org/abs/1709.05522) | Official distribution wording and original corpus description |
| [THCHS-30 OpenSLR](https://www.openslr.org/18/), [paper](https://arxiv.org/abs/1512.01882) | License/prose ambiguity; original release statistics should be checked against downloaded metadata |
| [AISHELL-2 owner](https://aishelltech.com/aishell_2), [application portal](https://opendata.aishelltech.com/) | Clear commercial-use restriction; mixed portal wording |
| [AISHELL-3 OpenSLR](https://www.openslr.org/93/), [original paper](https://arxiv.org/html/2010.11567), [download portal](https://opendata.aishelltech.com/aishell-3) | Label-generation method and exact original population; product page `https://www.aishelltech.com/aishell_3` repeatedly timed out |
| [WenetSpeech owner terms](https://wenet-e2e.github.io/WenetSpeech/), [owner HF card](https://huggingface.co/datasets/wenet-e2e/wenetspeech/blob/main/README.md) | Conflicting grant wording and underlying web-audio rights |
| [MAGICDATA read](https://www.openslr.org/68/), [RAMC](https://openslr.org/123/), [ST-CMDS](https://www.openslr.org/38/), [Primewords](https://www.openslr.org/47/) | Explicit restrictive release licenses |
| [Google FLEURS card](https://huggingface.co/datasets/google/fleurs), [raw card/schema](https://huggingface.co/datasets/google/fleurs/raw/main/README.md), [paper](https://arxiv.org/html/2205.12446) | Data and split evidence; lack of speaker-ID column; audio/text provenance distinction |
| [FLORES repository](https://raw.githubusercontent.com/facebookresearch/flores/main/README.md) | Current repository distinguishes dataset licenses; exact historical FLORES-101 grant remains to pin, not silently inferred from FLORES-200 |
| [OMPAL owner repository](https://github.com/phantomhsieh/OMPAL-corpus), [README](https://raw.githubusercontent.com/phantomhsieh/OMPAL-corpus/main/README.md), [LICENSE](https://raw.githubusercontent.com/phantomhsieh/OMPAL-corpus/main/LICENSE), [author publication](https://www.isca-archive.org/interspeech_2025/hsieh25b_interspeech.html) | Clear commercial permission, actual annotation semantics and speaker counts. PDF retrieval timed out; HTML abstract and repo read successfully |
| [LATIC owner page](https://ieee-dataport.org/open-access/latic-non-native-pre-labelled-mandarin-chinese-validation-corpus-automatic-speech) | Robots-blocked; no license claim based on uninspected page. [Primary MDD paper](https://www.isca-archive.org/interspeech_2024/wang24la_interspeech.pdf) establishes relevance only |
| [Griffith/Nanjing institutional metadata](https://researchdata.edu.au/audio-recordings-l2-errors-dataset/1465210) | Named rights holder and ND grant; actual downstream release/consent still to inspect |
| [ManDi authors](https://aclanthology.org/2022.lrec-1.213/), [syllable-dataset owner](https://github.com/danielwei0214/Mandarin-Chinese-Syllable-Dataset) | Public tone-related alternatives with incompatible commercial restrictions |
| [LDC segmented/tone corpus](https://catalog.ldc.upenn.edu/LDC2015S05) | Relevant annotation resource; commercial agreement not audited |
| [SpeechOcean762 authors](https://arxiv.org/abs/2104.01378) | Distinguishes Mandarin-L1/English-L2 from the required Mandarin-L2 task |
| [CC0](https://creativecommons.org/publicdomain/zero/1.0/), [CC BY](https://creativecommons.org/licenses/by/4.0/), [Apache](https://www.apache.org/licenses/LICENSE-2.0) | Primary license authorities; no grant of speaker identity or all noncopyright rights implied |

## Encoder, aligner and F0 primary sources

| Source | Evidence |
|---|---|
| [Meta wav2vec2 Base](https://huggingface.co/facebook/wav2vec2-base), [config](https://huggingface.co/facebook/wav2vec2-base/blob/main/config.json), [original release table](https://raw.githubusercontent.com/facebookresearch/fairseq/main/examples/wav2vec/README.md) | Exact pretrained model versus ASR-finetuned variants |
| [Meta HuBERT Base](https://huggingface.co/facebook/hubert-base-ls960), [config](https://huggingface.co/facebook/hubert-base-ls960/raw/main/config.json), [original release table](https://raw.githubusercontent.com/facebookresearch/fairseq/main/examples/hubert/README.md) | Architecture, pretraining and model grant |
| [LibriSpeech owner/distributor](https://www.openslr.org/12/) | Pretraining data grant and audiobook origin |
| [Multilingual LibriSpeech distribution](https://www.openslr.org/94/) | CC BY-4.0 grant for XLSR's MLS ancestor; does not clear its other ancestors |
| [WavLM Base card](https://huggingface.co/microsoft/wavlm-base/raw/main/README.md), [config](https://huggingface.co/microsoft/wavlm-base/raw/main/config.json), [original project](https://raw.githubusercontent.com/microsoft/unilm/master/wavlm/README.md) | Base versus Base+/Large lineage |
| [UniSpeech license linked by card](https://raw.githubusercontent.com/microsoft/UniSpeech/main/LICENSE), [UniLM license](https://raw.githubusercontent.com/microsoft/unilm/master/LICENSE) | Observed CC BY-SA-3.0 versus MIT pointers; do not silently choose one |
| [Tencent Chinese HuBERT](https://huggingface.co/TencentGameMate/chinese-hubert-base), [owner repository](https://github.com/TencentGameMate/chinese_speech_pretrain) | Mandarin SSL lineage; sibling wav2vec2 family considered, not separately cleared |
| [XLSR-53 card](https://huggingface.co/facebook/wav2vec2-large-xlsr-53), [config](https://huggingface.co/facebook/wav2vec2-large-xlsr-53/raw/main/config.json), [original paper](https://arxiv.org/html/2006.13979) | Multilingual architecture; official wav2vec release table details corpus ancestors |
| [MFA code license](https://raw.githubusercontent.com/MontrealCorpusTools/Montreal-Forced-Aligner/main/LICENSE), [Mandarin v3 model](https://mfa-models.readthedocs.io/en/latest/acoustic/Mandarin/Mandarin%20MFA%20acoustic%20model%20v3_0_0.html), [dictionary](https://mfa-models.readthedocs.io/en/latest/dictionary/Mandarin/Mandarin%20%28China%29%20MFA%20dictionary%20v3_0_0.html) | Separate tool, acoustic-model and dictionary grants; model training inventory |
| [CTC segmentation](https://github.com/lumaku/ctc-segmentation), [actual LICENSE](https://raw.githubusercontent.com/lumaku/ctc-segmentation/master/LICENSE) | Apache-2.0, not assumed MIT; language support depends on acoustic model |
| [MMS-1b-all owner card](https://huggingface.co/facebook/mms-1b-all) | Explicit NC restriction for this artifact |
| [torchcrepe](https://github.com/maxrmorrison/torchcrepe), [license](https://raw.githubusercontent.com/maxrmorrison/torchcrepe/master/LICENSE), [FCPE](https://github.com/CNChTu/FCPE), [RMVPE](https://github.com/Dream-High/RMVPE) | Future F0 candidates only; no completed checkpoint/data clearance |

## Scientific evidence

| Publication | Use and limitation |
|---|---|
| [De la Fuente & Jurafsky, 2024](https://www.isca-archive.org/interspeech_2024/delafuente24_interspeech.pdf) | Direct evidence for frozen linear probing of suprasegmentals; lexical/transcript-derived labels differ from Benma's goal |
| [End-to-End Mandarin Tone Classification with Short Term Context, 2021](https://arxiv.org/html/2104.05657) | Motivation for controlled context ablation, not proof of optimal padding |
| [Guo et al., 2017](https://proceedings.mlr.press/v70/guo17a.html) | Single-temperature calibration; no OOD guarantee |
| [Geifman & El-Yaniv, 2017](https://arxiv.org/abs/1705.08500) | Risk/coverage framing; our small study does not claim the paper's guarantees |
| [Mandarin sandhi production experiment](https://pmc.ncbi.nlm.nih.gov/articles/PMC4066894/) | Underlying category and surface alternation distinction |
| [Xu, Production and perception of coarticulated tones](https://pubmed.ncbi.nlm.nih.gov/8201120/) | Primary study abstract; context changes contour realization |
| [MIT thesis on Mandarin tone, 2001](https://sls.csail.mit.edu/archives/root/publications/2001/Wang_phd_thesis.pdf) | Tone-context and 一/不 background; policy remains conservative and listening-audited |

Local facts come from the frozen repository and read-only machine commands, detailed in [review.md](review.md). Memory/latency bands, collection quotas, costs and decision margins are explicitly **proposals or estimates**, not claims sourced from these papers.
