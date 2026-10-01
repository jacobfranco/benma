# Current code pipeline

Paths below are repository-relative. This is a source-code trace, not an assertion about private deployment settings. `Settings` defaults disable perception/assessment, use Praat, and select `alignment_provider=auto` with Azure timing disabled unless explicitly enabled. Factories allow OpenAI/replay perception and Azure/Tencent/iFlytek/replay assessment. No credentials or private recordings were inspected.

## Conversation / Free Talk

`app/conversation.tsx` re-exports `free-talk.tsx`. Both Free Talk and Practice use `useSpeechTurn` → `submitSpeech`.

1. `useAudioCapture` requests permission, sets the audio session, and uses Expo `RecordingPresets.HIGH_QUALITY`; `stop` returns a retained URI. `useSpeechTurn` supplies `audio/webm` on web and `audio/mp4` on native. These MIME choices are client claims; the server inspects the actual container.
2. `BenmaApiClient.uploadUtterance` obtains a platform-specific file/blob upload source and sends multipart audio to `/v1/utterances`.
3. `AudioIngestService.ingest` preserves/hashes the original, uses ffprobe to inspect it, ffmpeg to make mono 16 kHz PCM16 WAV, and persists a separate canonical asset/utterance. No transcript is part of encoding.
4. `/v1/utterances/{id}/perception` starts optional acoustic warmup outside test mode, then `PerceptionService.run` sends canonical bytes via `UnknownTargetPerceptionInput`. OpenAI's adapter has a fixed Mandarin verbatim policy, `zh` language hint, JSON response, and model-dependent logprob requests. There are no utterance target words/history in the request. `PerceptionRun` stores exact text, normalized evidence, raw payload/hash and provider metadata append-only.
5. On durable perception success the client publishes “heard” text. Two branches proceed independently: `analyzePerceivedSpeech` (with an optional faster readings request) and `addConversationUserTurn`.
6. `PerceivedSpeechAnalysisService.run` uses `perception.transcript` verbatim; resolves readings; first considers exact ASR token/character spans; otherwise uses configured alignment. Praat/acoustic work and alignment overlap. Timing is validated before contour slicing. Perceived reference hash, sources, raw timing evidence, missing spans, pitch, display contours and observed shape descriptors are persisted.
7. `ConversationService.add_user_turn` loads perception and history. `ContextualInterpretationService.build_run` produces a separate preserve/infer/clarify semantic decision. `AssistantGenerationService.run` uses perceived text **and separately resolved semantic text**, stores provenance and assistant text, and appends an assistant turn. Context for later turns uses semantic resolution, not a replacement `PerceptionRun`.
8. Optional `requestTurnSpeech` calls assistant synthesis against the persisted generation ID. Speech is independent/retryable; no client-supplied assistant text is accepted for synthesis.

## Practice

1. Target creation uses `/v1/pronunciation-targets`, `parse_mandarin_target`, and stored text/pinyin/lexical/surface expectations. Pinyin correction creates a new target with lineage.
2. Recording/upload is shared with Conversation. `submitSpeech` immediately starts `createAttempt` → `analyzePronunciation` while unknown-target ASR runs independently.
3. `PronunciationLaboratoryService.analyze` locks the attempt, reuses or prepares provider work, then runs assessment, independent acoustics and **target-text** alignment in a three-worker pool. Evidence and interpretation are persisted on the caller thread.
4. `AssessmentService.prepare` constructs `KnownTargetAssessmentInput` with an immutable target snapshot. Azure sends that text as `ReferenceText`; other assessment adapters are also target-conditioned. This output is never the unknown-target transcript.
5. `AlignmentService.prepare` uses `target.text` and `target.pinyin_syllables`. Laboratory result assembly can fall back to assessment spans only when exact unit labels/counts and structural timing validation pass. This remains target-relative timing.
6. `PronunciationInterpretationService` and laboratory result assembly combine the target expectations with raw provider/F0 evidence. The measured contour classifier receives raw F0/timing, not expected tone. Mobile `learnerVerdict` then compares its category with surface expectation and may display matches/close/different/unclear.
7. `onPerception` still displays the ASR transcript. With a target, the shared client's analysis promise points exclusively at target analysis: it does **not** also call `analyzePerceivedSpeech`. That missing dual trace is the principal Practice integration gap.

## Concrete stage map

All API paths in this table are under `services/api/src/benma_api/`; mobile paths are under `apps/mobile/src/`.

| File | Function/class | Input → output | Truth layer |
| --- | --- | --- | --- |
| mobile `audio/useAudioCapture.ts` | `useAudioCapture`, `start`, `stop` | microphone → encoded file URI/duration | raw acquisition |
| mobile `speech/useSpeechTurn.ts` | `useSpeechTurn` | mode, recording → workflow events | presentation/scheduling |
| mobile `audio/recordingUploadSource{,.web}.ts` | `createRecordingUploadSource` | URI → multipart source/blob | transport |
| mobile `api/client.ts` | `uploadUtterance`, `createPerception`, `analyzePerceivedSpeech`, `analyzePronunciation` | public IDs/audio → API records | transport |
| `audio/service.py` | `AudioIngestService.ingest`, `inspect_audio`, `canonicalize` | original bytes → original + canonical WAV + metadata/hash | raw acquisition |
| `speech/contracts.py` | `UnknownTargetPerceptionInput` | bytes, language, timeout → audio-only request | perception boundary |
| `speech/providers/openai.py` | `openai_form_fields`, `OpenAITranscriptionProvider.perceive` | audio-only request → exact text/logprobs/raw JSON | perception |
| `perception/service.py`, `perception/repository.py` | `PerceptionService.run`, `append_run` | provider response → persisted `PerceptionRun` | perception |
| `pronunciation/perceived.py` | `perceived_syllables`, `reading_response` | exact perceived text/grounded pronunciation tokens → readings/alternatives | lexical expectation, not observed sound |
| `pronunciation/readings.py` | `resolve_run`, `citation_reading` | Han run → phrase/grammar/dictionary/ambiguous readings | expected pronunciation |
| `pronunciation/surface.py` | `surface_expectations` | exact text, offsets, lexical tones → surface categories + reasons | expected pronunciation |
| `pronunciation/perceived.py` | `PerceivedSpeechAnalysisService.run` | persisted perception + audio → timing/pitch + distinct readings | perceived alignment + evidence/presentation |
| `pronunciation/alignment.py` | `AlignmentRequest`, `build_aligner`, `validate_alignment` | reference/audio → checked intervals | alignment (reference identity determines meaning) |
| `pronunciation/azure_alignment.py` | `AzureSpeechAligner.align`, `timing_payload`, `azure_syllable_units` | exact reference/audio → whitelisted word/phone timing → conditional syllable spans | alignment, not independent phone recognition |
| `pronunciation/alignment.py` | `MontrealForcedAligner.align`, `parse_textgrid` | configured model/dictionary + reference/audio → one syllable or word tier | optional alignment; no new aligner added |
| `pronunciation/acoustics.py` | `PraatAcousticAnalyzer.analyze`, `acoustic_result` | canonical WAV → tracker/selected F0, periodicity proxy, RMS, candidates, quality | observed acoustic evidence |
| `pronunciation/contours.py`, `evidence_region.py` | `display_contour`, `syllable_contour`, `classify_contour`, `select_tone_evidence` | raw frames/timing → filtered graph / target-independent shape evidence | evidence derivation + presentation |
| `pronunciation/targets.py` | `parse_mandarin_target`, `parse_corrected_pinyin` | intended text/corrected reading → target snapshot fields | expected pronunciation |
| `pronunciation/service.py` | `AssessmentService.prepare`, `target_snapshot` | intended target/audio → assessment run | target-relative evidence |
| `speech/providers/azure.py` | `AzurePronunciationProvider.assess` | target + WAV → scores, words/phones, timing/raw JSON | target-relative assessment |
| `speech/providers/tencent.py`, `iflytek.py` | configured pronunciation provider `assess` | target + audio → normalized score/tone/phone evidence | target-relative experimental evidence |
| `pronunciation/alignment.py` | `AlignmentService.prepare` | practice target/audio → `AlignmentRun` | target-relative alignment |
| `pronunciation/timing.py` | `resolve_target_timing` | target labels + alignment + acoustics → accept/reject reason | timing validation; acoustic padding exception only |
| `pronunciation/laboratory.py` | `PronunciationLaboratoryService.analyze`, `result` | target attempt + evidence → pronunciation result | orchestration/judgment/presentation |
| `pronunciation/interpretation.py` | `interpret_evidence` | target expectations + provider/F0 → conservative observations | judgment |
| `contextual_interpretation/service.py`, `openai.py` | `build_run`, configured `interpret` | exact perception + history → separate semantic inference | semantic interpretation |
| `conversation/context.py`, `conversation/service.py` | `resolved_user_turn_text`, `ConversationContextBuilder.build`, `add_user_turn` | persisted perceived/semantic records → history/user turn | semantic orchestration |
| `assistant_generation/service.py`, `openai.py` | `AssistantGenerationService.run`, provider `generate` | perception + semantic context → durable assistant reply | assistant generation |
| `assistant_speech/service.py`, mobile `freeTalk/workflow.ts` | synthesis service, `requestTurnSpeech` | durable generation → audio | presentation |
| mobile `speech/SpeechEvidence.tsx`, `TranscriptFeedback.tsx` | components | heard/understood records → separate displays | presentation |
| mobile `speech/learnerVerdict.ts`, `SyllableComparison.tsx`, `PronunciationFeedback.tsx`, `components/PitchPlot.tsx` | `learnerVerdict`, components | expected/observed evidence → tone wording/graph | judgment + presentation |

## Scheduling

`api/blocking.py`: separate AnyIO `CapacityLimiter(2)` budgets for blocking speech and optional analysis. Test environment executes inline. `api/routes.py`: conversation streaming has `CONVERSATION_WORKERS(max_workers=2)`. `pronunciation/warmup.py`: two acoustic workers, nonblocking capacity semaphore of two, keyed in-flight reuse, worker-owned DB sessions; perception does not join warmup. `perceived.py`: two local workers for acoustic/alignment work; DB persistence on caller. `laboratory.py`: shared three-worker assessment/acoustic/alignment executor, caller-thread ORM work, attempt lock/reuse. Client checkpoints retain upload/perception/analysis promises across retries. The research CLI runs stages sequentially and uses no DB; it is not a latency benchmark.

## Timing and evidence available today

“Direct” below means fields the adapter requests/retains if returned, not a guarantee every utterance contains them. Missing values remain missing. The audio container's duration is not the utterance's speech start/end.

| Evidence | Unknown-target OpenAI path today | Azure reference-conditioned path | Safe use |
| --- | --- | --- | --- |
| Recording start/end | 0 and canonical duration from audio, not ASR | same | recording domain only |
| Speech utterance offset/duration | no normalized timing | raw top-level `Offset`/`Duration` may exist | retain raw; do not substitute recording duration |
| Word boundaries | `segments=None`; no timing requested/normalized | `Words[].Offset/Duration` if present | direct reference-word regions after exact text checks |
| Character/syllable boundaries | no current native output; contract can accept explicit exact-offset tokens | no guaranteed Mandarin syllable tier | derive single-Han word span or exact matching full-pinyin entry; otherwise unresolved |
| Phone boundaries | absent | `Phonemes[].Offset/Duration` if present | direct provider intervals; label semantics reference-conditioned |
| Offset units | absent | 100 ns ticks | seconds = ticks / 10,000,000; harness ms = ticks / 10,000 |
| ASR confidence | model-dependent token logprobs in raw/normalized uncertainty; no calibrated utterance scalar | `NBest` confidence if supplied remains raw | do not treat logprobs or assessment score as timing confidence |
| Lexical forms | exact `text`, no distinct normalized lexical alternatives | `Lexical`, `ITN`, `MaskedITN`, `Display` may appear in raw `NBest` | Azure forms never replace unknown-target text |
| Pronunciation scores | absent | overall/accuracy/fluency/completeness and word/phone accuracy when returned | assessment against reference; not tone/segment diagnosis |
| Phone alternatives | absent | current config does not request them; Mandarin spoken-phone alternatives not documented supported | unavailable as independent observed phones |
| Recognized-word alternatives | adapter `alternatives=None` | raw NBest hypotheses if provider returns them, not normalized token alternatives | retain provider raw; no inferred alternatives |
| Timing confidence | absent | not normalized by existing timing mapper | null, not manufactured from accuracy score |

Microsoft's [pronunciation-assessment locale documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/how-to-pronunciation-assessment?pivots=programming-language-python) lists zh-CN SAPI phone names, but syllable groups and spoken-phoneme feedback only for en-US. Its response example documents 100 ns offsets. Thus English `Syllables`/`NBestPhonemes` examples cannot establish Mandarin syllable/observed-phone support. Benma's full-pinyin SAPI mapping is a checked repository convention that needs sentence-capture validation, not a general provider guarantee.

For multi-character tokens, safe subdivision requires an exact sequence match, one full-pinyin phone entry per character, matching resolved base reading, valid phone intervals inside the word, ordered nonoverlapping intervals inside audio, and no omission/insertion marker. Base matching intentionally ignores the reference tone digit: that digit must not become an observed tone. Erhua, partial initials/finals, count mismatch, ambiguous base readings and text conflicts do not justify boundaries.
