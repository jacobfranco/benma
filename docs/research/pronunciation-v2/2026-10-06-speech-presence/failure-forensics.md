# Exact failure and pipeline trace

## Identity and replay

- User-labelled accidental no-speech capture: perception `7e489fd3-c36d-41f6-a20b-300616ad1a42`.
- Utterance: `3259a3fd-16d2-45b4-8b81-69e52140d10b`.
- Persisted creation: `2026-10-03 18:58:57.143148+00:00`.
- Canonical SHA-256: `fcaf551459dc957c7544e396858395e4214c2447aa23cc577a2f9c5261b28eaf`.
- Original canonical path: `services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical/2b9ed25369134ee0b389b93039dd92f5.wav`.
- Frozen alias: `services/api/var/f0-foundation/audio-links/silence_accidental.wav`.
- Mono PCM16 / 16000 Hz; **3.1346875 seconds**, RMS **0.0204127964**, peak **0.231628418**, no clipping in the prior audit.

The SHA was verified against the actual persisted bytes. Both `speech_presence()` and `require_speech(..., transcript="我要一个苹果")` reproduce acceptance. No replay substitutes a synthetic waveform or fetches speech from a provider.

## Current detector, in decision order

`services/api/src/benma_api/audio/presence.py`, version `conservative-audio-presence-v2-corroboration`:

1. Validate readable mono PCM16 WAV and at least one sample.
2. Reject absolute peak ≤1/32768 as quantization-level silence.
3. Pass recordings shorter than 80 ms as `short_uncertain`.
4. Measure centered RMS on 20-ms frames every 10 ms. Background is the 20th percentile of **only** frames above 1/32768. Activity is the longest run whose RMS exceeds `max(3 * background, 3/32768)`. The reported duration is frame count ×10 ms, not the full union of overlapping 20-ms windows.
5. Run the **existing** independent presence Praat AC view: 10-ms cadence, floor 40 Hz, ceiling 550 Hz, voicing threshold .45. `periodic_seconds` is the longest voiced run, not total voiced duration.
6. Reject only if **background <.01 AND activity <.05 s AND periodic run ==0**. Consequently loud stationary material can pass without periodicity; periodic material can pass without energy activity; activity can pass without periodicity.
7. Only when not absent, background <.01, and activity <.05, obtain a second **existing** pitch view after a 100–4000-Hz Hann band filter (20-Hz transition). Corroborated frames require both pitch views voiced and within two semitones. This is the only existing spectral check. There is no explicit entropy, spectral-spread, flux, or modulation feature beyond activity.
8. Post-ASR: count Han characters in U+3400–4DBF / U+4E00–9FFF. Reject existing `no_speech`, or reject when **units ≥3 AND corroboration was checked AND total corroboration < min(units,10)*.02 s AND longest corroborated run <.05 s**. One/two Han characters, non-Han text, or no transcript bypass this latter veto. A 50-ms corroborated run or enough total agreement also rescues it.

Target text, pronunciation, tone, semantics and lexical validity are not arguments. ASR **confidence, token probabilities, timing, and no-match metadata are unused**. Transcript Han count affects the post-check. The raw `UtterancePitchTrack`, projected local eligibility, and tone-reference logic are never read by the detector. Its own Praat periodicity can independently keep the pre-ASR gate open; local pitch sufficiency cannot be used as independent speech evidence.

## Exact sub-check values

The accidental file is above quantization and longer than 80 ms. Background **.0048284973 <.01**; energy threshold **.0144854919**. Out of 312 guard frames, **81 active frames / .81 s total activity**, with a **.29-s longest run**. Therefore `activity <.05` is false and the absence conjunction fails. The **.47-s** periodic run also makes `periodic ==0` false.

Guard RMS quantiles at 0/10/20/50/80/90/95/100%:
`[0, .00423619, .00478710, .00709349, .02240030, .03246970, .04076083, .10457878]`.
The background's .00482850 differs slightly from the full q20 because its quantile excludes quantization-level frames.

There are **279 periodic frames / 2.79 s** in the existing presence pitch view. Voiced F0 min/p10/median/p90/max: **51.866 / 56.629 / 59.723 / 329.346 / 534.021 Hz**. A low median hides the higher-frequency bursts.

`corroboration_checked=False`; both corroborated durations are zero because that computation is **skipped**, not because it ran and found none. Six Han units would require 120 ms total or a 50-ms run **only if** this branch had run. It did not. Final reason: **`speech_or_uncertain`**. The transcript and any confidence are immaterial to this accept.

[Complete diagnostic values](measurements.json) include every sub-check, spectral band distribution, entropy, flux, frame energy quantiles, durations and pitch distribution. Research STFT uses 25-ms windows; those values are separately labelled from the exact 20-ms guard diagnostics.

## Failure hypothesis audit

![Accidental waveform](figures/silence_accidental-waveform.png)
![Accidental spectrum, 0–4000 Hz](figures/silence_accidental-spectrum.png)

The low-frequency floor is present, but **87.57%** of STFT power is in 300–4000 Hz and only **8.63%** below 150 Hz. Roughly 1.1–2.8 s contains changing, separated harmonic bursts with upper-frequency structure. Band-envelope p90/p20 RMS ratio is **34.73**, spectral-change p90 **.5561**, entropy median **.4517**. This is not explained by stationary low hum alone. A single transient followed by stationary ringing also does not account for the multiple changing bursts. A transient near .8 s is visible but not the only activity.

![Earlier periodic silence](figures/silence_periodic-spectrum.png)

The earlier periodic negative is much more low-frequency concentrated: **69.87%** below 150 Hz, band modulation **1.66**, no sustained activity. It differs materially from the new negative. A fix validated only on this old hum would not address the new file.

AGC, electrical/fan noise, microphone handling, distant speech and playback are possible physical-source hypotheses, **not established causes**. No device/AGC telemetry or source annotation identifies them. The new file has properties shared with accepted phone/TTS speech. Source attribution cannot be inferred from transcript identity, confidence, timestamp order or the spectrogram alone. The user-supplied no-speech label is retained without reinterpretation.

## ASR hallucination audit

The saved transcription product is `gpt-4o-transcribe`. No new ASR request occurred.

| Control | Saved raw text | Mean token logprob | Saved product result |
| --- | --- | --- | --- |
| Original silence | 现在是下午两点半。 | -2.23766 | succeeded historically; current guard rejects |
| Periodic silence | 其实我不行 | -3.99097 | succeeded historically; current post-check rejects |
| Accidental silence | 我要一个苹果 | -0.000331315 | succeeded; current guard accepts |
| Unresolved 277e9941 | 但我懂得 | -4.66940 | failed/no_speech; product transcript null |

The accidental tokens are `我要` (-.0000279681), `一个` (-.0000134252), `苹果` (-.0009525521). Under the supplied negative label this is a **high-confidence false transcription**, not a low-confidence case a simple confidence veto would catch. Token logprob is not a calibrated probability that human speech is present.

Transcription payloads expose token logprobs but **no token/word timestamps, recognized audio span, no-speech probability, or explicit no-match field**. The stored clips/synthetic controls/padding have no saved ASR; their rows say unavailable instead of inventing silence metadata. The separate 277e capture is retained as unresolved because a failed ASR result does not establish ground truth.

Saved Azure alignment is **conditioned on the transcript**, not an independent language-free presence detector. Accidental alignment reports `Success`, confidence **.947651**, SNR field **11.798456**, span **.96–2.96 s**, words 我 [.96,1.26], 要 [1.27,1.54], 一个 [1.55,1.94], 苹果 [1.95,2.96]. Those intervals overlap the changing harmonic bursts. Earlier negatives also report alignment `Success`, but confidence **0**, spanning nearly the full recording (0–6.79 / 0–3.51 s). Provider success and forced timing alone do not prove speech. [Exact saved timing](saved-alignment-audit.json).

## Callers and downstream consequences

All callers were traced before considering a production edit:

| Caller | Order / responsibility |
| --- | --- |
| `audio/service.py: AudioIngestService.ingest` | Preserve original asset first; canonicalize; `require_speech` without transcript; only then persist canonical/utterance. A rejection leaves original evidence, no successful utterance. |
| `perception/service.py: PerceptionService.run` | `require_speech` before provider; persist presence result on success; obtain unknown-target ASR; `corroborate_transcript`; then append successful perception. A post-ASR veto stores failed/no_speech plus raw provider evidence, with product transcript absent. A pre-ASR exception currently leaves the presence diagnostic dict empty because assignment follows `require_speech`. |
| `audio/presence_service.py: require_saved_speech` | Latest saved `no_speech` failure vetoes first; otherwise recompute from canonical bytes and saved transcript, never target. |
| `api/routes.py: create_pronunciation_attempt` | Account/asset checks, saved presence guard, then attempt insertion. Practice cannot start a target attempt after a real rejection. |
| `pronunciation/service.py: AssessmentService.prepare` | Guard before known-target provider work is prepared. |
| `pronunciation/laboratory.py: analyze` | Guard also on cached assessment reuse, before acoustic/alignment/interpretation work; cached success cannot bypass a later no_speech. |
| `pronunciation/perceived.py: analyze` | Require successful perception, verify ownership, then presence before cached analysis return, timing, projected pitch and tone graph. Used by Free Practice/perceived feedback. |
| `conversation/service.py: add_user_turn` | Require successful transcript and ownership, then presence before interpretation, generation and user-turn insertion. |
| `api/routes.py: streamed user turn` | Separate bounded preflight guard before returning streaming response/starting event worker; service guard is also retained. |

A false accept **can** reach all four interpretation paths. The accidental file already has saved ASR, alignment, attempt and graph history. Current local eligibility does not rescue speech-presence correctness: **61 sufficient pitch windows** still exist and are deliberately preserved. Existing independent raw acoustic extraction/warmup remains untouched and may keep diagnostic evidence even when interpretation rejects. No evidence is deleted.

For true guard rejections, historical negatives return 422/no_speech before grade/graph/turn creation. For the newest file, four strict expected-failure integration tests execute the real guard and stop on its erroneous accept before downstream work. They record the leak without fabricating successful learner feedback. Existing global experimental comparison restrictions are unchanged.
