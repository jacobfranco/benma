# Speech-provider data flows

Reviewed 2026-08-03. This is an engineering inventory, not legal advice. Voice audio can be
personal or sensitive data. A public-user launch requires consent and a current account/contract
review; the personal-development export flag is not public consent.

| Candidate | Benma sends | Destination/account boundary | Documented retention/privacy | Current decision |
|---|---|---|---|---|
| Azure Pronunciation Assessment | canonical audio, reference text, locale and assessment config | configured Azure Speech region | Microsoft's current real-time/pronunciation privacy page says customer audio/text is processed in server memory and not retained at rest; optional logging must remain off unless reviewed | adapter retained; no live Pass 4 request |
| Tencent SOE-N product 1774 | canonical audio, Chinese text or numeric pinyin, mode/strictness/tone flag | Tencent Cloud SOE-N WSS endpoint and account/AppId | transport is encrypted; a sufficiently specific SOE-N WebAPI retention statement was not established. Review console, contract, region, temporary-credential, and deletion controls before non-personal use | fixture validated only |
| iFlytek streaming ISE | canonical audio, target text, `cn_vip` full-dimension config | iFlytek mainland-China service/account | the current ISE SDK privacy policy describes mainland-China processing/storage and retention as needed for service/legal duties. Confirm that the WebAPI account terms are identical before collection | fixture validated only |
| Alibaba SSECP | audio, Mandarin target/task config if provisioned | selected Alibaba account/region and provisioned SDK/service | not established for the unprovisioned product path | documentation only |
| SpeechSuper | expected audio and target/config if a trial is obtained | unknown until trial contract | not established | documentation only |

Benma stores an independent canonical copy, hash, target snapshot, sanitized provider response,
response hash, adapter/configuration provenance, and interpretation versions. Secrets, signed URLs,
account identifiers, and raw authorization frames must never enter reports or fixtures. A live
fixture needs explicit provider-term permission and the `LIVE_CAPTURED_SANITIZED` label.

Production deletion and research export are intentionally separate. An explicit personal research
export is an independent copy; deleting mutable production audio does not silently mutate research
evidence. Any required withdrawal must delete the export separately and record the action. This is
the documented personal-build behavior, not a completed public privacy policy.

Sources:

- [Azure Speech data privacy and retention](https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/speech-service/speech-to-text/data-privacy-security)
- [Azure pronunciation assessment](https://learn.microsoft.com/en-us/azure/ai-services/Speech-Service/how-to-pronunciation-assessment)
- [Tencent SOE-N interface](https://cloud.tencent.com/document/product/1774/107497)
- [Tencent SOE-N SDK disclosure](https://cloud.tencent.com/document/product/1774/107346)
- [iFlytek streaming ISE API](https://www.xfyun.cn/doc/Ise/IseAPI.html)
- [iFlytek ISE SDK privacy policy](https://www.xfyun.cn/doc/total_sdk_privacy/ise_privacy.html)
