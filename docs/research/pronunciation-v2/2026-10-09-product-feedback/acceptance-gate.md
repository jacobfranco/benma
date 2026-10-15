# Acceptance preflight

**ACCEPTANCE NEEDS ONE SPECIFIC FOLLOW-UP.** Unhinted detected language is useful,
but the proposed gate would reject a protected low-F0 positive. No production
acceptance gate, ASR model switch, route ordering or retry copy was integrated.

## Confirmed physical negatives

Read-only local PostgreSQL inspection found both recordings. The user explicitly
confirmed their identity in this conversation; these are no longer tentative matches.

| Recording | Capture UTC / EDT | Current conditioned result | Current evidence |
| --- | --- | --- | --- |
| `01f22591ea244e4cae4818724df25eff` | Oct 10 01:59:00 / Oct 9 21:59:00 | 请用简体汉字。 | presence passes; 9 retained track points; timing unavailable; one normal attempt already exists |
| `d40b357a157545769ab731fff3e97ce6` | Oct 9 02:10:06 / Oct 8 22:10:06 | 所以我感觉我把UI改了很多。 | presence passes; 253 retained track points; timing unavailable; one normal attempt already exists |

Full SHA-256, perception IDs, timestamps and derived measurements are frozen in
[negative-controls.json](negative-controls.json). Another “所以。” take was inspected
as an unconfirmed candidate and was **not** relabelled as either confirmed negative.
No audio was committed, no saved attempts were altered/deleted, and no listening
claim is made; user confirmation establishes the physical test labels.

## Available signals

The configured provider remains `gpt-4o-transcribe` with a fixed Mandarin prompt and
`zh` hint. Saved JSON has text, token logprobs and usage; it lacks independent language,
ASR word times, no-speech probability and language confidence. Mean conditioned
logprob is about -0.556 for throat-clear, -0.459 for English, -0.013 for the clear
Mandarin control. These are transcription-model probabilities, not validated
speech/language acceptance probabilities. No cutoff was inferred from three values.

Before perception, canonical duration and existing acoustic presence are available.
Presence records background RMS and longest activity/periodic runs, not a syllabic
region count or calibrated probability. It marks throat-clear activity/periodicity
as 0.17/0.09 s; protected low-F0 speech as 0.01/0.07 s. Requiring more periodic duration
would endanger the positive before rejecting the negative. No generic acoustic grid,
VAD bakeoff, tracker experiment or energy threshold adjustment was run.

Saved timing success and F0 coverage are available later. Timing is conditioned on
perceived text, may be unavailable for real Mandarin, and normally arrives after
attempt creation. It is not independent language evidence and is not suitable for
retroactively legitimizing a transcript. The corpus includes an untimed Mandarin
recording; requiring alignment would reject it. No syllabic detector is assumed to exist.

## Capability and authorization

Current official [file-transcription documentation](https://developers.openai.com/api/docs/guides/speech-to-text)
was fetched during this pass. It documents `gpt-transcribe` detected `languages`, with
an empty list when language cannot reliably be identified. This supports an unhinted,
prompt-free experiment; it does not promise calibrated confidence or exhaustive
language coverage for mixed speech.

The English-only probe was explicitly approved and completed first. Automatic approval
review initially required explicit private-payload authorization; the user granted it.
The continuation then explicitly approved **exactly nine** entries already pinned in
`/tmp/benma-product-feedback/preflight-manifest.json`. The source runner checked all
nine hashes before requesting, made one request each, never retried the timeout and
never substituted audio. Requests contained only model, JSON format and WAV bytes:
no language, languages, prompt, keywords, target, history or semantic hints.

[approved-upload-manifest.json](approved-upload-manifest.json) preserves IDs, hashes
and real durations without private storage paths. [acceptance-preflight.json](acceptance-preflight.json)
preserves responses/latencies/errors and the prior English probe. The mixed control
concatenates existing English, 200 ms silence and the approved Mandarin take; it is
an artificial mixed control, not a newly recorded natural mixed utterance.

## Exactly nine prepared results

| ID | Actual duration | HTTP/result | Returned text | Languages, in returned order | Proposal |
| --- | ---: | --- | --- | --- | --- |
| throat_clear | 2.043375 s | 200 | empty | `[]` | UNKNOWN → generic retry |
| clear_mandarin | 3.250813 s | 200 | 我想买这个。 | `zh` | ACCEPT |
| ambiguous_mandarin | 2.716750 s | 200 | 我想买五八一三。 | `zh` | ACCEPT |
| short_human_a | 0.170 s | 200 | 对。 | `zh` | ACCEPT |
| short_human_c | 0.200 s | ReadTimeout, ~30.20 s | unavailable | unavailable | UNKNOWN → generic retry |
| short_native | 0.300 s | 200 | 我要一个。 | `zh` | ACCEPT |
| low_f0_excerpt | 0.260 s | 200 | empty | `[]` | UNKNOWN → generic retry — protected positive lost |
| digital_silence | 1.000 s | 200 | empty | `[]` | RETRY from existing acoustic absence |
| mixed_english_mandarin | 11.159875 s | 200 | English sentence followed by “Washing my chuka.” | `en` only | RETRY; mixed coverage not reliably exposed |

The earlier 7.709063 s confirmed English take returned an English transcript and
`[{"code":"en"}]`. This is **one recording / one successful English-only request**,
not established general reliability. Eight of the nine additional requests succeeded;
one timed out. Successful responses contain **no confidence/probability/ranking**.
Every nonempty language list has exactly one entry; the mixed control does not expose
both languages. A list's order cannot be treated as a confidence ranking. `usage.seconds`
is rounded provider duration accounting, not a replacement for canonical WAV duration.
Another-language control, confirmed standalone 嗯/好/不/可以, and a user-confirmed
Mandarin-gibberish recording were not available in the approved set. No substitutes
or additional recordings were uploaded. Short excerpts do not prove exact transcript
accuracy, even when they preserve Chinese language detection.

## Research policy and why it does not ship

`product_acceptance.py` is research only:

1. Confident existing acoustic absence → RETRY.
2. Failed/missing preflight or empty language metadata → UNKNOWN.
3. Only zh/cmn detected and not acoustically absent → candidate ACCEPT.
4. One non-Mandarin code → RETRY; multiple distinct languages → UNKNOWN.

No transcript string, Han count, dictionary validity, lexical correctness or duration
cutoff enters the proposal. This preserves arbitrary text structurally; the ambiguous
physical recording provides limited empirical support, not comprehensive gibberish
certification. UNKNOWN and RETRY would show **“Try recording that again.”** Language
metadata from the mixed example is not enough to assert that no Mandarin was spoken.

The throat-clear now differs materially from its Mandarin-conditioned hallucination:
empty text and no detected language. But **the same result occurs for protected
low-F0 speech**, and the current acoustic-presence check passes both. Reject-all-UNKNOWN
loses valid speech; accept-UNKNOWN admits the throat-clear. No safe exception is earned.
The short timeout also leaves its language outcome unmeasured. Thus the gate is promising,
not integrated. Future refinement must address this specific UNKNOWN boundary; it
must not repeat generic VAD research or silently reinterpret absence of language as
absence of speech. Any further audio upload requires separate user approval.

Practice, untargeted Practice, Conversation, streamed Conversation and History retain
existing acceptance behavior. The confirmed negatives can therefore still become
normal attempts in the current product. Existing digital-silence rejection remains.
No new “no rejected History/assistant response” guarantee is claimed. When acceptance
is eventually earned, its decision must precede creation of normal attempts, analysis,
history entries and assistant generation; immutable perception evidence can remain
stored separately for diagnostics.
