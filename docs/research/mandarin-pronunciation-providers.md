# Mandarin pronunciation-provider candidates

- Reviewed: 2026-08-03
- Rule: documentation establishes eligibility only

| Provider/product | Documented | Implemented | Fixture validated | Live validated | Calibrated |
|---|---:|---:|---:|---:|---:|
| Azure Pronunciation Assessment `zh-CN` | yes | yes | yes | no | no |
| Tencent SOE-N | yes | no | no | no | no |
| iFlytek ISE streaming | yes | no | no | no | no |
| Alibaba Chinese/Pinyin evaluation | yes | no | no | no | no |
| SpeechSuper Mandarin | product-level | no | no | no | no |

Azure remains the replaceable production baseline. Its normalized evidence preserves scores, word/phone structures, and explicit unsupported Mandarin tone capabilities. No detected Mandarin lexical-tone field is invented.

Tencent is the highest-priority next adapter. Current official [SOE sentence-mode output](https://cloud.tencent.com/document/product/884/84147) includes `RefTone` and `HypothesisTone`; the documented product also provides validity and phone/timing detail. Credentials and an allowed raw-response corpus are required before an adapter can honestly be marked implemented.

iFlytek's current [streaming ISE API](https://www.xfyun.cn/doc/Ise/IseAPI.html) documents Mandarin `phone_score`, `tone_score`, rejection state, syllable nodes, `mono_tone`, and initial/final error semantics. The live endpoint is WebSocket with signing and XML results. No credentials are present, so implementation stops at documented-candidate status.

Alibaba's current [Pinyin evaluation contract](https://help.aliyun.com/en/document_detail/2996306.html) documents initial, final, and tone scores plus a five-entry tone-confidence vector. That vector must be preserved if access is obtained; converting it immediately to a categorical label would lose evidence.

SpeechSuper documentation makes it eligible for character/phone/tone testing, but no account-backed raw contract was available. It is not conflated with Alibaba.

Required live captures are correct, wrong tone, wrong initial, wrong final, omission, nonsense, and native controls. Secrets must be redacted and fixtures checked against provider terms. Until then `implemented`, `live_validated`, and `calibrated` remain false.

