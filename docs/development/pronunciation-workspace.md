# Pronunciation workspace

## October 10, 2026 — dominant tone families and primary learner grades

This policy supersedes earlier comparison/color descriptions below. The acoustic
layer classifies the dominant supported measured gesture without knowing target,
characters, readings, lexical tones, expected tones, transcript or reference TTS.
A small boundary counter-movement may remain subordinate to a coherent primary
rise, fall or valley. Full-track corruption gates and perturbation checks remain.

The linguistic layer supplies explicit surface expectations where resolved. Those
expectations remain authoritative, including 一, 不 and resolved T3 sandhi. When
surface realization is null but reading/pinyin and lexical tone 1–4 are resolved,
the learner layer may grade against that lexical family. It does not rewrite the
surface field. Details say “Tone N family” and “Connected-speech realization may
vary here.” Contextual coaching refines the explanation without erasing a useful
family judgment. Unresolved readings remain unavailable.

As of October 13, learner correctness uses an asymmetric conservative policy:
trustworthy compatible numbered families default to green (“Pitch acceptable”);
meaningful interpretation uncertainty is amber (“Pitch may be off”); only strong,
stable incompatible evidence is red; unavailable evidence or unresolved required
context is gray. Compatible families with fewer than 6/7 agreeing probes remain
amber because of interpretation sensitivity. Small excursion alone never changes
a grade. `LearnerPitchGrade.coaching` remains independent, including on green units.

Red requires support ≥0.90, maximum acceptable-family support ≤0.20,
winner–acceptable margin ≥0.70, winner–runner-up margin ≥0.60, clarity ≥0.90,
and at least seven probes with 100% agreement. Explicit surface rules remain
authoritative; the existing unresolved adjacent-T3 fallback may accept T3/T2,
never T4. See the [conservative grading audit](../research/pronunciation-v2/2026-10-13-conservative-grading/README.md)
for the exact rules, every changed grade, threshold rationale and validation.

Neutral uses contextual dependent-syllable acceptance, without a fixed numbered
tone. In recognized chunks with separate accepted timing and exact playback,
structurally supported neutral can be positively accepted. Unmeasured neutral can
remain non-vetoing. Neither can hide a red, amber or unavailable grade-bearing head. Standalone,
optional-neutral, unresolved and grouped cases remain bounded.

See [implementation, frozen replay and validation](../research/pronunciation-v2/2026-10-09-product-feedback/dominant-gesture-pass.md).


## October 10, 2026 — normalized shape and learner details

This section supersedes the learner presentation described in the earlier dated passes.
The worktree integrates a 100 px identity/playback rail beside a 96 px normalized pitch
shape graph. Both learner axis titles are removed. Accepted timing spans share 0..1
progress bounds; missing onset/tail/internal intervals remain empty. Pronunciation chunks
use their whole real timing span and retain constituent proportions. Underlying timestamps,
semitones, ownership, selected measurements and playback bounds are unchanged.

`PitchShapePlot` / `shapeDisplay` provide local display scaling: the midpoint of the
10th/90th pitch percentiles, a 6 st minimum range, and enough padding to keep every
selected extremum visible. No clipping, interpolation, energy relaxation or pixel-based
classification occurs. Technical plots retain the recording domain and real timestamps.

`pitchShape` independently describes the retained numeric geometry as Level, Rising,
Falling, Dip and rise, or Shape unclear. It checks internal valleys before net direction,
uses 1 st valley limbs / 1.5 st directional movement, and withholds labels that change
under endpoint deletion, thinning, flagged-point removal or neighboring endpoint regions.
The frozen corpus improves from 18 to 28 matching descriptions among 29 unambiguous
review labels and preserves all 18 old useful outputs. Exaggerated 我/想/买 and normal
saved 我 are now dip/rise; saved backend gesture/strict eligibility remain unchanged.
These are broad geometry descriptions, never inferred lexical tone numbers or grades.

More Details shows selected identity, reading/playback, Your pitch, a 152 px normalized
plot, measured shape and the server's contextual expected behavior. Technical details
starts collapsed and retains strict eligibility, saved gestures, measurement reasons,
source/frame metadata, real-time sentence evidence and Raw. Unresolved contextual
surface behavior stays Context-dependent; lexical tone never silently substitutes for it.
Connected T3 does not require a full rise. Neutral tone remains flexible. Existing
T3 sandhi, 一/不 and pronunciation-chunk rules are reused without expansion.

这个 retains all 20 这 points and zero 个 points. The chunk says “Pitch detail is limited.”;
constituents keep independent exact playback and pitch availability. No aggregate grade
or character partition is invented for grouped 雨伞. Unavailable pitch still says
“Pitch couldn't be measured reliably.” Comparison semantics and agreement colors remain
unintegrated; selection/background/trace colors do not encode pronunciation correctness.

Validation: 181 focused tests, then all 541 mobile tests / 35 suites; lint/typecheck,
web/Android export, 14 portable research tests, and offline browser review at 320/390/412.
Keyboard/dialog/playback/History/untargeted Practice/Conversation checks pass. Physical
phone listening and native screen-reader smoke remain pending.

The separately approved language-preflight experiment is research only. It distinguished
the confirmed English and throat-clear negatives but returned no language for protected
low-F0 speech and timed out on one short excerpt. Production acceptance, provider model,
Practice/History creation and Conversation rejection semantics are unchanged. Overall
acceptance remains a blocker; this UI slice alone is ready for physical smoke.

See [the complete product-feedback report](../research/pronunciation-v2/2026-10-09-product-feedback/README.md)
for exact gates, numeric exceptions, approved request receipts and reproduction details.

## October 9, 2026 — learner-facing pitch feedback cleanup

Default detail is **text → reading → exact playback → measured graph → only a
necessary limitation**. Current coarse gesture labels (including “Mostly level”)
are demoted to More Details; no replacement classifier or readability heuristic
has been introduced. “Experimental” is absent from default pronunciation feedback,
including the older pronunciation screen's analysis badge. It remains only in
explicit advanced diagnostics. “Measurement: clear” and other strict measurement
labels are also absent from default text and selector accessibility labels.

The presentation mapping intentionally uses existing constituent pitch availability:

| Selected evidence | Default presentation |
| --- | --- |
| Retained pitch in every constituent | Graph, no status or limitation message |
| Retained pitch in some constituents, none in others | Normal graph/playback layout; subtle “Pitch detail is limited.” |
| No retained pitch | Playback and “Pitch couldn't be measured reliably.”; no empty graph |

Strict `incomplete`, `unstable`, or `insufficient` eligibility alone does not trigger
a warning or suppress a usable graph. This pass does not infer how readable a
contour is. “Not enough pitch signal” is replaced in the shared plot's empty copy
as well. Unavailability describes pitch reliability, never missing speech.

For saved **我**, the exact retained contour remains primary while its existing
level interpretation can be inspected in More Details. For **这个**, all 20 retained
这 points remain at their original times; 个 still contributes zero points. Whole
chunk playback stays 2.34–3.04 s. The normal panel has the one subtle limited-detail
line above, with no error banner. More Details says **Pitch available** for 这 and
**Pitch unavailable** for 个, with exact constituent playback. A timed standalone
个 keeps playback and the reliability message. **雨伞** remains one timing identity:
its graph or unavailability message follows the same rules, without inventing
individual 雨/伞 availability.

More Details retains observed gesture, strict eligibility, measurement status,
reasons, exact timing, reference information and constituent inspection. Raw retains
tracker evidence and exclusion reasons. Limitation messages are accessible text;
healthy selector labels no longer announce measurement taxonomy. Selection remains
available without color. No new colors, grading, scores, or positive status badges.

This pass changes presentation only. Extraction, energy gating, gesture classification,
five-bin summaries, timing, chunk boundaries, pitch ownership, shared attempt scale,
exact playback, expected surface tones and Tone 3 logic are unchanged.
**PER-UNIT PITCH PROJECTION VERIFIED; ENERGY GATE NEEDS ONE SPECIFIC REFINEMENT;
GESTURE READABILITY NEEDS ONE SPECIFIC REFINEMENT; COLOR NOT YET JUSTIFIED.**
Pronunciation Chunks V1 remains earned integration; those investigations were not reopened.

Validation: **227 focused tests / 9 native-web suites**, then **524 tests / 34 suites**
in the full mobile suite, including Practice, shared untargeted/Conversation workspaces,
exact playback, grouping, accessibility and More Details/Raw. Lint, typecheck, web
export, Android export and `git diff --check` pass. Two test typing errors were fixed
(the grouped fixture's required timing ID and optional absent-graph access); no product
behavior change was needed during final validation. The chunk fixture now clones its
base evidence to prevent test-order-dependent mutations. Existing React test-renderer
deprecation/act warnings remain; no tests are skipped or failing.

Offline Chromium review and screenshot inspection cover **320, 390 and 412 × 844 px**:
normal saved 我, standalone unavailable 个, partial 这个, grouped 雨伞, and More Details.
The default graph remains 104 px high with unchanged geometry/scale; both learner
messages fit on one line at these sizes. Graphs, compact playback, More Details and
the New Attempt footer remain available without horizontal page overflow. At 320 px
the longer/singleton navigation wraps normally. Partial 这个 uses the ordinary card,
with one subtle limitation line and no error banner. Real browser checks also cover
canonical playback, Enter/Space selection, dialog focus/Escape, History, New Attempt,
Clear target, untargeted Practice, and collapsed Conversation.

Reproduce with `apps/mobile/scripts/pronunciation-chunks-browser.cjs` against the fresh
export, using `PLAYWRIGHT_MODULE`, `BENMA_WEB_URL` and the existing private saved audio
fixtures. Current artifacts: `/tmp/benma-pitch-cleanup-{web,android,review}`; the review
directory contains screenshots and `review.json`. No provider requests or new recordings
are needed for these automated checks. Backend tests were not rerun for this presentation
pass; the existing backend/schema diff was verified unchanged.

**LEARNER PITCH UI CLEANUP READY FOR PHYSICAL SMOKE.** This checkpoint concerns
presentation honesty only. It does not claim improved gesture detection or tone grading.
Native listening and VoiceOver/TalkBack are still pending. The compact graph can look
flatter than More Details; that future visual UX question is deliberately unresolved,
with X/Y scale, filtering and geometry unchanged. Earlier documented speech-presence
limitations remain. No commit, push, or deployment was performed.

Phone checklist:

1. 我: graph visible; no default Mostly level, Experimental, or Measurement: clear.
2. 我 → More Details: current gesture/measurement diagnostics still recoverable.
3. 想 / 买: usable graphs preserved without unnecessary measurement clutter.
4. 这个: whole-chunk playback, truthful graph and “Pitch detail is limited.”
5. Constituent 个: exact playback, no empty graph, “Pitch couldn't be measured reliably.”
6. 雨伞: grouped graph/playback unchanged, with no invented character timing.
7. Older pronunciation screen: no default Experimental analysis badge.

Next step: run this phone smoke checklist. Earlier dated sections describe their
original passes, including their historical copy.

## October 9, 2026 — pronunciation chunks V1

**PRONUNCIATION CHUNKS V1 EARNED INTEGRATION; READY FOR PHYSICAL CHUNK UX SMOKE.**
The default compact navigation now projects pronunciation chunks over the original
accepted timing units. **ACOUSTIC UNIT != PRONUNCIATION CHUNK; READING PHRASE !=
PRONUNCIATION CHUNK; PRONUNCIATION CHUNK != TARGET WORD.** The prior per-unit architecture
below remains the constituent evidence layer.

The API supplies deterministic candidates for exactly **雨伞, 这个, 那个, and quantity-use
一个**, using saved perceived readings and existing quantity metadata. The workspace
accepts only whole, adjacent, fully timed units under these candidates, with the existing
≥ .30 s visible-pause marker able to veto a join. Existing timing groups stay indivisible;
all remaining perceived syllables are singleton chunks, untimed ones noninteractive.
No general phrase/dictionary, neutral-particle, numeral/classifier, or 不 rule was added.

For the saved 我想买这个 take, navigation is 我 / 想 / 买 / 这个. Chunk playback/display
spans 2.34–3.04 s, while 这 remains 2.34–2.73 and 个 remains 2.74–3.04. The combined
graph unions their original selected projections, retaining the attempt Y scale and all
gaps: 20 selected 这 points and no selected 个 points. The panel says “Pitch was measured
for part of this chunk.” It does not aggregate eligibility, gestures, scores, or colors.
More Details offers one constituent inspector with exact playback and evidence. Grouped
雨伞 remains one timing identity and never exposes invented individual 雨/伞 playback.

Chunk pinyin concatenates saved citation readings (`zhège`, `nàge`, `yīgè` in the fixtures).
Contextual 一/不/neutral expectations remain independently authoritative. Chunk IDs use
constituent identities rather than text. Target edits cannot change the plan. Optional-target
Practice, session-local History, New Attempt/Clear target, playback cancellation, and collapsed
Conversation retain their existing lifecycle. Web chunk/constituent buttons now explicitly
expose `aria-pressed`; native selected state and compact wrapping/hit areas are retained.

Validation: 508 mobile tests / 34 native-web suites; 221 relevant API tests; lint, typecheck,
Ruff, mypy, deterministic OpenAPI generation, web/Android exports, and 320/390/412 px Chromium
review pass. Full API: 607 passed, 67 skipped, two pre-existing target-reading correction
test failures reproduced against HEAD. No phone smoke, commit, push, or deployment is claimed.
See the [full policy, audit, fixtures, validation, and phone checklist](../research/pronunciation-v2/2026-10-09-pronunciation-chunks/README.md).

## October 8, 2026 — practice entry pass

**NON-MANDARIN DETECTION NEEDS ONE SPECIFIC TECHNICAL FOLLOW-UP.** The practice entry UI
is implemented; robust source-language detection is not implemented with the configured
recognizer. No commit, push or deployment was performed. Tone/gesture interpretation,
eligibility, pitch filtering, comparison policy, experimental wording and the future
visual-state seam remain unchanged. No tracker/VAD research or new model was introduced.

### Optional target and entry controls

Practice has an optional target, not a learner-facing Free Practice mode. The empty screen
has **Add target** and **Random phrase** as compact secondary controls immediately above
the primary **Record** footer. There is no empty target card, mode label, explanation or
History control. The existing top-level route/title is already **Practice** and stays so.

**Record** starts capture whenever there is no current attempt, including a prepared target
with no take yet. After an accepted take, the action becomes **New Attempt**. New Attempt
clears the active evidence and selection, stops playback and starts capture while retaining
the target and session history. During capture it says **Stop recording**. A failed/rejected
new take leaves an empty workspace with **Record**; old attempts remain available only by
explicit History selection. A subsequent accepted take shows **New Attempt** again.

**Add target** opens the existing target-entry dialog. **Random phrase** selects from the
60 short, manually reviewable strings in `apps/mobile/src/speech/practicePhrases.ts`, such as
我不知道, 你今天忙吗, 我想喝咖啡, 请再说一遍, 我想去超市 and 可以用手机付款吗.
The module stores text only. Its chooser accepts an injected RNG and excludes the previous
random selection for this mounted session, including across Clear target. Nothing is stored
persistently, and no LLM or phrase-fetch request is used.

Both entry actions use the same `prepare` function and `api.createTarget` followed by
`api.createReferenceSpeech`: normal lexical parsing, pinyin, surface expectations, reading
corrections, reference audio, attempts and History semantics apply. There is no random-target
type. Normal target preparation still uses the existing backend/reference services; only
phrase selection is entirely local. Selection never starts recording. Preparing disables
duplicate selection/recording, successful preparation announces the target, target-creation
failure displays the existing error without a phantom target, and reference failure retains
the prepared target with the existing reference-retry action.

The target phrase **and pinyin body** open the existing edit dialog, labelled
`Edit target: <phrase>`. The redundant target pencil is removed. Hover/press tint and a focus
border provide subtle affordances; web Enter/Space activate editing. Speaker and Clear are
sibling controls, not children of the edit button, so they cannot bubble into editing.
Speaker uses `Play native reference for <phrase>` and Clear uses `Clear target`.
The separate lexical **Edit reading** selector is preserved for ambiguous readings only.

Clear target retains its session-generation race guard: it clears target/reference/draft,
current attempt/selection, all exercise entries and analyses, and playback. Late old
analysis cannot restore that exercise. It returns to Add target / Random phrase / Record.
History remains session-local and secondary once accepted attempts exist. Untargeted
Mandarin attempts retain perceived identity, wrapped units, detail, graphs, full/selected
playback and History, without target-relative controls or a mode heading.

### Source-language audit and exact limitation

The shared live perception path for targeted practice, untargeted practice and Conversation
is `submitSpeech` → `createPerception` → `PerceptionService` →
`OpenAITranscriptionProvider`. The checked repository default and local non-secret model
setting both select **gpt-4o-transcribe**. The request sends `language=zh`, `response_format=json`,
`include[]=logprobs`, and the server-owned `mandarin-verbatim-v1` policy whose first sentence
asserts that the recording is Mandarin. That is language conditioning, not independent
source-language detection. Intended target and conversational context are structurally
absent from `UnknownTargetPerceptionInput`. Azure's separate known-target/alignment requests
use zh-CN and do not establish the language of the source recording either.

This explains the risk in English audio becoming plausible Chinese: the recognizer is
asked to decode Mandarin even when the input is English. The precise reported recording
was not available to reproduce, so this is a traced failure mechanism, not a measured
explanation of each hallucinated word. A Chinese transcript, successful pinyin mapping or
high token probability cannot certify Mandarin speech.

The adapter already preserves raw provider payloads, singular `language` and plural
`languages` metadata, including an explicitly empty array. The normalized perception keeps
`detected_language` / `detected_languages`; nothing relevant was being discarded.
`gpt-4o-transcribe` JSON/logprobs do not provide a documented independent language-ID signal
usable in this configuration. Simply omitting the hint does not add a documented language-ID
field. Existing constrained metadata cannot be treated as independent evidence.

The current [official OpenAI file-transcription guide](https://developers.openai.com/api/docs/guides/speech-to-text)
documents detected language codes for **gpt-transcribe** and an empty `languages` array when
it cannot reliably identify a language. That is a different model, supported by the adapter
but not selected here; even that adapter path currently supplies `languages[]=zh` and the
Mandarin assertion. The prior transcription bakeoff retained gpt-4o-transcribe for a reason
([recorded audit](perception-alignment-pitch-2026-09-18.md#transcription-and-truth-boundaries)).
This pass does not silently switch recognizers, add a classifier, or repurpose token logprobs
as language confidence. Automatic rejection of accidental English therefore remains
**unsupported in the running backend**. Target presence cannot make this evidence stronger.

### Language-rejection UX plumbing (no detector yet)

The shared mobile workflow now recognizes reserved `non_mandarin` and `language_uncertain`
errors, from either a failed perception response or transport error, before publishing a
perception or starting any pronunciation/Conversation work. The current backend does **not**
emit either code. Tests inject them to validate the future error boundary, not to claim
English/other-language classification accuracy.

- `non_mandarin`: “This doesn't sound like Mandarin. Try again.”
- `language_uncertain`: “Couldn't identify the language. Try recording again.”

These errors announce as alerts, discard the recording's retry checkpoint, leave the target
intact and permit immediate fresh capture. They do not offer resubmission of the rejected
audio, create pronunciation attempts, show fabricated perceived text/graphs/timing, add a
History entry, or invoke the conversational assistant. Unknown language is never labelled
confidently non-Mandarin. Normal accepted perceptions retain existing behavior; no transcript
heuristic was added. Conversation layout and collapsed-pronunciation behavior are unchanged.

Speech presence remains separate: digital silence rejection and short-Mandarin acceptance
are preserved; ambient/background false positives remain an existing blocker. VAD research
was not reopened. The visible-geometry versus gesture-interpretation discrepancy remains a
separate future pass, with no grading colors or policy changes here.

### Entry-pass validation

- Mobile native/web: **32 suites, 412 tests passed**, including entry state, Record/New Attempt,
  deterministic phrase selection, ordinary target/reference flow, no automatic capture,
  preparation/reference failure, clear-target race protection, readings, full/canonical
  playback, grouped 雨伞, d47274bc no-timing, 广州/贵州 and Conversation regressions.
- Language UX mocks cover target/no-target rejection, uncertain rejection, fresh retry,
  no new History, and no assistant/analysis publication. These are plumbing tests only.
- Mobile lint/typecheck and web/Android exports pass. Artifacts/logs use `/tmp/benma-entry-*`.
- Final focused rerun after the compact 320 px spacing adjustment: **85 tests passed**.
- Unchanged-backend regression check: **64 passed, 2 optional private-recording skips** across
  provider adapters, perception truth, speech presence and target-reading/ownership tests.
  No backend code, schema, API contract, generated OpenAPI, database or migration changed.
- Chromium entry and existing workspace review **passed at 320/390/412 × 844 px**, with no
  horizontal overflow or page errors. Empty/target screenshots were visually inspected;
  Enter/Space/touch editing, independent speaker/clear controls and the complete primary
  attempt loop passed at each width. The review is recorded by
  `apps/mobile/scripts/workspace-browser.cjs`; all API/provider responses are intercepted.
  Screenshots and results go to `/tmp/benma-entry-review`. Physical native playback and
  VoiceOver/TalkBack still require device smoke; browser automation is not language-ID validation.

**One next technical step:** run a bounded source-language evaluation of an **unhinted,
prompt-free gpt-transcribe preflight**, retaining the existing Mandarin transcription path
until results support integration. Include short/accented Mandarin, English, another language,
ambiguous/mixed speech and empty-language output; establish Mandarin-versus-generic-Chinese
handling from observed provider codes. This would be a separately validated model/configuration
change, not a solved detector in this UI pass.

## Compact learner hierarchy

Practice shows the target (when present), current perceived phrase, one selected-unit detail and a fixed **Record / New Attempt** footer. The normal surface removes YOU, What Benma heard, Your pitch, the graph introduction, repeated recording-target text and reference disclaimers. Conversation retains its contextual heard/understood distinction and starts with pronunciation collapsed.

The Target card contains a small `Target` label, the Chinese phrase, tappable phrase/lexical-reading body and inline reference playback / clear actions. It replaces “Target active · every recording uses this phrase” and the stack of large action buttons. Reference audio uses `Play native reference for <target>`; whole-attempt playback uses `Play my full recording`. Both native and web playback render compact icons in this workspace. Existing non-workspace playback remains compatible.

The perceived phrase is the wrapping timed-unit row when it covers the lexical text; otherwise complete perceived text remains visible. Whole-recording playback sits in that phrase row, including when no timing is available. Unit playback sits beside the selected identity and reading, with `Play my recording for <unit>`. All icon actions have accessible names and at least 44 × 44 px hit targets. Pending downloads expose busy/disabled state. Selection remains a neutral outline, independent of correctness.

The normal selected panel is identity/reading/playback, retained pitch graph, experimental gesture (when eligible), measurement quality, and **More details**. Diagnostic codes, timestamps, expected tones and sandhi explanations move to details. Wrapped sentence units retain 24 px characters, at least 44 px width / 48 px height, and atomic groups. No horizontal sentence scrolling is introduced on the core surface.

**Change target**, **Edit reading**, **History**, and **Full pitch details** share `WorkspaceDialog`: a bounded, scrollable native Modal, visible close control, native back handling, and web Escape/focus containment. Full details contains the existing whole-utterance graph and **Raw** expansion. The primary recording loop remains outside dialogs. Advanced elapsed-time graphs retain their optional horizontal inspection.

## Reading selector and correction truth

The existing target pinyin correction workflow now offers discrete choices from `pinyin_alternatives`. A target with only one reading per unit has no edit-reading action. An ambiguous target opens **Edit reading**, with radio choices only for ambiguous units. There is no free-text pinyin or generic tone picker. The candidates are the existing dictionary/context vocabulary, which can include rare dictionary readings; this pass does not add a new lexical resolver or claim those rare candidates are common modern usages.

`parse_corrected_pinyin` now checks every requested reading against the existing target parser's supported candidates. Unsupported 我 → `wo4` produces the existing 422 `invalid_target` response before a revision is created. Valid corrections still append an immutable target revision and regenerate its reference; they preserve the alternatives so another valid reading can be selected later. The phrase itself never changes because a reading changes.

Target alternatives for 一/不 now use the existing `citation_reading` normalization. For 一个, lexical 一 is `yi1`, while the surface rules independently record T2 for 一; the aggregate surface list can remain unresolved because 个 is context dependent. For 不是, lexical 不 is `bu4` while its surface expectation is T2 before T4. Surface `yi2`/`bu2` are not offered as lexical corrections. Revising to the same lexical reading preserves alternatives and surface expectations. No surface engine rule changed.

This selector edits **target/reference reading**, not the perceived analysis. The existing perceived resolver continues to own attempt readings; no new perceived-reading override API was invented. Raw perceived text, saved readings, timing, graphs and audio remain unchanged when the target reading changes.

Transcript correction is a separate existing backend mechanism: `POST /v1/utterances/{id}/corrections` appends a `UserCorrection` with intended text and an optional owned perception ID. It does not rewrite `PerceptionRun.transcript`. There is no new large transcript editor in Practice. Choosing another legitimate reading never silently substitutes a different Chinese character.

## Evidence, identity and selection

`pronunciationWorkspace.ts` projects saved perceived syllables and accepted groups into units. A unit ID incorporates timing-evidence identity, character offsets, and the original start/end span. It references saved syllable objects. Only recorded-audio analyses with aligned/partial accepted timing create selectors. Synthetic timing and unavailable alignment do not. Untimed characters in a partly timed sentence remain readable without timed buttons. When no timing exists, the full perceived sentence and whole-recording playback remain available.

Grouped 雨伞 is one selector, one span, one graph projection, one detail identity and one Mine action. The group is an atomic flex item; no 雨/伞 timing or individual grade is inferred. Per-character timing remains independently selectable when actually supplied.

Default selection is deterministic: first actionable approved agreement (currently unreachable), otherwise first acoustically sufficient unit, otherwise first timed unit, otherwise none. Choosing a timed unit does not certify its pitch. New analysis/attempt identity remounts the workspace and resets selection/expansion. Unit taps only project saved data; they never rerun acoustics or submit recording workflows.

Perceived text, reading resolution, timing, observations, graph and audio stay independent of the intended target. For target 广州 and perceived 贵州, units remain 贵州; 广 → 贵 appears only as a separate textual difference. Context-sensitive expected surface references remain secondary. Connected T3 need not form an isolated U, and neutral tone has no fixed expected contour. Provider-conditioned phone labels are not independent observed phonetics. This pass introduces no segmental grader and removes none of the laboratory's separately guarded evidence.

## Comparison policy and future colors

**The UI architecture supports future color-coded agreement, but the current learner-comparison policy intentionally does not authorize confident positive/negative pitch judgments.**

`toneGestureMatch` continues returning uncertain for every comparison, including sufficient acoustics and unknown future policy strings. Acoustic eligibility is not permission to give learner feedback. `pitchAgreement` centralizes this abstention; `unitPresentation` centralizes visible labels/treatment. The semantic type reserves strong/partial/different/unavailable for a later approved policy, but no fake colored example or runtime switch enables them.

| Future color | Current production condition |
| --- | --- |
| Green / strong | Never emitted; no authorized strong-agreement rule |
| Amber / partial | Never emitted; uncertain does not mean partial match |
| Orange / difference | Never emitted; no authorized negative comparison |
| Neutral | Every unit, including sufficient acoustics |

Measurement labels use the saved backend eligibility, separately from gesture interpretation:

| Saved state | Learner copy | Actual meaning |
| --- | --- | --- |
| sufficient | Measurement: clear | Enough sustained retained evidence, with no completeness/discontinuity reason under the current rules |
| incomplete | Measurement: mixed | Voiced boundaries or substantial raw-to-selected support were lost; the panel says part of the measurement is missing |
| unstable | Measurement: mixed | Raw jumps or fragmented support; the panel says some pitch measurements disagree |
| insufficient / missing | Measurement: limited | Too little sustained evidence, no voiced support, or unavailable native tracker history |

“Clear” describes local measurement support under the existing rules, not verified speech presence, tracker ground truth or pronunciation correctness. The prior “Pitch evidence unstable” label could sound like learner failure. The new copy names the measurement explicitly. The presentation and future agreement seam remains centralized in `unitPresentation`; no semantic grade/color is enabled.

Only sufficient individual evidence permits the existing backend gesture vocabulary: Mostly level, Rising, Falling, Dipping, each marked experimental. Dipping does not assert a complete dip-and-rise. Unclear, incomplete, unstable and insufficient evidence show **Gesture unavailable**, even if an `observed_gesture` field happens to contain `dipping`. Groups never borrow a member's gesture. Diagnostic reason codes stay in More details, not the normal learner panel.

### Saved 买 investigation and physical-take limitation

The available saved longer-phrase take **40357072**, 我想买五把雨伞, gives 买 an accepted **1.94–2.52 s** span. Its only eligibility reason is `raw_pitch_discontinuity`: **3 jumps over 6 semitones**, maximum **10.734704 st**. It retained 41 of 51 raw voiced frames (0.8039), with early/middle/late retention 0.8824/0.9412/0.5882 and a longest retained island of 0.26 s. Neither attrition nor boundary-loss rules fired. The saved contour features also count three octave-like jumps; this is not proof of actual octave error. It is not a single isolated discarded outlier.

The retained geometry remains inspectable, but the backend intentionally suppresses gesture interpretation (`unclear`, low, `pitch_evidence_unstable`). A visually plausible valley is not enough to authorize an interpretation. The UI preserves that suppression and displays Measurement: mixed. **The newest physical 我想买 recording is not available as an inspectable artifact in this pass. These saved findings are not its exact diagnosis.** No acoustic thresholds or classifier were changed to make the graph look better.

## Graph truth

Selected graphs use the saved `tone_graph.filtered` retained measurements, falling back only to available measured points for older data. They do not use the smoothed Mine contour or synthesize expected shapes. Points belong to the selected half-open accepted span `[start,end)`. The existing later-start ownership rule resolves tiny accepted overlaps. Every source segment boundary and any exclusion during projection remains a gap. Source timestamps and pitch values are unchanged.

All units use the existing PitchPlot scale rule calculated across the same entire attempt; selecting a new unit does not recenter pitch or derive a prettier local range. Real start/end times define the horizontal axis. No relative-centering, robust-overflow, composed-relative, pitch-repair, or new scaling experiment is included. The selected plot is 104 px high. Full pitch details retains whole-utterance elapsed time, accepted groups/boundaries, gaps and optional raw tracker diagnostics. No graph infrastructure was deleted.

The normal-versus-exaggerated physical recordings establish that measured contours respond to deliberate gesture. They do not establish reliable lexical T1/T2/T3/T4 recognition.

## Exact Mine and canonical audio

The canonical option is necessary, not speculative complexity. `pronunciation/acoustics.py` and the alignment service read `canonical_audio_asset_id`; canonical ingest converts to mono PCM16 at 16 kHz. The original `/v1/utterances/{id}/audio` response serves `original_audio_asset_id`. Original codec decode/timing is not guaranteed sample-identical to canonical audio; canonical spans must not be applied to an unverified original decode.

The existing GET resource now accepts optional `canonical=true`. Omitted/false retains original audio exactly. Authentication, utterance ownership, selected AudioAsset ownership, UUID validation, private/no-store headers and the existing storage abstraction apply to both. The selector is a boolean, not a client-supplied path. No raw storage path, new database model, mutation, lock, migration or parallel media service was added. The client validates the utterance path before adding the fixed query. OpenAPI JSON was regenerated; DTO TypeScript is unchanged because no response DTO changed.

Each mounted workspace lazily caches one complete canonical byte download. `exactRecording` validates canonical mono PCM16/16 kHz WAV, retains only the accepted window, clamps against actual PCM frame count, and copies samples unchanged. Boundaries quantize to the nearest PCM sample (at most half a sample); there is zero context padding, fade, gain change, speed change or pitch processing.

The native Expo player uses file-backed playback and offers no sample-scheduled segment end in the existing cache adapter. Accordingly, only the **currently selected** segment is materialized as an ephemeral WAV in the existing private cache. Web uses the same PCM window as a Blob. This avoids an imprecise JS stop timer and a library of per-character files. Selection replacement/unmount deletes the old segment cache; the complete download is shared across selections and released when the workspace ends or auth resets. No cropped files are persisted in attempt history or on the server.

Existing playback registration gives one foreground player, recording interruption, cancellation of stale asynchronous downloads, safe repeated taps, and unmount cleanup. Selection/attempt changes stop playback; Stack blur and app background/page hiding also stop pending/active playback. No unit auto-plays. A failed canonical request does not fall back to original audio. Whole-recording playback keeps the existing original-upload semantics and needs no timing.

**Context playback is absent.** The research 40/80 ms settings are listening candidates, not approved production defaults. No contextual reference-unit playback is inferred from learner timing.

## Attempts and surfaces

- **Practice with a target:** one current entry, separate immutable target snapshot/comparison, selected-unit workspace, retained reference workflow, fixed New Attempt control, compact attempt counter and History. A new perceived result becomes current. Late analysis hydrates its own entry without switching the active history selection.
- **Practice without a target:** the same Practice screen and workspace with session-local history. Perceived speech is its only identity. There is no separate free-practice backend.
- **Conversation:** the `/conversation` route reuses `free-talk.tsx`. Heard text and whole-recording audio remain visible, pronunciation starts collapsed behind Explore pronunciation, and the assistant reply remains primary. Expansion mounts the same workspace. No practice retry/history mechanics were added to Conversation.
- **Pronunciation laboratory:** not redesigned; existing guarded experimental/provider diagnostics remain separate.

**New Attempt** preserves target and session history, clears the active attempt immediately (no fallback to the latest entry), unmounts selected detail/graphs/dialog state, stops playback via the existing recording lifecycle, clears retry/checkpoint state and starts microphone capture. A failed/no-speech new take leaves the workspace empty; history can explicitly reopen the prior take. Permission denial likewise does not restore stale graphs.

**Clear target** clears target/reference/draft, current attempt, selected detail, all entries/analyses for the exercise, transient dialogs/errors and playback, then returns to the empty untargeted entry state. A session generation guard ignores late analyses from cleared exercises. Preparing a different target starts a fresh exercise; canceling its dialog preserves the current exercise. Changing only a supported reading preserves previous attempts and their immutable target-text snapshots.

History reuses the existing in-memory entries/analyses and is **session-local to the mounted Practice screen**. Its compact header action opens a dialog, newest attempt first with an accessible Current marker. Reopening an old attempt replaces the one workspace. It is not persistent after reload and adds no before/after comparison feature.

## No-audio investigation

The traced path is: `useAudioCapture` → `useSpeechTurn` → `submitSpeech` → authenticated upload/canonical conversion → `AudioIngestService` `require_speech` → `PerceptionService` `require_speech` → provider ASR → `corroborate_transcript` → validated perception callback → workspace/optional target attempt.

The previous workspace diff did not change capture, upload, turn acceptance, presence checks, ASR requests or submission ordering. Its server audio change only added a canonical playback selector. Its recording label/footer and playback-stop handling did not bypass the guard. There is **no 500 ms client cutoff**. Digital silence at **500 ms and 10 s**, and deterministically near-empty audio, is rejected at upload without a successful utterance, perception, pronunciation attempt or conversation turn. The original upload asset remains audit evidence. Legacy accepted uploads are checked again before ASR; the provider is not called for either silent duration.

Focused tests raised the test-only upload duration limit to 15 s so the 10 s case actually exercises presence rejection rather than the fixture's old 5 s size/duration rejection. A ~350 ms successful perception still creates a learner attempt; no new short-Mandarin threshold was introduced. Mobile tests also reject `no_speech` at perception with no analysis, history or workspace.

Longer **room/background recordings** may contain enough sustained activity or periodicity to pass the existing permissive pre-check. The post-ASR corroboration path only applies to the ambiguous low-background/low-activity case; activity outside that case can still admit hallucinated Chinese. This is the documented pre-workspace false-positive blocker, not a demonstrated workspace regression. Duration alone cannot diagnose the user's new audio; those exact new physical files were not available. The deterministic guards were intact, so no production presence algorithm was modified. Speech presence generally remains unresolved, including deployment/Conversation acceptance risk.

## Regression controls and validation

Saved timing/identity extracts for 40357072 and d47274bc are in `workspaceTimingControls.json`; they intentionally omit pitch/audio and are not substitute acoustic fixtures. The browser review uses the complete saved six-take data locally, plus an explicitly synthetic long-sentence layout fixture. No live providers, recapture, or closed research benchmark reruns were used.

- Saved **40357072 雨伞**: one unit, exact 3.56–4.87 s accepted span.
- Saved **d47274bc**: no selectors, selected graph, or bounded Mine action; heard text and whole replay remain.
- **广州/贵州** and changed intended targets: readings/identity/graph/playback source remain perceived, comparison separate.
- Incomplete/unstable/insufficient evidence stays neutral and withholds observed-gesture interpretation. No-timing, missing reading, empty pitch and non-Han states remain explicit.

Historical validation for the preceding workspace polish pass (before the entry changes above):

| Check | Result |
| --- | --- |
| Final focused mobile Practice / workspace / Conversation / playback / API client / safety | 139 passed |
| Full mobile native + web suite | 31 suites, 392 tests passed |
| Mobile lint / typecheck | Passed |
| Web / Android exports | Passed; `/tmp/benma-polish-{web,android}` |
| Focused presence / lexical correction / ownership | 57 passed, 2 optional private-fixture skips |
| Relevant API audio, perception, reading, graph, gesture, pitch and concurrency subset | 306 passed, 2 optional private-fixture skips, 5 known streaming cases deselected |
| API Ruff / mypy | Passed; 78 source files |
| OpenAPI | Existing generated artifacts unchanged by the reading validation; determinism checked |
| Local isolated PostgreSQL regressions | 4 passed |
| Diff whitespace | `git diff --check` passed |

The appended tests were checked for imports, module structure, duplicate names and assumptions. Fixes included the missing pytest import, retaining 个's existing context-dependent surface expectation, and using a web-only Modal stub because react-test-renderer cannot mount ReactDOM portals. Real dialogs are exercised in Chromium. API tests run with `BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION=false` to isolate the laboratory's expected default from the local .env experiment flag; no production flag or grading policy was changed.

The five excluded API cases are the pre-existing streaming stalls documented in [checkpoint validation](../research/pronunciation-v2/2026-10-06-checkpoint-scope/validation.md): three parameters of `test_stream_orders_authoritative_interpretation_before_committed_reply`, `test_stream_generation_failure_keeps_perception_and_rejects_other_account`, and `test_meaning_bytes_leave_server_while_generation_is_still_running`. They were explicitly deselected, not claimed as passing. Closed tracker/VAD benchmarks were not rerun.

Responsive Chromium review covers **320, 390 and 412 × 844 px**, target actions, atomic groups, compact playback, the complete visible primary loop, fresh attempts, history, clear-to-free-practice, reading selection, no timing, dialog keyboard focus/Escape and Conversation collapse. Screenshots are visually inspected; native sound and VoiceOver/TalkBack still require physical smoke. The first browser review caught the separate web playback component ignoring compact props; that was fixed and actual button dimensions/clipping and unchanged playback bounds in playing/paused states are now asserted. Short sentence units use 2/1/1 rows at 320/390/412 px; the long layout fixture uses 6/4/4. The complete short primary loop fits at all three reviewed heights, with no browser page errors.

Reproduce with `apps/mobile/scripts/workspace-browser.cjs`; set `PLAYWRIGHT_MODULE`, serve the exported app at `BENMA_WEB_URL`, and provide the ignored six-take viewer data via `BENMA_WORKSPACE_FIXTURE` if needed. Screenshots and `review.json` live under `/tmp/benma-polish-review`, not tracked source. API/provider responses are offline fixtures, not live inference.

## Earlier workspace boundary

The known false-positive speech-presence issue remains a **deployment blocker**. Non-speech can still be accepted and perceived as Chinese, potentially creating a neutral pitch workspace or Conversation response. No UI color, acoustic eligibility or successful request certifies speech presence. Tracker and VAD research remain closed.

The earlier workspace checkpoint called for a second physical UI smoke. The current entry pass and its single technical follow-up are described at the top of this document. Context padding and authoritative color comparison remain separate unresolved decisions; deployment is not authorized.
