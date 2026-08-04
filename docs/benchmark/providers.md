# Provider setup and adapter policy

Never place secrets in manifests, runs, reports, command history, or screenshots. Export variables
in the shell or use an ignored `.env` through your own secret-loading mechanism. The harness does
not automatically parse `.env`.

## Unknown-target live adapters

### OpenAI

Set `OPENAI_API_KEY`. The adapter calls `gpt-4o-transcribe` with `language=zh`, JSON output, and
logprobs. It never sends `prompt`. Run:

```bash
uv run python -m benchmark smoke-live openai SAMPLE_ID
```

Pass 1 final validation reached the API with a synthetic calibration file, but the available
account returned `credit_balance_exhausted`. Add API credits before rerunning on consented Mandarin
audio. The sanitized failed run is preserved separately from comparative outputs.

### Google Chirp 3

Set `GOOGLE_CLOUD_PROJECT`, optional `GOOGLE_CLOUD_LOCATION` (`us` by default), and a short-lived
`GOOGLE_CLOUD_ACCESS_TOKEN`. Enable Speech-to-Text V2 and billing. The adapter calls recognizer `_`
with `cmn-Hans-CN` and `chirp_3`. It does not send phrase hints or prompts. Prefer workload/ADC
credentials in production; the environment token is a research-smoke convenience.

### FunASR and Whisper

The local factories use package-owned Python runners that emit the one-object JSON contract
consumed by the benchmark; they do not assume that a third-party CLI writes JSON to stdout. The
boundary launches an argument vector, not a shell, and accepts no semantic prompt.

Whisper uses the upstream package API, never passes `initial_prompt`, records
`condition_on_previous_text`, and preserves segment uncertainty fields when present. FunASR uses
the currently documented `AutoModel(...).generate(input=...)` API with explicit model, VAD, and
punctuation configuration and no hotwords. Their argument vectors have contract tests. Neither
runner has been executed against downloaded local models in this repository, so local model and
hardware compatibility must be validated before collecting benchmark evidence. FunASR weights
may have a different license than the MIT toolkit. Whisper needs FFmpeg and local model
storage/GPU planning.

## Known-target live adapters

### Azure

Set `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`. The REST adapter sends the target through the
Pronunciation-Assessment header with `zh-CN`, `HundredMark`, and phoneme granularity. It records
unsupported normalized capabilities rather than inventing tones.

### Tencent SOE-N

Required: enabled Tencent Cloud SOE-N service, `TENCENT_SECRET_ID`, `TENCENT_SECRET_KEY`, and
`TENCENT_SOE_APP_ID` for the benchmark adapter, or the `BENMA_`-prefixed equivalents for the
production API. Production now has a signed SOE-N product-1774 WebSocket transport, separate
sentence (`eval_mode=1`) and pinyin (`eval_mode=8`) identities, explicit `F_TDET=true`, pinned
strictness, detailed normalization, and documentation-contract fixtures. Legacy Basic product 884
cannot be selected. No real request succeeded because credentials were absent.

### iFlytek ISE

Required: an iFlytek application with streaming ISE enabled plus `IFLYTEK_APP_ID`,
`IFLYTEK_API_KEY`, and `IFLYTEK_API_SECRET`. Do not build against the retired one-shot API. Preserve
vendor pinyin/phone symbols raw and map only documented fields. Production implements the current
streaming endpoint and full-dimension configuration; fixture validation is not live validation.

### SpeechSuper / Alibaba SSECP

Both remain documentation-only. Alibaba's SSECP onboarding requires provisioned commercial
access/warrant/SDK details. SpeechSuper requires a trial and complete usable contract. Obtain a
written product/API identity, endpoint, region, data terms, response schema, and price before
implementation.

## Adapter acceptance checklist

Every adapter needs fixture tests for success, timeout, malformed response, missing credentials,
unsupported config, and raw response preservation. Normalizers may add fields but never discard
the raw object. A new provider must implement exactly one evidence contract; do not introduce a
universal speech-provider interface.
