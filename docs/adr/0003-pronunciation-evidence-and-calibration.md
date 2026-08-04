# ADR 0003: Pronunciation evidence is richer than pronunciation truth

- Status: Accepted
- Date: 2026-08-03

## Decision

1. Azure Speech is the first replaceable reference adapter, provisionally configured as `zh-CN-Xiaochen:DragonHDLatestNeural`. Assets are configuration-keyed, account-owned, immutable examples, not grading truth. Live voice listening is still required.
2. Production acoustic evidence initially uses normalized-autocorrelation v2: raw Hz, periodicity, energy, utterance-local semitones, quality diagnostics, full points, and min/max downsampling. `torchcrepe` remains the preferred neural research contestant; its production footprint and accuracy are unvalidated.
3. MFA is isolated behind `AlignmentPort`, records its runtime version, and normalizes TextGrid output. It is disabled by default and raw evidence. MFA 3.4 documentation says `align_one` changes toward MFA 4, so command syntax does not enter domain code.
4. Surface-tone v1 resolves only canonical two-syllable T3+T3, 不 before T4, contextual 一 before T1–T4, and neutral-tone identity. Longer T3 sequences are context-dependent; neutral tone has no fixed shape grade.
5. Pinyin correction creates a child target revision. Assessment snapshots include syllable units, lexical and surface layers, rules, and provenance.
6. Azure assessment is implemented and fixture-tested, not live-tested or calibrated. Tencent, iFlytek, Alibaba, and SpeechSuper are documented candidates only. Missing access is not replaced with fabricated responses.
7. Scores, phones, detected tones, F0, quality, timestamps, and reference contours remain raw evidence. Surface rules and evidence-agreement observations are experimental. No categorical judgment is calibrated; server policy rejects enabling it.
8. Promotion requires the real pilot gates, three listeners per critical sample, held-out FAR/FRR, diagnosis/confusion analysis, conflict review, versioned parameters, and an ADR update naming the supported population/error class. A convenient threshold is insufficient.

## Consequences

Results may be partial. TTS failure does not block recording; provider failure does not erase acoustics; alignment failure removes precise syllable slicing; invalid audio suppresses interpretation. Attempts remain replayable.

Upload/transcode, provider calls, reference generation, F0, and alignment now cross a shared AnyIO worker boundary capped at two concurrent jobs, keeping the event loop responsive without introducing Celery or Redis. The repository's constrained test runtime deadlocks when it enters any worker bridge, so `environment=test` runs deterministic replay work inline; a unit test verifies that development/production select the bounded path. Database access remains synchronous and each request uses its session serially within one worker operation; a future async-database rewrite is not justified by current evidence.

On this host, 10 forced replay analyses of the same one-second synthetic chirp measured: provider p50/p95 0/0 ms (below clock resolution), F0 1,238.5/1,272.0 ms, replay alignment 0/0 ms, persisted component sum 1,238.5/1,272.0 ms, and end-to-end HTTP 1,249.0/1,310.7 ms. These are local plumbing/CPU timings, not live-provider latency or Mandarin accuracy evidence.

Calibration remains blocked at 0/50 real recordings. Synthetic fixtures validate plumbing only.
