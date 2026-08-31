# Speech truth invariants

These are permanent product rules, not temporary replay-provider limitations.

## Rule 1 — unknown means no semantic target

Unknown-target perception receives owned canonical audio, audio identity, a Mandarin language hint,
and timeout only. Target text, intended text, pinyin, prompts, vocabulary hints, corrections,
conversation history, and context are rejected at the API contract, absent from the internal type,
not queried by the service repository, and absent from serialized live-provider requests.

## Rule 2 — raw perception is not inferred intention

A `PerceptionRun.transcript` records what that provider returned for that run. It cannot be replaced
with a target, contextual guess, normalized correction, or more plausible sentence.

## Rule 3 — corrections append

`UserCorrection` records what the speaker later says they meant. It belongs to the same account and
utterance and may reference a run, but it never updates that run. UI must show “what Benma heard”
and “what you meant” as distinct statements.

## Rule 3a — semantic context travels only downstream

The permitted flow is audio-only perception to immutable perception evidence to contextual
interpretation. Context may support a downstream `preserve`, `infer`, or `clarify` decision, but it
never enters `UnknownTargetPerceptionInput`, a perception-provider request, or a mutation of a
`PerceptionRun`.

## Rule 4 — reruns create evidence

Each provider invocation creates a new `PerceptionRun` or `AssessmentRun`, including failures.
Retry never overwrites a prior success or failure. Domain sessions reject updates and deletes of
evidence rows.

## Rule 5 — missing capabilities remain missing

Normalized DTOs omit unavailable values. A pronunciation provider that has no trustworthy tone
field produces an explicit unsupported-capability statement, not a fabricated tone, score, or icon.

## Rule 6 — provider scores are not listener truth

Vendor scores and uncertainty are preserved with their provenance. They are not automatically
converted into calibrated human intelligibility, percentages, correctness thresholds, or pass/fail
labels. Such interpretation requires comparison against blinded human listeners.

## Rule 7 — synthetic evidence is visible

Every replay result is marked `synthetic_replay` in normalized evidence and presented as
“Development fixture — not real speech evaluation.” Replay results cannot silently stand in for a
failed live provider.

## Rule 8 — F0 remains diagnostic

Fundamental-frequency analysis remains diagnostic research evidence until empirical validation
promotes a particular algorithm and interpretation. It is not learner grading in this product slice.

## Product-to-research boundary

Production audio is account-owned data. It is never copied into `benchmark/` automatically. A
future import path must begin with explicit research selection and consent, then create a separate
benchmark artifact with its own provenance. No consent system is implied or implemented here.

The release-blocking tests for these rules cover strict request rejection, narrow service access,
live request serialization, append-only sessions, retry behavior, corrections, synthetic labels,
unsupported fields, audio preservation, and cross-account ownership.
