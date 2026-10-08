# Exact Mine + With context playback refinement

**Checkpoint: AUDIO-FIRST REPRESENTATION STILL NEEDS ONE SPECIFIC REFINEMENT.**

The separate-action research prototype is implemented. Mine always plays the exact
accepted unit with **0 ms padding**. With context plays the same canonical recording
with either **40 ms or 80 ms on each side**, limited by the recording bounds.
Neither action changes accepted timing, evidence status, readings or pitch.

**Physical listening is pending. No production integration occurred. No production
context window has been selected.** The initial 40 ms research setting is merely
the first candidate to audition. It is not a listening-based recommendation.
There is no basis yet to choose gate A, B or C: C would assert that playback sounds
too artificial, which has not been heard. Missing listening evidence is not that
perceptual result. Likewise, “NO CONTEXT ACTION” would be an unsupported choice.

## Physical listening methodology and limitation

Use the [local comparison viewer](../../../../services/api/var/audio-first-feedback/viewer.html)
and [30-unit listening sheet](listening-review.md). All six original October 6
physical recordings are embedded whole, as hash-verified canonical mono 16 kHz WAVs.
No replacements, synthesized reference audio, provider requests or new recordings.
The saved analyses are reused without running acoustics, trackers, VAD or speech
presence. Physical origin of the recordings does not mean this pass listened to them.

The execution environment exposes no audio-listening/perception capability and no
listener supplied observations in this pass. The user agreed to review the prepared
viewer; the listening sheet remains pending. Headless Chromium starts and renders
audio; that proves scheduling and sample identity, not intelligibility. No subjective
conclusions are inferred from waveform bounds, status labels or neighboring overlap.

The prepared protocol is to hear the whole take, then each accepted card as A exact,
B +40 ms and C +80 ms on the same device at fixed volume. Repeat A after C. Record
intelligibility, abruptness, onset clipping, vowel/coda completeness, distracting
neighbor speech and correspondence to the selected unit for all 30 cards. Record
group naturalness for 雨伞. Ask a learner to explain the two actions in their own
words. Use one global context amount only if listening supports it. 120 ms was not
added or tested: neither smaller candidate has been heard to be inadequate.

## Exact versus context behavior

| Action | Playback window | What is established | Listening result |
| --- | --- | --- | --- |
| Mine | Accepted start through accepted end; 0 ms | Every real Mine click remains exact at either research setting | Pending |
| With context, 40 ms | Start − 0.04 s, end + 0.04 s; clamp to decoded duration | Playback-only context; all 30 units intersect a neighboring accepted span | Pending |
| With context, 80 ms | Start − 0.08 s, end + 0.08 s; clamp to decoded duration | Playback-only context; all 30 units intersect a neighboring accepted span | Pending |

Neighbor overlap is expected. It does not establish audible intrusion, distraction
or failure. No padding modifies the unit object. Whole-recording playback remains
available and uses decoded duration. No signal processing, fade, speed change or
trimming controls were added.

## Required cases

| Take / case | Exact seconds | 40 ms seconds | 80 ms seconds | Status / listening |
| --- | --- | --- | --- | --- |
| 40357072 雨伞 — group / recording end | 3.56–4.87 | 3.52–4.8994375 | 3.48–4.8994375 | Unstable; naturalness and neighbor dominance pending |
| 8faf1a90 我 — sufficient evidence | 0.59–0.87 | 0.55–0.91 | 0.51–0.95 | Sufficient; intelligibility pending |
| 40357072 买 — unstable | 1.94–2.52 | 1.90–2.56 | 1.86–2.60 | Unstable; onset/coda completeness pending |
| a5acd04c 个 — shortest, 190 ms | 1.48–1.67 | 1.44–1.71 | 1.40–1.75 | Unstable; 270/350 ms context windows; usefulness pending |
| 8d252264 果 — recording end | 4.03–4.67 | 3.99–4.6904375 | 3.95–4.6904375 | Sufficient; both ends clamp; naturalness pending |
| d47274bc — no timing | None | None | None | Whole-recording replay only |

雨伞 is still **one accepted group, one Mine action and one With context action**.
There are no 雨 or 伞 segment buttons. No physical take has an `incomplete` state;
the physical unstable cases cover the requested incomplete/unstable category.
No physical accepted unit starts within 80 ms of time zero. Start clamping is
therefore a synthetic bounds test, not a claim about listening to a start-edge case.
End clamping is exercised on the real grouped 雨伞 and 8d252264 果 recordings.

## Card interaction, state and accessibility

Each card has a compact `Mine ▶` primary button and `With context ▶` secondary
button on the same row at 320 and 390 px. Supporting copy says:

- Mine: exact matched speech segment.
- With context: the same segment with a little surrounding audio; neighboring
  speech is outside accepted timing.

The research controls expose only 40/80 ms candidates and explicitly say they affect
With context only. Accepted seconds remain in card details. Labels are `Play exact
recording for 雨伞` and `Play recording with context for 雨伞` (equivalent labels for
each other unit). Buttons have 44 px minimum height, visible text, an accessible
explanation and action-specific pressed state. Activating context keeps focus on
context; sentence selection focuses Mine without autoplay. No learner usability or
screen-reader listening study is claimed.

Both actions share the existing prototype player. Every tap stops/disconnects the
old source, clears its end listener and invalidates pending asynchronous work.
Only the newest decode/resume may start. One full decoded buffer is cached per take.
The browser audio clock stops at the scheduled end; no playback stop timers were
introduced. Starting another card or whole replay also replaces segment playback.
Stop, candidate/take/layout/surface changes and page hiding cancel playback.
Page exit disposes sources, cache and AudioContext. A page retained in browser
back/forward cache stops playback without destroying the reusable player.
This is browser lifecycle coverage, not a React/Expo unmount implementation.

## Surfaces, graph and production gate

Research Practice and Free Practice show both actions. Research Conversation starts
collapsed with whole replay available; segment actions appear upon expansion.
Production Practice, Free Practice and Conversation are untouched. Pitch details,
complete selected F0, real time, gaps and Raw rendering are unchanged. No research
relative-pitch or overflow experiment was integrated. No grading or reference audio.

Production files changed in this pass: **none**. The prior audit's mobile
original-upload versus canonical-timing source constraint still applies if gate A/B
is later supported; this pass did not reopen that audit or change any backend route.
`docs/development/tone-graph-v2.md` is unchanged because the production default has
not changed. All pre-existing work is retained; no commit, push or deployment.

## Seven decisions

| Decision | Current conclusion |
| --- | --- |
| 1 — exact playback usefulness versus chopped sound | **Pending physical listening**; neither perceptual option is supported |
| 2 — context improves listening, adds little, or confuses | **Pending physical listening**; none is supported |
| 3 — 40 ms / 80 ms / no context action | **Pending physical listening**; no production constant chosen; 120 ms not justified |
| 4 — grouped naturalness versus confusion | **Pending physical listening**; one-group identity is verified |
| 5 — default representation | **AUDIO-FIRST CARDS STILL NEED REFINEMENT** |
| 6 — checkpoint | **AUDIO-FIRST REPRESENTATION STILL NEEDS ONE SPECIFIC REFINEMENT** |
| 7 — remaining product issue | **The exact/context listening comparison has not established whether context is useful or which single window to use.** |

One next step: complete the prepared physical listening sheet for these six
recordings, then apply the existing A/B/C production gate. No acoustic-model research
is proposed. See [validation](validation.md) for executable checks and their limits.
