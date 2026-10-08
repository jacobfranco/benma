# Speech presence: no safe lightweight fix found

The accidental recording passes because **290 ms of above-background energy bypasses post-ASR corroboration**. Its 470-ms periodic run also prevents the initial absence predicate. Five bounded generic acoustic policies, including ±20% threshold neighborhoods, did not solve this safely. Every policy still accepts this recording. The four stricter policies reject five or six short real-speech excerpts; the short-speech-compatible policy accepts additional negatives.

**No production fix is promoted. The accidental recording remains accepted. The stack is not ready for the physical smoke/checkpoint gate.** This is the explicitly permitted **NO SAFE RULE FOUND** outcome, not a completed silence fix. Eleven strict expected-failure regressions expose the unresolved requirements.

The file contains changing harmonic bursts with upper-frequency structure. These are measurable speech-like properties, not proof of the physical source. Its saved ASR is unusually confident, and its saved, text-conditioned alignment overlaps the bursts. The supplied negative label remains unchanged. Available evidence cannot establish whether the source was background speech/playback, another tonal source, or something else. No replacement recording or new provider request was made.

## Results

- Frozen corpus: **31 existing positive waveforms + 6 exact speech excerpts = 37**, **6 existing negative waveforms + 4 exact padding excerpts = 10**, and one unresolved capture. These are **48 cases, not 48 independent recordings**. The 31 positives comprise 28 captures and three existing digital-reference variants.
- Positive retention: **37/37 before → 37/37 after**, because production is unchanged. All 37 also accept with absent, empty, non-Mandarin nonsense, and changed Chinese transcript metadata. This protects acoustic acceptance without claiming actual nonsense audio was independently tested.
- Negatives: **4/10 rejected before → 4/10 after**. Original and periodic silence still reject with their persisted transcripts; newest accidental silence, the stored clicks fixture, and four padding excerpts still pass.
- Low-F0: **5/5 retained**: three whole recordings with saved 54–70-Hz evidence and two exact excerpts. No F0 floor, track, selection, or eligibility changed. The low-F0 labels are existing acoustic proxies, not independently measured pitch truth.
- Added production latency: **0 ms**. Unpromoted feature extraction costs **2.65 ms median / 5.54 ms p95** per corpus waveform; existing guard median **3.78 ms**.
- Gibberish: tested positives remain accepted without lexical metadata. The **existing negative-side Han-count dependency remains**, so full language-independent presence semantics are not certified.

| Category (overlapping) | Waveforms | Accepted before | Accepted after |
| --- | --- | --- | --- |
| confirmed_human | 4 | 4 | 4 |
| low_f0_54_70_proxy | 5 | 5 | 5 |
| ordinary | 28 | 28 | 28 |
| quiet_gain_control | 1 | 1 | 1 |
| quiet_rms_proxy | 12 | 12 | 12 |
| short | 6 | 6 | 6 |
| sparse_pitch | 8 | 8 | 8 |
| tts_native_like | 4 | 4 | 4 |
| tts_phone | 4 | 4 | 4 |


## Six decisions

1. **OVERLY PERMISSIVE ACOUSTIC GATE.** Energy activity is treated as enough plausibility; periodicity and an amplitude bypass also keep noise alive. ASR confidence is not the decisive branch for the newest file.
2. **NO SAFE RULE FOUND.** None of the five bounded policies both rejects the newest negative and preserves meaningful positive categories.
3. **FIX RELIES TOO HEAVILY ON ASR/LANGUAGE.** This is the failed shipping criterion for the retained legacy fallback: Han count changes the periodic-noise decision. No new language-based fix is proposed. Positive gibberish compatibility passes; whole-detector language independence does not.
4. **LOW-F0 SPEECH PRESERVED.** All five explicit 54–70-Hz whole/excerpt controls remain accepted and saved acoustic evidence is unchanged.
5. **TRUST BLOCKERS REMAIN.** The accidental file still escapes Practice, Free Practice, and both Conversation gates. Existing tone-comparison restrictions remain untouched.
6. **EVALUATE ONE BOUNDED LANGUAGE-INDEPENDENT VAD.** Future step only: one frozen Silero VAD model, offline CPU replay on this exact corpus. No model is downloaded or evaluated in this pass.

## Evidence

- [Failure and complete pipeline trace](failure-forensics.md)
- [Features, policies, threshold neighborhoods, retention](feature-comparison.md)
- [Shipping decision and the bounded future experiment](decision.md)
- [Checks, explicit failures, preservation, reproducible commands](validation.md)
- [Frozen manifest with hashes and provenance](corpus.json)
- [Every measured value and old sub-check](measurements.json)
- [Saved ASR audit](asr-audit.json), [separate saved alignment audit](saved-alignment-audit.json)

The work stays on `pronunciation-v2-research`. Production/mobile source and 893 prior evidence artifacts are unchanged. No reset, stash, commit, push, deployment, model download, provider request, new recording, or alternate F0 tracker evaluation occurred.
