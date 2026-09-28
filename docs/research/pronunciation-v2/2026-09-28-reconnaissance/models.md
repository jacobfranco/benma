# Encoder shortlist and compute

Recommendation: start with frozen **`facebook/wav2vec2-base`**, keep **`facebook/hubert-base-ls960`** as the one backup. These are English-pretrained acoustic probes; Mandarin accuracy is an empirical question. No weights were downloaded or run. GREEN refers to the documented released lineage and permissions, not a warranty covering every underlying recording or jurisdiction.

## Five candidates

| Encoder | Architecture / parameters / frames | Mandarin relevance | Weight license and lineage | Decision |
|---|---|---|---|---|
| `facebook/wav2vec2-base` | CNN + 12 Transformer layers; approximately 95 M; 768-dimensional states, approximately 20-ms stride | English LibriSpeech; test cross-language acoustic transfer without Mandarin lexical pretraining | Canonical Meta card declares Apache-2.0; original release maps **unfine-tuned Base** to LibriSpeech, CC BY-4.0. No NC ancestor identified. [Card](https://huggingface.co/facebook/wav2vec2-base), [release table](https://raw.githubusercontent.com/facebookresearch/fairseq/main/examples/wav2vec/README.md), [data terms](https://www.openslr.org/12/) | **GREEN, medium-high documentary confidence; first**. Do not substitute `base-960h` ASR-finetuned weights. |
| `facebook/hubert-base-ls960` | CNN + 12-layer masked-cluster Transformer; approximately 95 M, 768 dimensions | Same English transfer test; different SSL objective | Apache-2.0 canonical card; released Base pretrained only on LibriSpeech 960 h. Large/XL instead use Libri-Light and are different choices. [Card](https://huggingface.co/facebook/hubert-base-ls960), [original table](https://raw.githubusercontent.com/facebookresearch/fairseq/main/examples/hubert/README.md), [config](https://huggingface.co/facebook/hubert-base-ls960/raw/main/config.json) | **GREEN, medium-high; backup**. |
| `microsoft/wavlm-base` | HuBERT-style CNN/12-layer Transformer with relative-position and denoising changes; approximately 95 M / 768 | Preserves several speech properties; plausible tone probe | Base uses LibriSpeech 960 h. **YELLOW license-path conflict**: HF card explicitly links UniSpeech's CC BY-SA 3.0 license, while original UniLM project refers to its MIT root. Both permit commercial use but redistribution/adaptation conditions differ. [Card](https://huggingface.co/microsoft/wavlm-base/raw/main/README.md), [linked license](https://raw.githubusercontent.com/microsoft/UniSpeech/main/LICENSE), [original release](https://raw.githubusercontent.com/microsoft/unilm/master/wavlm/README.md), [MIT root](https://raw.githubusercontent.com/microsoft/unilm/master/LICENSE) | Do not silently call the HF checkpoint MIT. Not first while simpler clean alternatives exist. |
| `TencentGameMate/chinese-hubert-base` (Mandarin wav2vec2 sibling considered with it) | HuBERT Base, approximately 95 M / expected 768; exact downloaded config/hash must be verified. Sibling uses wav2vec2 | Direct Mandarin pretraining is scientifically attractive | HF HuBERT card says MIT and identifies WenetSpeech L 10k h. WenetSpeech conflicts and underlying copyright reservation carry through the audit. No assertion that an NC source automatically determines weight copyright. [Card](https://huggingface.co/TencentGameMate/chinese-hubert-base), [owner repository](https://github.com/TencentGameMate/chinese_speech_pretrain), [corpus terms](https://wenet-e2e.github.io/WenetSpeech/) | **YELLOW, exclude pending rights clarification**. Mandarin-specific does not override lineage. |
| `facebook/wav2vec2-large-xlsr-53` | CNN + 24 Transformer layers; approximately 317 M, 1,024 dimensions | 53-language pretraining includes Mandarin Common Voice | Apache-2.0 card; MLS (~50.7k h), Common Voice (~3.6k h), BABEL (~1.7k h). MLS has a permissive corpus license; Common Voice release terms and corpus-specific BABEL agreements require review. [Card](https://huggingface.co/facebook/wav2vec2-large-xlsr-53), [official lineage](https://raw.githubusercontent.com/facebookresearch/fairseq/main/examples/wav2vec/README.md), [config](https://huggingface.co/facebook/wav2vec2-large-xlsr-53/raw/main/config.json) | **YELLOW**, slower and harder to audit; not first. Old CV audio may recur in new CV evaluation releases. |

Apache-2.0 permits commercial use, redistribution and derivatives with its notice/license/change obligations. MIT permits those uses with preservation of notices. Share-alike is **not** synonymous with noncommercial; WavLM's problem is determining which grant applies to the precise artifact and what must be shared. MLS's CC BY-4.0 grant is independently listed by its [official distributor](https://www.openslr.org/94/). See [licensing.md](licensing.md) for exact unresolved questions. A canonical owner model card plus original pretraining table plus data license is materially stronger evidence than an aggregator badge. Checkpoint files, hashes and complete bundled notices still must be archived on acquisition.

All five have PyTorch/Transformers inference paths. Prefer the maintained library integration over reproducing a historical Fairseq environment. The original model releases are established 2020–2022 research artifacts, not newly validated pronunciation products. The Meta models have broad downstream use and canonical configs; Tencent has a small release repository with older package examples; WavLM has official examples and model documentation. Repository pages were inspected, but exact latest commits/maintenance cadence were not reliably verified: **no claim of active maintenance or support SLA**. Pin a compatible library version in the later isolated research environment.

## Why this is scientifically worth testing

De la Fuente and Jurafsky (Interspeech 2024) probe English and Mandarin wav2vec2, HuBERT and WavLM layer by layer, using linear classifiers and speaker-held-out evaluation. Middle layers are relevant; English-trained models retain useful suprasegmental information. This supports a **small frozen probe**, not a claim of ready Mandarin learner accuracy. Their Mandarin targets are automatically derived lexical pinyin and include neutral tone, and their classifiers are frame-level. Benma needs audited surface-tone, syllable-level testing and abstention. Do not import their scores as a V2 accuracy forecast. [Original study](https://www.isca-archive.org/interspeech_2024/delafuente24_interspeech.pdf).

Whole-window mean pooling can dilute a center syllable with its neighbors. Exact crops isolate the task but remove contextual information and expose boundary errors. **Start with C: syllable-only, mean pooling + linear softmax.** Keep full waveform and boundaries to enable B: bounded context with center-only pooling next. A 2021 syllable/context study supports testing context, but its task and labels do not establish Benma's best padding. [Original context study](https://arxiv.org/html/2104.05657).

One important falsification limit: failure of one mean-pooled probe does not establish that the encoder contains no tone information. Before abandoning a representation, allow the preregistered middle-layer comparison and a three-bin temporal-pooling linear control; neither requires a larger neural architecture.

| Small head | What it tests | Order |
|---|---|---|
| Mean + multinomial linear | Whether frozen features expose recoverable tone with minimal capacity; 3,076 parameters at dimension 768 | First |
| Three ordered temporal-bin means + linear | Whether averaging hides rise/fall order; 9,220 parameters | One controlled follow-up if mean fails, before a broad NO-GO |
| One hidden-layer MLP | Nonlinear separability; increased overfitting risk | Later |
| Attentive pooling | Learns which frames matter; can learn speaker/onset shortcuts | Later |
| Small temporal convolution | Learns local dynamics but introduces temporal/head hyperparameters | Later |

## Actual machine and planning estimates

Read-only inspection: Intel i7-10700F, 8 physical cores / 16 logical CPUs, AVX2, 31 GiB RAM (~24 GiB available), 15 GiB swap, approximately 195 GiB free workspace disk. `nvidia-smi` failed to communicate with the driver. **Usable GPU and VRAM are unverified**, not zero or a guessed GPU model.

The following are **engineering budgets, not measured performance**. FP32 weights alone are approximately parameters × 4 bytes; framework, activation and allocator memory are additional. Assume short 0.15–1.5-second regions, one resident encoder, CPU FP32, no gradient tracking, bounded batches.

| Model | One FP32 weight copy / acquisition budget | RAM budget | Optional GPU inference budget | CPU per short region planning band |
|---|---|---|---|---|
| wav2vec2 Base | ~0.38 GB / 0.4–0.8 GB | 2–4 GiB | 2–4 GiB | 0.1–2 s |
| HuBERT Base | ~0.38 GB / 0.4–0.8 GB | 2–4 GiB | 2–4 GiB | 0.1–2 s |
| WavLM Base | ~0.38 GB / 0.4–0.8 GB | 2–4 GiB | 2–4 GiB | 0.1–2 s |
| Chinese HuBERT Base / wav2vec2 Base | ~0.38 GB / 0.4–0.8 GB each | 2–4 GiB | 2–4 GiB | 0.1–2 s |
| XLSR-53 Large | ~1.27 GB / 1.3–2 GB | 4–8 GiB | 4–8 GiB | 0.3–6 s |

These latency bands only reserve resources; actual kernels, threads, crop lengths and warmup can move outside them. GPU latency is unmeasured; batching should improve throughput but cannot be assumed to meet an interactive SLO. Benchmark 100 validation crops first, report warm/cold p50/p95, peak RSS, throughput and real-time factor; use measured numbers for an ETA. Frozen extraction plus a CPU linear head is feasible locally. Full fine-tuning is a different compute commitment and deferred.

For 4,608 instances, three pooled 768-dimensional FP32 layer vectors occupy about **42.5 MB** before metadata. Saving all frame features for all layers unnecessarily increases storage. Cache only pooled features for layers 4/6/8 and the bounded temporal control; persist source/model/config hashes. Three deterministic linear fits take minutes rather than encoder-training time. Budget roughly 1–6 hours for extraction and bounded comparisons until measured; data collection/auditing dominates elapsed time.

Production is a later decision: keep a model resident in a dedicated bounded worker, batch short crops by duration, avoid loading a copy per web request, and measure concurrent request behavior. CPU service inference is plausible, not proven affordable. Reusing sentence features changes contextual receptive fields relative to syllable crops and must be reevaluated. No on-device, quantization, deployment, package installation or production dependency change belongs in this pass.

## Neural F0 remains secondary

Three candidates for a later **graph/diagnostic** bake-off: CREPE/torchcrepe, FCPE, RMVPE. torchcrepe is already represented in `benchmark/acoustics/pitch.py`; its code license is MIT, but individual checkpoint/training-corpus rights still need review. FCPE has a PyTorch CPU/GPU path; RMVPE targets robust vocal pitch and requires speech-domain validation. None is cleared for production here; all remain **YELLOW for unaudited weight/data lineage**. [torchcrepe](https://github.com/maxrmorrison/torchcrepe), [license](https://raw.githubusercontent.com/maxrmorrison/torchcrepe/master/LICENSE), [FCPE](https://github.com/CNChTu/FCPE), [RMVPE](https://github.com/Dream-High/RMVPE).

If V2 works, better F0 could improve display, auxiliary features and disagreement diagnostics. It should not become a hidden gate requiring continuous pitch before V2 may classify. Compare voicing errors, octave errors, missingness and honest graph continuity on independently annotated audio; a smoother picture is not evidence of a better tone judge.
