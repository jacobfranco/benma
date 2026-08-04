# Pass 4 manual action kit

This is the executable checklist for work that credentials, real speakers, and human listening
prevent Codex from completing. Start from a clean checkout. Never paste secrets into commands,
reports, screenshots, fixtures, or Git.

Current deficit (2026-08-03): 0 real learner-correct, tone-error, initial-error, final-error,
native-control, negative-control, or spontaneous recordings; 0 native raters; 0 Stage A/B
annotations; 0 live provider responses; 0 reference voices listened; 0 real F0/alignment
comparisons. Calibration scope is `NONE`.

## 1. Provider credentials

Copy placeholders from `services/api/.env.example` into an ignored `services/api/.env` or export
them through your secret manager. The mobile app must never receive these values.

### Tencent SOE-N

- Create/verify a Tencent Cloud account able to use 口语评测（新版）, product 1774. Do not enable
  product 884 Basic for this integration.
- Enable the Chinese service, create an AppId, and create least-privilege SecretId/SecretKey or a
  reviewed temporary-credential flow.
- Set `BENMA_TENCENT_SECRET_ID`, `BENMA_TENCENT_SECRET_KEY`, and
  `BENMA_TENCENT_SOE_APP_ID`. Keep baseline `BENMA_TENCENT_SOE_SCORE_COEFF=4.0` and record any
  deliberate sweep separately.
- Run both modes on the same consented canonical WAV:

```bash
cd services/api
uv run python scripts/provider_smoke.py tencent_sentence \
  --sample /abs/canonical.wav --target 生活 --pinyin sheng1 huo2 \
  --capture ../../benchmark/corpus/provider-captures/tencent-sentence.json
uv run python scripts/provider_smoke.py tencent_pinyin \
  --sample /abs/canonical.wav --target 生活 --pinyin sheng1 huo2 \
  --capture ../../benchmark/corpus/provider-captures/tencent-pinyin.json
```

Success prints `capture_type=LIVE_REQUEST_SUCCEEDED`, lifecycle `LIVE_VALIDATED`, product/mode,
audio hash, request config, timings, raw hash, and normalized word/phone/tone evidence. Inspect that
sentence mode requested `eval_mode=1`, pinyin mode `eval_mode=8`, both contain `F_TDET=true`, and
invalid `-1` tones are absent—not `T-1`. Review Tencent fixture/retention terms before committing a
sanitized response.

### iFlytek streaming ISE

- Create an iFlytek application, enable 语音评测（流式版）, and confirm full-dimension access. The
  older ordinary API is offline and must not be used.
- Set `BENMA_IFLYTEK_APP_ID`, `BENMA_IFLYTEK_API_KEY`, and
  `BENMA_IFLYTEK_API_SECRET`.
- Run:

```bash
cd services/api
uv run python scripts/provider_smoke.py iflytek \
  --sample /abs/canonical.wav --target 生活 --pinyin sheng1 huo2 \
  --capture ../../benchmark/corpus/provider-captures/iflytek.json
```

Success must show `/v2/open-ise`, `ent=cn_vip`, `rst=entirety`, `ise_unite=1`, and
`extra_ability=syll_phone_err_msg;pitch;multi_dimension`. Confirm the response actually includes
expected tone/phone/error detail. If not, label it account capability missing and resolve the
entitlement; do not call Mandarin unsupported.

### Azure baseline

- Create/select an Azure Speech resource in the intended region.
- Set `BENMA_AZURE_SPEECH_KEY` and `BENMA_AZURE_SPEECH_REGION`.
- Run the same `provider_smoke.py azure` command. A real response advances Azure to
  `LIVE_VALIDATED`, but zh-CN phoneme scores do not become tone hypotheses.

### Alibaba SSECP

- Request Smart Education Content Platform access for `cn.raw.score`/`cn.word.score` and obtain the
  exact endpoint/SDK, warrant, AppKey, region, schema, price, and processing terms.
- No Benma adapter exists yet. Do not populate generic Alibaba placeholders and assume it works.
  Provide the non-secret contract and a consented sanitized response, then implement/test the exact
  transport before any smoke run.

### SpeechSuper

- Request a Mandarin evaluation trial and the current server API documentation.
- Obtain endpoint, authentication, task/mode, audio schema, response schema, limits, price, region,
  retention/deletion terms, and fixture permission.
- No adapter exists. Continue the campaign without it if sales/trial access is slow.

### Controlled all-provider run

After credentials are ready, run [the same-audio bakeoff](provider-bakeoff.md). Keep one output
directory per audio hash. Import only successful sanitized captures whose provider terms permit it.
Supply `--sample-id`, expected surface tones, and available acoustic/alignment JSON so the Markdown
artifact shows provider, F0, and boundary evidence together without merging their truth roles.

## 2. Learner and native recordings

### Learner capture

- Start API/mobile development normally and open **Calibration capture (development)**.
- For each prompt: read target/pinyin and the requested production; record, stop, replay, discard or
  record again if necessary, then save. Do not view provider feedback before finalizing.
- Complete 10 tone, 10 initial, and 10 final error prompts. Add at least 12 correct paired attempts
  with the same speaker/target/device/session. The screen's `pair_id` keeps those linked.
- The requested error is only an instruction. Never edit metadata to say it was truly produced.

### Native and negative controls

- Record at least 10 natural Standard Mandarin controls without exaggerated textbook contours.
- Record at least 10 assigned controls spanning silence, Mandarin-like nonsense, distorted/omitted
  target, unrelated speech, clipping, low volume, and mild noise.
- Preserve original capture; canonicalize to mono 16 kHz PCM16; record device/microphone, duration,
  clipping, silence ratio, voiced fraction, level, and quality status.

### Explicit export/import

For every selected production attempt:

```bash
cd services/api
uv run python scripts/export_pronunciation_attempt.py ATTEMPT_UUID \
  --output ../../benchmark/corpus/imports \
  --requested-production wrong_tone \
  --confirm-research-export
cd ../..
uv run python -m benchmark import-audio SAMPLE_ID \
  benchmark/corpus/imports/ATTEMPT_UUID/canonical.wav
```

Verify metadata hashes and copy the appropriate pseudonymous speaker, pair, device, and quality
metadata into the manifest. The export is independent from mutable production DB state. Public
collection needs a separate consent/withdrawal design.

## 3. Native listeners

Launch locally:

```bash
uv run python -m benchmark annotation-workbench \
  --manifest benchmark/corpus/manifests/benma-v0.1.0.json \
  --annotations benchmark/corpus/annotations
```

Share the printed tokenized URL with one listener at a time. An SSH local forward is the preferred
remote path: keep the server on `127.0.0.1:8765` and forward that port over an authenticated SSH/VPN
connection. Binding to another interface requires explicit `--allow-network` and a trusted
firewall/VPN; do not expose it anonymously to the internet.

Each listener chooses a pseudonym, native-Mandarin self-report, optional region/accent note, and
ordinary/trained role. Stage A exposes only opaque audio and commits perception, first-pass
understanding, repeat request, confidence, and notes. Only then does Stage B reveal target/pinyin.
Provider output and requested learner intent are never shown. Browser local storage recovers an
unfinished form; committed responses are immutable.

Target three independent native listeners per critical sample. Export a portable, audio-free
bundle and test import on a clean directory:

```bash
uv run python -m benchmark export-annotations --output /abs/annotations-v1.zip
uv run python -m benchmark import-annotations /abs/annotations-v1.zip \
  --annotations /abs/clean-annotations
```

## 4. Reference voice listening

With Azure TTS credentials, generate the corpus in
`docs/calibration/reference-tts-listening-worksheet.md` using the configured Xiaochen default plus
Yunfan/Xiaoxiao. If Tencent TTS is accessible, add one current Mandarin voice. Listen through
speakers, wired headphones, and Bluetooth. Select a provisional personal-use voice by listening;
never ask a pronunciation score to choose it.

## 5. Final analysis

After real imports and three-rater annotation:

```bash
uv run python -m benchmark create-calibration-split \
  --split-version benma-v0.1.0-s1 \
  --output benchmark/corpus/manifests/calibration-split-v0.1.0-s1.json
uv run python -m benchmark pronunciation-calibration \
  --split benchmark/corpus/manifests/calibration-split-v0.1.0-s1.json
uv run python -m benchmark cost \
  --output benchmark/reports/outputs/cost-scenarios.json
```

Do not change the split in place. Increment its version. Review numerator/denominator/interval,
abstentions, disagreement, failure gallery, score overlap, confusion classes, and held-out results.
Threshold candidates remain exploratory until a new ADR sets risk limits and records promotion.

For selected real WAVs, run `compare-acoustics --evidence-origin real_recording`; create manual
alignment JSON and run `compare-alignments --evidence-origin real_recording`. Run
`services/api/scripts/replay_interpreter.py --output ...` to diff current behavior against stored
interpretations without paying providers again.

The campaign is complete only when the generated report—not a checklist assertion—shows the gate.
Until then keep `BENMA_ENABLE_CATEGORICAL_TONE_JUDGMENT=false`.
