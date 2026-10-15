# Contextual comparison and learner details

**COMPARISON NOT YET JUSTIFIED; COLOR NOT YET JUSTIFIED.** The observed shape layer
ships independently. The comparison function in the numeric audit is a research
proposal with no production import, grade, badge or color mapping.

## Expected behavior is a separate source

`expectedShapeLabel` reads the existing server contextual `expected_surface_tone`
and reading resolution for the **perceived** unit. It never infers tone from pitch,
uses target identity, or falls back from an unresolved surface expectation to a
lexical-tone cartoon. Surface 1/2/4 become Level/Rising/Falling. Surface 3 is
“Low or dipping · a full rise is optional”; neutral is “Flexible · neutral tone”.
An unresolved reading is “Reading unresolved”; an unresolved contextual decision
is “Context-dependent”. Existing 一 quantity/ordinal/ambiguous rules, 不 sandhi,
T3 pair sandhi, flexible quantity 个 and unresolved prosodic chains are preserved.

In particular, the 我想买 T3 chain is contextually unresolved by current linguistic
truth. Showing a readable dip for 我 does **not** establish an expected full dip/rise.
The new UI therefore does not claim “Your rise is weak” for that recording. A learner
may have produced an entirely appropriate reduced T3 realization. Surface T3 also
allows low movement: a relative shape class cannot by itself establish low register.

## Research-only semantics

- **STRONG_MATCH:** stable observed shape, adequate support and constrained contextual
  compatibility. The candidate requires matching Level/Rising/Falling; directional
  movement must be >=2 st. This means pitch-shape agreement only, never perfect speech.
- **PARTIAL_OR_WEAK:** matching rise/fall with 1.5–2 st endpoint movement, or a stable
  dip compatible with an expected low/dipping realization but without enough evidence
  to establish strong contextual agreement. Weak limb support is retained as numeric
  evidence; no universal T3 recovery requirement is invented.
- **CLEAR_DIFFERENCE:** stable rise versus constrained expected fall, or stable fall
  versus constrained expected rise. Measurement messiness alone cannot produce this.
- **UNAVAILABLE:** no coherent shape, insufficient/unstable evidence, grouped timing,
  unresolved reading/context, unconstrained neutral shape, or unvalidated deviation.

The initial exploratory mapping treated flexible neutral behavior as partial and used
full range to assess rise strength. Review rejected those choices: flexibility alone
is not a weak positive, and a weak net rise is not strong because of incidental range.
The final research prototype uses UNAVAILABLE for neutral and endpoint movement for
rise/fall strength. Production was never given either mapping.

Frozen result: **0 strong, 5 partial, 3 clear differences, 45 unavailable**. Four partials
are expected-low/dip examples; the fifth is `8d252264:一`, a 1.646 st rise under the
existing quantity 一 expectation. The three differences are `4b9dbd2b:一`,
`8faf1a90:苹`, and `a5acd04c:苹`: stable falls versus expected rise. These comparisons
are plausible hypotheses, not independently validated learner feedback. There is no
positive strong-match coverage in this frozen set, no adequate labelled reduction/
prosody comparison set, and recording acceptance remains unearned. Synthetic semantic
regressions demonstrate rule behavior but cannot fill those empirical gaps.

**No green/amber/orange/gray grading rules are active.** If eventually earned, proposed
colors remain green=strong pitch agreement, amber=partial/weak agreement,
orange=clear coherent conflict, gray=unable to judge. No red or scores. Neutral selector
backgrounds and the teal trace are interface styling, not agreement states.

## Chunks

Keep judgments attached to accepted constituent timing units as an architectural seam;
no aggregation policy is activated. For 这个, all 20 retained points belong to 这 and
个 still has none. The chunk keeps whole-span playback, truthful proportions, and
“Pitch detail is limited.” In learner details, 这 and 个 can be inspected independently.
The contradictory 这 fragments currently yield unclear; missing 个 never makes 这
incorrect or the chunk orange. Grouped 雨伞 has one accepted timing identity, so no
individual character shape, playback or grade is invented.

## Final details hierarchy

More Details contains selected unit/chunk, reading and exact playback; “Your pitch”;
a 152 px clean normalized plot; “Measured shape”; contextual “Expected”; and the
established missing/limited evidence copy where needed. Multi-unit chunks include
constituent controls. Stable geometry is stated directly without “Experimental”,
“Probably” or “Maybe”. No unearned comparison sentence is added.

**Technical details** starts collapsed. It retains saved strict gesture, eligibility,
measurement status/reasons, true timestamps, source evidence ID and frame indices
where available, the new shape features/perturbations, and the real-time sentence
view. **Raw** still exposes tracker/selected points and exclusion reasons. Diagnostic
text, raw energy exclusions and uncertainty do not crowd the learner surface. Dialog
focus containment/Escape, keyboard selection, accessible playback targets and textual
shape descriptions work without color. Native screen-reader listening remains physical
validation, not something the browser suite can certify.
