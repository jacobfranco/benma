# Presence failure blast radius

## The boundary that still fails

Production `audio/presence.py` remains `conservative-audio-presence-v2-corroboration`, byte-identical to the beginning of this checkpoint pass. Upload calls `require_speech` before recording successful upload state. Perception repeats the pre-ASR check and post-ASR corroboration. Perceived analysis, target-attempt/assessment paths and both Conversation routes recheck canonical audio. Repetition of the same guard is not independent verification.

For the known accidental silence, above-background activity bypasses the ambiguous-background corroboration path; ASR text does not repair that false accept. The periodic older negative still has a transcript-dependent Han-count fallback. This audit does not change either behavior or infer the recording's physical source.

The opt-in frozen corpus establishes six negative false accepts: `silence_accidental`, `neg_clicks`, `padding_human_head`, `padding_human_tail`, `padding_low_voice`, `padding_phone`. A separate expected failure records transcript-dependent acceptance of periodic background. Four integration cases establish that accidental silence escapes the guards for Practice, Free Practice, Conversation and streaming Conversation. Those tests stop immediately after guard escape with a sentinel, so they prove admission failure, not actual live provider execution.

## Consequences if ASR returns a nonempty successful transcript

“Yes, conditional” below describes reachable code, not a provider call performed during this pass. If ASR fails or returns empty text, `submitSpeech` rejects the perceived turn; that separate condition is not a reliable silence defense.

| Consequence | Practice with target | Free Practice | Conversation | Streaming Conversation |
|---|---|---|---|---|
| ASR text visible | Yes: `onPerception` adds an entry immediately | Yes: same shared workflow | Yes: provisional heard text before interpretation/generation | Yes; already visible before the NDJSON request |
| Pitch graph can render | Yes, if acoustic analysis and usable timing/text are returned | Yes, same graph | Yes; optional graph and assistant branch proceed independently | Yes; analysis runs independently of the streamed meaning/reply |
| Observed gesture can render | Conditional: tap detail, real character timing and `sufficient` eligibility; otherwise unclear/incomplete/unstable | Same | Same | Same sufficient-evidence and experimental-detail condition |
| Learner consistent/different can activate | **No**; helper always returns uncertain | **No** | **No** | **No** |
| Practice can treat submission as successful | **Yes as processing completion**, not a correct pronunciation, target match, grade, award or mastery event | Same; no target attempt | Not a Practice success; successful user-turn processing remains possible | Not a Practice result; a completed stream can return a successful turn |
| Target attempt / assessment | Can create an attempt, assessment and interpretation; target failures are optional and do not hide perceived text | No target or assessment request | No target or assessment request in this mode | No target assessment in this mode |
| Assistant receives a user speech turn | No | No | **Yes**, after the repeated guard passes; contextual interpreter then generator | **Yes**; both preflight and worker use the same fallible guard |
| Stored history | Uploaded utterance/assets, successful perception, possible acoustic/perceived result and target attempt/evidence | Uploaded utterance/assets, perception and possible acoustic/perceived result | Same speech evidence, plus contextual interpretation and paired durable user/assistant turns on generation success | Same durable speech evidence and paired turns on generation success; an early interpretation event alone is not a committed turn |
| TTS response | No automatic response TTS; reference audio is separately prepared from the target | None | **Yes, conditional**: successful assistant text triggers `prepareVoice`; request persists speech evidence; autoplay depends on audio success, activity and platform | **Yes, conditional** after the completed assistant result; same speech request/autoplay path |

Practice's on-screen entry list is local component state; durable utterance/attempt evidence is separate. No main Practice “correct” or “passed pronunciation” state exists. Its generic success means processing returned, and false speech can reach that state even if the later graph is unavailable. Target analysis starts independently; failure is swallowed as optional feedback, not a successful grade.

Conversation generation is not gated by `PitchInterpretationEligibility` or `toneGestureMatch`. `ConversationService.add_user_turn` requires an owned, successful, nonempty perception, checks the canonical asset and calls the retained presence guard, then builds contextual interpretation, a user turn, generation and the assistant turn. The final commit makes both turns durable on success. Generation failure follows existing rollback/failure handling; it does not manufacture a successful reply. Streaming preflight has the same guard before response streaming and the worker rechecks. The phone requests assistant speech only after the successful response, independently of graph readiness.

Previously stored perceptions and transcripts are not rewritten. History/read endpoints can expose already saved evidence even if a future submission would be rejected. No graph-side change retracts a false transcript, removes history or prevents a Conversation response.

## Graph safety versus turn acceptance

**Graph safety:** evidence identity, immutable raw values, original timestamps, excluded samples and honest gaps remain inspectable. Projection must not invent missing syllable timing or substitute the target. Eligibility can suppress a gesture without erasing its measurements. Descriptive gestures remain experimental even when eligible: a coherent tracker branch can still be wrong.

**Turn acceptance safety:** whether any intended user speech should have entered the workflow. The guard's false accept remains unresolved. In the frozen evidence report, accidental silence has 61 locally sufficient stress windows. Therefore neither visible F0, lexical-looking ASR, a sufficient region nor a coherent curve proves speech or intended-speaker identity.

Current containment prevents authoritative tone grading; it does **not** contain false-turn creation, provider costs, wrong perceived text, durable Conversation history or responses to silence. That is sufficient transparency for an undeployed research checkpoint, not production qualification.

## Release separation

Preserving Tone Graph V2 on the research branch does not deploy the changed Conversation checks or UI. All are part of a coherent snapshot, but promotion is a later release decision. Conversation's turn-acceptance concern must be resolved or explicitly scoped by that decision independently from graph visualization. No broad Conversation disablement or new acoustic workaround is justified by this pass. Tracker/VAD search stays closed.

Evidence locations: `services/api/src/benma_api/audio/service.py`, `perception/service.py`, `audio/presence_service.py`, `pronunciation/perceived.py`, `pronunciation/service.py`, `pronunciation/laboratory.py`, `api/routes.py`, `conversation/service.py`; `apps/mobile/src/speech/workflow.ts`, `useSpeechTurn.ts`, `SpeechEvidence.tsx`, `toneGestureMatch.ts`, `app/practice.tsx`, `app/free-talk.tsx` (`conversation.tsx` re-exports it).
