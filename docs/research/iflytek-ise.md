# iFlytek streaming ISE Mandarin evaluation

- Research checked: 2026-08-03
- Repository lifecycle: `FIXTURE_VALIDATED`; no live request has succeeded
- Product: 语音评测（流式版）, not the retired ordinary/non-streaming evaluator
- Endpoint: `wss://ise-api.xfyun.cn/v2/open-ise`

## Pinned Benma integration

Benma sends 16 kHz, 16-bit, mono canonical audio using the documented `ssb` → `auw`
WebSocket lifecycle. The primary configuration is:

```text
sub=ise
ent=cn_vip
category=read_sentence
rst=entirety
ise_unite=1
extra_ability=syll_phone_err_msg;pitch;multi_dimension
group=adult
```

The `ise_unite`, `rst`, and `extra_ability` combination matters: without it, missing tone or phone
detail may be an account/configuration problem rather than a provider limitation. Every run records
the exact configuration and `full_dimension_requested=true`.

The adapter preserves aggregate total, accuracy, fluency, integrity, phone, and tone scores. At the
phone layer it retains pinyin symbols, initial/final identity (`is_yun`), `mono_tone`, `dp_message`,
`perr_msg`, `perr_level_msg`, timings, and provider attributes. Error mappings retain omission,
insertion, repeat, substitution, initial error, final error, tone error, and combined final+tone
error. `perr_level_msg` remains provider confidence metadata; Benma does not reinterpret it as a
probability.

The current response body is base64-encoded XML. Stored raw evidence contains the decoded XML and
sanitized envelope metadata. Authentication URLs and secrets are never stored.

## Account and live-validation caveat

An iFlytek application must enable the streaming assessment service and possess AppID, APIKey, and
APISecret. If the requested extra abilities are not enabled for the account, that is
`account capability not enabled`, not evidence that Mandarin tone detail is unsupported. A real
successful request is still required for `LIVE_VALIDATED`.

The current API page says a newly created application receives a default daily 500-call allowance
and directs production users to obtain free quota or purchase a package. A durable public unit
price was not exposed in the reviewed API page, so Benma keeps cost unknown until the console/account
quote and observed bill are recorded. The ISE SDK privacy page describes mainland-China service and
storage; confirm the WebAPI account terms rather than assuming the SDK statement transfers exactly.

## Official sources

- [Streaming ISE WebAPI documentation](https://www.xfyun.cn/doc/Ise/IseAPI.html)
- [iFlytek service console](https://console.xfyun.cn/)
- [ISE SDK privacy policy](https://www.xfyun.cn/doc/total_sdk_privacy/ise_privacy.html)

The official page states that the ordinary assessment product is offline, documents the current
streaming endpoint and the full-dimension parameters, and recommends final `status=2` results as
authoritative for a session.
