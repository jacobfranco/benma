# Pronunciation chunks V1 — October 9, 2026

**PRONUNCIATION CHUNKS V1 EARNED INTEGRATION.**

Presentation follow-up: the learner pitch cleanup keeps the partial 这个 graph and
whole-chunk playback, replacing the original partial-measurement sentence with
“Pitch detail is limited.” More Details preserves constituent availability and exact
playback. See the [current workspace presentation](../../../development/pronunciation-workspace.md).
The original implementation account and research conclusions below are unchanged.

The reviewed policy is deliberately limited to **雨伞, 这个, 那个, and quantity-use 一个**.
Existing accepted timing groups remain indivisible, including groups outside this list.
Everything else stays a singleton unless an existing timing group already owns it.

**ACOUSTIC UNIT != PRONUNCIATION CHUNK**

**READING PHRASE != PRONUNCIATION CHUNK**

**PRONUNCIATION CHUNK != TARGET WORD**

The API supplies exact perceived linguistic candidates. The workspace forms an ordered
partition from whole accepted timing units, with missing timing and the existing visible
pause marker able to veto a merge. It does not reinterpret Mandarin independently.

The saved 我想买这个 recording becomes **[我] [想] [买] [这个]**. The chunk spans
**2.34–3.04 s** for exact canonical playback and graph display. Its 20 retained pitch
points all remain owned by 这; 个 still has zero retained points. The default panel says
“Pitch was measured for part of this chunk.” More Details provides separate exact 这
and 个 playback, readings, timing, measurement status, and graphs. The grouped 雨伞
recording remains one span at **3.56–4.87 s**, without invented 雨/伞 boundaries.

No acoustic thresholds, pitch selection, source indices, timing, reference pronunciation,
reading resolution, surface-tone rules, gesture classification, comparison policy, or
tone colors changed. There is no chunk score or aggregate gesture. The existing research
conclusions remain: **PER-UNIT PITCH PROJECTION VERIFIED; ENERGY GATE NEEDS ONE SPECIFIC
REFINEMENT; GESTURE READABILITY NEEDS ONE SPECIFIC REFINEMENT; COLOR NOT YET JUSTIFIED.**

**READY FOR PHYSICAL CHUNK UX SMOKE**, subject to the validation limitations recorded in
[validation.md](validation.md). Automated browser playback is not a phone listening test.
No physical smoke is claimed. No commit, push, or deployment was performed.

- [Exact policy and deferred categories](chunk-policy.md)
- [Grouping audit, schema, planner, and evidence architecture](architecture.md)
- [Bounded saved/design fixture review](fixture-review.md)
- [Validation, limitations, and phone checklist](validation.md)

The interrupted worktree contained the candidate schema, pure API generator, response
enrichment, and generated OpenAPI/DTO changes. There was no client planner, chunk UI,
chunk test suite, or chunk documentation yet. The pre-existing modified workspace tests,
pitch/energy fixtures, and untracked gesture research were preserved. Work continued on
`pronunciation-v2-research`; no repository state was reset, reverted, stashed, or discarded.

Future research question, intentionally unanswered: should pitch agreement color live on
the constituent timing unit, the pronunciation chunk, or both? Keeping source units and
the learner projection separate leaves all three possible without authorizing any color.

**One next step:** perform the phone checklist in [validation.md](validation.md).
