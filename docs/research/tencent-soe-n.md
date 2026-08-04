# Tencent SOE-N / Smart Oral Evaluation-New Age

- Research checked: 2026-08-03
- Repository lifecycle: `FIXTURE_VALIDATED`; no live request has succeeded
- Product: Tencent Cloud product **1774**, 口语评测（新版） / SOE-N
- Excluded product: product **884**, 口语评测（基础版） / SOE-B

## Pinned Benma integration

Benma uses the current WSS endpoint
`wss://soe.cloud.tencent.com/soe/api/{appid}` with `server_engine_type=16k_zh`,
16 kHz mono PCM16 WAV, recording mode, `text_mode=0`, and an explicit adult-strict
baseline `score_coeff=4.0`. The coefficient is stored with every run and must not be mixed with
other strictness settings during calibration.

Two modes are separate provider identities:

| Identity | Configuration | Purpose |
|---|---|---|
| `soe-n_mandarin_sentence_tone_detection` | `eval_mode=1`; `F_TDET=true` prefixed in `ref_text` | Chinese text, explicit tone hypothesis when valid |
| `soe-n_mandarin_pinyin_tone_detection` | `eval_mode=8`; numeric pinyin; `F_TDET=true` | Controlled pinyin comparison |

The modes must be run on the same canonical audio. They must never be pooled. Tencent's own
current pinyin-mode example returns useful phone detail while returning `Tone.Valid=false` and
`-1` tones. Benma therefore treats false validity, `-1`, and null as missing tone evidence.

Normalized evidence retains word/reference word, accuracy, fluency, match tags, phones/reference
phones, phone scores, tone validity, reference and hypothesized tones, and millisecond timings.
The full response is retained separately. Signatures, SecretId values, and other credentials are
never included in run configuration or reports.

## Failure and transport policy

The live transport sends one canonical WAV in documented recording mode and then an explicit end
message. Provider failures create immutable failed runs. Benma does not automatically resubmit an
assessment because doing so may duplicate billing; a deliberate rerun creates a new evidence run.
Error codes for OOV text, silence/no speech, audio decoding, unsupported modes, concurrency, and
service failures remain provider failures rather than synthetic fallback results.

## Official sources

- [SOE-N product overview](https://cloud.tencent.com/document/product/1774)
- [Current WebSocket interface, updated 2026-01-16](https://cloud.tencent.com/document/product/1774/107497)
- [Evaluation modes](https://cloud.tencent.com/document/product/1774/107338)
- [Pinyin mode and tone-detection example](https://cloud.tencent.com/document/product/1774/107402)
- [Strictness coefficient](https://cloud.tencent.com/document/product/1774/107379)
- [Basic product retirement notice](https://cloud.tencent.com/product/oeb)

The older product 884 data-structure page is linked from parts of the current documentation. It is
useful only for field semantics; it is not an authorization to call the Basic endpoint.
