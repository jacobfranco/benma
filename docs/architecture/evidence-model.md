# Future Benma evidence and service boundaries

Pass 2 should begin as a modular monolith. Ports protect evidence semantics and vendor replacement;
they are not a request to deploy separate services.

## Immutable evidence model

```text
Utterance
  └── raw audio asset + hash
      ├── PerceptionRun       what an audio-only listener returned
      ├── AssessmentRun       known-target evaluator evidence
      └── AcousticRun         independent measurements

ContextualInterpretationRun  contextual guess; references PerceptionRun
UserCorrection               asserted intent; references Utterance
ErrorEvent                   derived diagnosis; cites one or more evidence runs
```

A `ContextualInterpretationRun` may say context makes 北京 likely even if the perception transcript
was 背景. It snapshots its semantic context and uncertainty, and may mark that clarification is
needed. It may not update that transcript. A `UserCorrection` may record “I intended 北京”; it may
not rewrite the earlier raw response. Rerunning a provider creates a new versioned run. Deleting a
raw response to save space would break auditability; retention policy should archive/encrypt
instead.

The contextual interpreter receives the perceived transcript and an allowlisted snapshot of
normalized perception evidence. Raw provider payloads remain on the perception run's audit path
and never enter contextual interpreter input.

The boundary is deliberately one-way:

```text
audio-only perception
    ->
immutable PerceptionRun + normalized perception evidence snapshot
    ->
contextual interpretation (preserve | infer | clarify)
```

Semantic context is introduced only at the last step. It must never travel backward into the
unknown-target perception request, provider prompt, vocabulary hints, or persisted perception
evidence. A contextual decision appends a new run; even an `infer` decision cannot update its source
`PerceptionRun`.

## Initial ports

- `PerceptionPort(UnknownTargetPerceptionRequest) -> PerceptionRun`
- `PronunciationAssessmentPort(KnownTargetAssessmentRequest) -> AssessmentRun`
- `AcousticAnalysisPort(audio) -> AcousticRun`
- `AlignmentPort(audio, target) -> AlignmentRun`
- `ToneInterpretationPort(evidence bundle, linguistic target) -> derived tone hypotheses`
- `TTSProviderPort(text, voice constraints) -> reference audio` (defer until selected)
- `ConversationReasonerPort(perception evidence, conversation state) -> Interpretation`

The reasoner never implements or calls `PerceptionPort` with context. Product domain objects consume
normalized contracts and stable evidence IDs, never vendor JSON. Vendor JSON is available through
an audit/research path.

## Replacement criteria

A provider replacement is a configuration/adapter change after it passes the frozen corpus and is
better on relevant independent dimensions. It must not require migrating historical raw results
into a new vendor shape. Threshold/normalization changes are versioned interpretations over old
evidence, not destructive rewrites.
