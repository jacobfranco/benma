# Alibaba Mandarin pronunciation evaluation

- Research checked: 2026-08-03
- Lifecycle: `DOCUMENTED`
- Implementation/live status: not implemented; no account entitlement, warrant, SDK, or real response

Alibaba Cloud's current Smart Education Content Platform documentation describes Mandarin
`cn.raw.score` and `cn.word.score` tasks. The response documentation includes whole-result scores,
word/character and pinyin detail, initial/final or phone scores, a tone-confidence vector ordered
neutral/T1/T2/T3/T4, and audio-quality information. Those are attractive fields for Benma, but a
documentation table is not a captured API contract.

The documented onboarding path requires commercial access and provisioned credentials/artifacts
(including a warrant/SDK path in the current material). Benma has no such entitlement in this
environment. There is therefore no transport adapter, fixture, endpoint claim, price claim, or
privacy/retention claim. The provider has not been live tested and must not appear in a bakeoff as
anything other than `BLOCKED_EXTERNAL`.

Before implementation, obtain the exact product SKU, task endpoint/SDK, region, warrant lifecycle,
server authentication, concurrency, current price, data-processing terms, and a consented real
response. Preserve every tone-confidence element and vendor audio-quality field. Do not label a
maximum confidence element as a produced tone until the contract and real output confirm its
semantics.

Official sources:

- [Chinese sentence evaluation result](https://help.aliyun.com/en/document_detail/2996306.html)
- [Chinese word evaluation result](https://help.aliyun.com/en/document_detail/2996317.html)
- [Service access and warrant flow](https://help.aliyun.com/zh/document_detail/2865622.html)
- [SDK/use flow](https://help.aliyun.com/zh/document_detail/2996328.html)
