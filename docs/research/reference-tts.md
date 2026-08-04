# Reference TTS research

- Reviewed: 2026-08-03
- Decision scope: one replaceable Standard Mandarin imitation example, not conversational TTS
- Listening status: infrastructure complete; no credentialed listening panel has run

Microsoft's current [language and voice inventory](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support) lists numerous `zh-CN` neural voices and newer Dragon HD families. Its [HD voice documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/high-definition-voices) lists `zh-CN-Xiaochen:DragonHDLatestNeural` and `zh-CN-Yunfan:DragonHDLatestNeural` as GA. Azure is the initial adapter because its PCM WAV REST output, account access path, and Mandarin-specific voices fit a short reference workflow.

Tencent's [basic synthesis API](https://cloud.tencent.com/document/api/1073/37995) returns WAV/MP3 plus optional character/phoneme timing, and its current [voice inventory](https://cloud.tencent.com/document/product/1073/92668) includes Mandarin large-model voices. It remains the strongest next listening-test candidate, but signing, account access, and voice selection have not been live validated.

OpenAI's [current model catalog](https://developers.openai.com/api/docs/models/all) contains quality-oriented speech models. The official material reviewed does not make a particular voice a Standard Mandarin pedagogical reference, so OpenAI remains eligible for listening—not selected by documentation alone.

## Selected default and listening corpus

The provisional default is `azure_speech / zh-CN-Xiaochen:DragonHDLatestNeural / zh-CN / rate 0% / 24 kHz PCM WAV`. It is selected for an accessible, versioned adapter, not because documentation proves natural pronunciation. `BENMA_REFERENCE_SPEECH_VOICE` replaces it without changing old evidence.

```text
妈 麻 马 骂
买 卖 水 睡
生活 后面 睡觉
你好 很好 可以 不知道 一个 不是
```

Generate at least Xiaochen HD, Yunfan HD, Xiaoxiao Neural, and one current Tencent Mandarin voice where credentials permit. Compare clean pronunciation, tone, sandhi, neutral tone, pacing, and imitation suitability. Record listener/voice/config notes; do not rank from vendor scores.

The cache key covers normalized text, provider, locale, voice, model/version, rate, and output configuration. A changed configuration creates another immutable asset. Normal retries reuse the successful asset; an explicit force request creates new evidence.

The development replay produces tonal beeps and is labeled `synthetic_replay`. It proves playback/caching only and is not speech. A reference contour is one realization for visual comparison. It is never a correct-shape boundary or grading template.

