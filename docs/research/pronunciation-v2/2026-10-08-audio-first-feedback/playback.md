# Playback architecture and padding

All six full canonical WAV files exist locally. The build checks their SHA-256
against the saved analyses, checks mono/16 kHz format, and matches WAV duration to
analysis duration within one sample. Their complete bytes are embedded in the
ignored local viewer; no source recording is cropped, rewritten, or duplicated
into per-unit audio files. There are no runtime network/provider requests.

One lazily created Web Audio context and a decoded-buffer cache serve the viewer.
Each explicit Mine or With context tap stops and disconnects the previous source, obtains the
same full utterance buffer, and schedules an offset plus duration. The [Web Audio
start API](https://developer.mozilla.org/en-US/docs/Web/API/AudioBufferSourceNode/start)
supports that bounded scheduling directly. [decodeAudioData](https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/decodeAudioData)
decodes the complete file; the source buffer remains intact. Playback is at normal
speed, with no fade, normalization, pitch repair or signal processing added here.

`accepted_start_seconds` / `accepted_end_seconds` remain distinct from the clamped
playback range. End is clamped against the actual decoded buffer duration, not just
server metadata. Invalid/empty ranges fail. A new source node is created for each
tap because source nodes are one-shot. The audio clock ends playback, avoiding
coarse HTML media timeupdate polling. Full replay spans the full decoded recording.

An operation counter invalidates stale asynchronous decode/resume completions.
Repeated taps share pending decoding but only the latest can start. Stop, take or
mode/layout/padding changes cancel playback. Hidden-page handling stops audio;
page exit disconnects sources, clears cached buffers and closes the context. A page
retained in the browser back/forward cache stops playback but keeps a reusable player.
Failed decoding is evicted from cache and can be retried. Nothing auto-plays on
initial load, sentence focus, or detail expansion.

Native production already has playback registration, recording interruption,
URI retention and protected caching; reuse that lifecycle if integration earns a
later gate. This standalone research player does not claim native Expo behavior.

## Bounds comparison (not listening results)

| Before/after padding | Unit combinations tested | Units entering at least one neighboring accepted span | Decision |
| --- | ---: | ---: | --- |
| 0 ms | 30 | 0 | Mine always uses this exact accepted span |
| 40 ms | 30 | 30 | Listening comparison only; includes context |
| 80 ms | 30 | 30 | Listening comparison only; more context |

These are interval-overlap results, **not** a claim that every neighboring span
contains audible speech at the overlapped edge. All 90 buffered segment renders
matched the corresponding original PCM sample window exactly in the browser's
16 kHz offline playback check, with zero sample error and no output beyond the
scheduled duration. All six files were decoded. A real playback button was
exercised on each take; d47274bc used whole-utterance replay and the other five
used a timing-unit button.

For primary 雨伞, true bounds are 3.56–4.87 s. At 40 ms playback is
3.52–4.8994375 s; at 80 ms it is 3.48–4.8994375 s. The true end remains 4.87 s.
For a5acd04c 个, 1.48–1.67 s becomes 1.44–1.71 or 1.40–1.75 s, overlapping both
neighbors. The 80 ms option expands this 190 ms unit to 350 ms of listening.

No human listening evaluation was performed in this agent run. The tests prove
which existing samples are played, not whether a boundary sounds chopped or which
padding sounds best. No nonzero default is justified by these tests alone.

## Separate actions implemented; listening gate pending

**Mine** now calls `playExact` with 0 ms irrespective of the research selector.
**With context** calls `playWithContext` with only a 40 or 80 ms candidate. One
player serves both, with action-specific state and accessible labels. This preserves
one grouped 雨伞 card with one action of each kind. No timing means no segment actions.
The 40 ms initial selector value is the first audition candidate, not a chosen
production default. No 120 ms option was added.

The remaining refinement is the physical exact/40/80 listening comparison and
selection of one global playback-only context amount if it is useful. Do not infer
A (useful), B (exact sufficient), or C (too artificial) without hearing the recordings.
Production integration is deferred. Use the [listening sheet](listening-review.md)
and [current report](context-playback.md).

There is also an audited integration constraint: the existing mobile audio route
serves original uploads while timing is canonical. Do not apply canonical segment
bounds to an unverified original decode. The frozen prototype avoids that ambiguity
by replaying hash-matched canonical audio. No backend route was changed.

## Reference playback

Practice/lab can replay cached target-scoped whole-phrase references. The current
reference response carries audio and acoustic results but no accepted per-unit
alignment to the perceived transcript. None of the six captured analyses links a
matching reference-unit segment. Target audio cannot inherit learner timing or be
silently substituted when target and heard text differ. Consequently no Reference
button appears on the cards. Unit reference playback is a future capability, with
its own matched source and timing evidence; no provider work was done here.
