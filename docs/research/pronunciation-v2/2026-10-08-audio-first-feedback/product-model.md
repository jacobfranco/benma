# Product model and existing capability audit

The audit preceded implementation. Relevant source files below describe the
existing uncommitted tree, not changes introduced by this pass.

## Existing mobile capabilities

| Area | Existing behavior / available evidence | Implication |
| --- | --- | --- |
| `SpeechEvidence.tsx` | Heard transcript, immutable analysis, reading results, intended-target difference, inferred meaning, full user recording URL | Natural shared integration point; the audio URL is not passed into `TranscriptFeedback` today |
| `TranscriptFeedback.tsx` | Loading/readings/error states; renders `SentenceToneGraph` when analysis exists | Current graph dominates completed results; no bounded playback |
| `SentenceToneGraph.tsx` | Character focus, accepted character spans, grouped word spans, eligibility, observed gesture, secondary reference tone; More detail and nested Raw | Evidence is already available on mobile; graph currently renders an equal-character-width default |
| `sentenceToneGraph.ts` | `hasTiming`, exact group validation, grouped identity, real-time detail helpers | Reuse these concepts if integrated; do not split grouped words |
| `SyllableComparison.tsx` | Historical contour helpers only; not the current result component | Do not revive classifier-derived geometry |
| `toneGestureMatch.ts` | Existing states always compare as `uncertain`; gestures are experimental | Do not enable grading or use expected tone to shape acoustics |
| Practice | `practice.tsx`, a prepared target plus the shared `SpeechEvidence` | Cards would be the expanded default; intended target remains separate |
| Free Practice | The no-target mode of the same `practice.tsx`, not `free-talk.tsx` | Same cards from perceived text; no target is required |
| Conversation | `free-talk.tsx` uses the same `SpeechEvidence` for a user turn; assistant reply/audio already separate | Prototype collapses pronunciation evidence while keeping heard sentence and whole replay visible; no conversational redesign |
| Pronunciation screen | `pronunciation.tsx` is a separate target-oriented laboratory with history, reference audio, syllable diagnostics and advanced plots | Do not automatically treat laboratory target syllables as perceived evidence cards; leave this screen unchanged |
| Native playback | `PlaybackButton.tsx`, `useCachedAudio.ts`, Expo Audio; local URI or protected download, play/pause/seek, operation tokens, shared stop registry | Whole recording already supported; public component API has no start/end bounds |
| Web playback | `PlaybackButton.web.tsx`, `useBrowserPlayer.ts`, `useCachedAudio.web.ts`; HTMLAudioElement/blob lifecycle | Whole playback exists; no segment stop scheduler or bounded public API |
| Stored audio | Canonical mono 16 kHz WAV used for analysis; original upload preserved | Local canonical replay is possible without a new file or provider |
| Recording endpoint | `GET /v1/utterances/{id}/audio` explicitly reads `original_audio_asset_id` | Do not assume this is the canonical analysis source merely because the path says “utterances” |
| Reference audio | Target-scoped `ReferenceSpeechAsset` cache; whole-phrase audio in Practice/lab | No saved reference-unit timing or matching reference identity in these six perceived analyses; omit card reference playback |

Canonicalization decodes/resamples without an explicit trim, but container start
offsets and native/browser decoding have not been verified against accepted timing.
Before any eventual mobile integration, the source used for exact replay must have
an explicit relationship to the canonical timing clock. That is an integration
constraint, not an assertion that existing whole-recording playback is broken.

## Card contract

The research model takes only persisted perceived-analysis data. A target is not
an input. One accepted character span creates one card. One accepted multi-character
group creates one card. Accepted timing is validated using alignment state, finite
ordered in-recording bounds, timing source and timing evidence identity. Group
members must be contiguous and independently untimed. Conflicting identity spans
are withheld rather than split or duplicated. Synthetic partitions are withheld.

Timing validity does **not** require a resolved reading, a classified gesture, or
even a pitch track. A missing/mismatched acoustic projection makes acoustic labels
unavailable, while a valid timing unit still permits listening. This preserves
timing truth separately from acoustic and reading truth. 把 is the concrete example:
its reading is unresolved and its pitch insufficient, yet its timing supports Mine.

Hierarchy:

1. Large perceived character/group; pinyin only when every displayed member has a
   resolved reading with high resolution confidence.
2. Exact Mine and secondary With context buttons, labeled “Play exact recording
   for 雨伞” and “Play recording with context for 雨伞.”
3. One acoustic evidence sentence, independent of pronunciation correctness.
4. Optional tentative observed pitch label.
5. Per-card details: accepted seconds, reference reading/tone, entry to full pitch.

Tapping a sentence unit focuses its card and Mine button without starting audio.
Tapping either playback action plays only after that explicit action. Mine always
uses 0 ms; With context uses the 40/80 ms research candidate, clamped to the recording.
Only the activated action shows pressed state, and context keeps keyboard focus.
The accepted timing unit, pitch status and gesture are identical for both actions. Group selection covers the
entire displayed 雨伞 span. Punctuation and untimed text remain text, not fake buttons.

## Status and gesture policy

| Actual eligibility state | Card wording | Gesture |
| --- | --- | --- |
| `sufficient` | Pitch evidence available | Existing moderate-confidence gesture, with “(tentative)”; otherwise “Unclear” |
| `incomplete` | Pitch evidence incomplete | Hidden |
| `unstable` | Pitch evidence unstable | Hidden |
| `insufficient` | Not enough pitch evidence | Hidden |
| Missing or unbound pitch projection | Pitch evidence unavailable | Hidden |

“Available” deliberately does not say “clear,” “correct,” or “reliable tone.”
Eligibility describes existing support, not validated speech presence or pitch
accuracy. The exact gesture aliases are `level`, `rising`, `dipping`, `falling`,
`unclear`. Historical `neutral-like` classification is not a distinct public
`ObservedGesture`; its public alias is unclear. No new neutral gesture is invented.

The stored low-confidence dipping labels for 我 in 40357072 and 8d252264 are
preserved in the data, but the card says “Unclear.” Moderate gestures use Level-like,
Rising, Dipping / valley-like, or Falling plus the tentative qualifier. Groups have
no group-level gesture classifier, so they show no shape even if group pitch were
sufficient. Member shapes are never combined into a group shape.

Reference tones only appear in details. Contextual reference tone is preferred
when resolved; otherwise the lexical tone is explicitly marked as such. Unknown
readings remain unresolved. In a grouped card, member readings may be listed as
secondary linguistic information without implying member timing or playback.

## Layout and detail decision

Exactly two layouts were built: horizontal cards and a compact vertical list.
At 320/390 px the list exposes full status text and normal page scrolling. The
horizontal version makes later cards less discoverable and adds another scroll
axis. Choose the list; sentence taps provide direct access to later units.
The list is still longer than the clean-data graph, so the clean controls do not
prove universal superiority or faster use. Physical listening is not established
by screenshots.

The default shared Mine graph is absent in the research mock. **Pitch details**
retains the exact saved `tone_graph.filtered` arrays. Real seconds and a single
fixed sentence baseline preserve register, all selected points and gaps. This is
the existing “absolute” detail representation, not unit-centered pitch or hertz
re-estimation. Selecting a card highlights its accepted span without cropping the
rest of the graph. **Raw** is nested and renders the original stored frames as
diagnostic JSON; production Raw UI is unchanged.

The optional graph solves inspectability, not default intelligibility. No point is
deleted, smoothed, clipped, locally centered, or altered using target expectations.

## Exact + context continuation

The compact two-button row is now implemented in the standalone prototype. Both
buttons are available in expanded Practice/Free Practice and after Conversation
expansion. No-timing text still produces neither action. The research selector
never pads Mine, and no product context amount has been selected. This is playback
UX only; all evidence and optional graph policies above remain unchanged. Physical
listening and learner understanding are pending; production integration is deferred.
See [context playback](context-playback.md) and the [listening sheet](listening-review.md).
