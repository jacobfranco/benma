# Speech technology landscape

Research date: **2026-08-03**. Sources are primary vendor documentation, project repositories,
or original research papers. “Documented” below means the source claims/exposes a capability;
it does not mean Benma has experimentally validated it.

## Unknown-target Mandarin perception

### FunASR / Paraformer

FunASR is the strongest local-first Mandarin contestant to test first. Its official repository
documents `paraformer-zh` as a 220M-parameter non-streaming Mandarin ASR model trained on 60,000
hours, with a streaming counterpart and timestamp support. The toolkit is MIT licensed, but its
README warns that pretrained models have separate model licenses. This distinction must be
checked for the exact downloaded artifact before production use. Local inference is attractive
for privacy and repeatability; operational cost and learner-error honesty are unknown.

Sources: [FunASR repository](https://github.com/modelscope/FunASR),
[FunASR tutorial/model inventory](https://github.com/modelscope/FunASR/blob/main/docs/tutorial/README.md).

### Google Cloud Speech-to-Text V2 / Chirp 3

Google calls Chirp 3 its current multilingual ASR generation. Official documentation lists
`chirp_3`, streaming/synchronous/batch methods, US/EU multi-regions, and Simplified Mandarin
`cmn-Hans-CN` as GA. It also documents a crucial caveat: the word-confidence value returned for
Chirp 3 is not a true confidence score. Benma must preserve it as provider metadata rather than
treat it as calibrated probability. Phrase biasing and preview custom prompts make Chirp useful
for the A/B/C context-leakage experiment, but production unknown-target calls must use A only.
V2 standard recognition is listed at $0.016/audio minute in the first volume tier.

By default, Google's data-usage FAQ says sync/stream audio is processed in memory, customer
content is not used beyond providing the service unless the project opts into data logging, and
multi-region endpoints can constrain processing to the US or EU. Account configuration still
needs verification during a privacy review.

Sources: [Chirp 3 model and limitations](https://cloud.google.com/speech-to-text/docs/models/chirp-3),
[pricing](https://cloud.google.com/speech-to-text/pricing),
[data usage FAQ](https://cloud.google.com/speech-to-text/docs/v1/data-usage-faq).

### OpenAI transcription

The current dedicated candidates are `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, and
`gpt-realtime-whisper`; `whisper-1` remains a priced baseline. The Transcription API supports a
language hint and token log probabilities for current GPT transcription models. It also accepts a
free-text prompt. That prompt is exactly a semantic-repair risk, so Benma's production adapter
does not expose it. A separate research-only `ContextInfluenceProbeRequest` exists for A/B/C
experiments and cannot be passed to the production provider contract.

Official pricing currently gives token rates for `gpt-4o-transcribe`, not a durable
cost-per-minute conversion. The cost catalog therefore leaves its per-minute price unknown until
real runs record usage. `gpt-realtime-whisper` is duration-priced at $0.017/minute and `whisper-1`
at $0.006/minute. OpenAI states API inputs and outputs are not used to train models by default;
retention/configuration still requires account review before human recordings are uploaded.

Sources: [GPT-4o Transcribe model](https://developers.openai.com/api/docs/models/gpt-4o-transcribe),
[GPT-Realtime-Whisper model](https://developers.openai.com/api/docs/models/gpt-realtime-whisper),
[Audio Transcriptions API](https://platform.openai.com/docs/api-reference/audio/createTranscription),
[Whisper API model](https://developers.openai.com/api/docs/models/whisper-1),
[business data privacy](https://openai.com/business-data/).

### Open-source Whisper

OpenAI's Whisper repository provides multilingual recognition and an MIT license for code and
weights. Upstream exposes `initial_prompt`; the Benma local command boundary never sends it.
Whisper is a baseline, not presumed to be literal: its language model can also repair speech.

Sources: [Whisper repository](https://github.com/openai/whisper),
[transcription implementation and prompt option](https://github.com/openai/whisper/blob/main/whisper/transcribe.py).

### Mandarin-native cloud ASR

Tencent and iFlytek have Mandarin recognition products, but Pass 1 prioritizes their explicit
known-target assessment products. A free-speech adapter should be added only after the exact
current product, region, authentication, pricing, and raw schema are confirmed. No result is
fabricated in their absence.

## Known-target Mandarin assessment

### Tencent SOE-N

SOE-N is the most important first live known-target contestant because its official mode table
explicitly documents Chinese sentence tone detection and a pinyin assessment mode with tone
assessment. Pinyin tone detection is restricted to four pinyin items within a request even though
the pinyin text limit is larger. The service streams over WebSocket and documents accuracy,
fluency, completeness, phones, timing, and tone-oriented results. Postpaid pricing is 0.005 CNY
per billed call; text longer than 20 Chinese characters can count as multiple calls. A Tencent
Cloud account, enabled SOE-N product, `SecretId`, `SecretKey`, and `SoeAppId` are required.

Documented capability is unusually relevant; false acceptance, sandhi expectations, native false
rejection, and region/privacy suitability remain completely unmeasured.

Sources: [SOE-N overview](https://cloud.tencent.com/document/product/1774),
[Chinese/pinyin modes](https://cloud.tencent.com/document/product/1774/107338),
[WebSocket API](https://cloud.tencent.com/document/product/1774/107497),
[pricing](https://cloud.tencent.com/document/product/1774/107342).

### iFlytek ISE

iFlytek documents Mandarin character/word/sentence/passage assessment and “full dimension”
`phone_score` and `tone_score`; its detailed schema says pinyin symbols encode tones, with 5+
representing neutral tone. The old one-shot WebAPI is retired, so new integration must target the
streaming service. Vendor phonetic symbols are not IPA and must remain in raw/vendor metadata.
Credentials are app ID, API key, and API secret. Public durable pricing was not found; obtain a
console quote.

Sources: [ISE API and retirement notice](https://www.xfyun.cn/doc/voiceservice/ise/API.html),
[detailed Mandarin result schema](https://www.xfyun.cn/doc/voiceservice/ise/ise_protocol.html).

### Azure Pronunciation Assessment

Azure lists `zh-CN` among pronunciation-assessment locales and supports SAPI phoneme names for
Chinese. However, its feature table says syllable groups and spoken-phoneme alternatives are
English-only. The documented output gives accuracy/fluency/completeness/prosody and phone detail,
but not a normalized “detected Mandarin lexical tone” field. Azure is therefore a useful broad
baseline, not assumed to solve Benma's tone requirement. Microsoft states fast/pronunciation
assessment audio is not retained by default; the adapter does not request content logging.

Sources: [pronunciation assessment](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment),
[language support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=pronunciation-assessment),
[speech data/privacy](https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/speech-service/speech-to-text/data-privacy-security).

### SpeechSuper, Alibaba distribution, and iFlytek alternatives

Alibaba-hosted documentation for a Chinese pinyin assessment flow was located, and returned
examples reference `ssapi.cn`, which appears related to SpeechSuper distribution. Contractual and
technical ownership is not sufficiently clear to call this a native Alibaba Cloud speech
assessment API. SpeechSuper advertises Mandarin assessment, but current public response schemas,
pricing, and terms require sales/account access. These are access candidates, not implemented
results.

Source: [Alibaba-hosted pinyin assessment page](https://help.aliyun.com/zh/document_detail/2996306.html).

## Acoustic and alignment contestants

- **torchcrepe**: MIT PyTorch CREPE implementation with pitch plus periodicity, Viterbi decoding,
  and explicit silence/low-periodicity caveats. Its own docs warn CREPE was not trained on silence.
  [Repository](https://github.com/maxrmorrison/torchcrepe).
- **Praat/Parselmouth**: directly calls Praat algorithms, making it the scientific comparison path.
  Parselmouth is active and describes itself as premature; pin versions in recorded results.
  [Documentation](https://parselmouth.readthedocs.io/en/latest/).
- **Montreal Forced Aligner**: has a Mandarin MFA acoustic model (current catalog includes v3.0.0)
  and CC BY 4.0 models. Model documentation warns the training is read speech in low-noise
  conditions and divergence can cause alignment problems. MFA does not provide a general forced-
  alignment gold-standard metric. [Mandarin model catalog](https://mfa-models.readthedocs.io/en/latest/acoustic/Mandarin/index.html),
  [model caveats](https://mfa-models.readthedocs.io/en/latest/acoustic/Mandarin/Mandarin%20MFA%20acoustic%20model%20v2_0_0.html).

## Access and privacy gaps

During final validation, an OpenAI credential reached the live transcription endpoint with a
synthetic sine-wave calibration file, but the account returned HTTP 429
`credit_balance_exhausted`. The failed, sanitized run is preserved under
`benchmark/reports/outputs/smoke`; it validates neither transcription quality nor Mandarin support.
No Google, Azure, Tencent, iFlytek, or SpeechSuper credential set was available. Audio retention,
cross-border processing, enterprise-contract terms, and account regions require a human legal/
privacy review. Marketing claims were not promoted to benchmark results. The exact evidence that
would close every quality gap is the same: identical recorded corpus audio, raw responses, blind
native-listener labels, and fixed adapter/model versions.
