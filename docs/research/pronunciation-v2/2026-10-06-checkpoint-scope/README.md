# BENMA — Tone Graph V2 checkpoint scope and release posture

October 6, 2026 · `pronunciation-v2-research` · uncommitted branch checkpoint review.

**Recommendation: OPTION B — CHECKPOINT WITH FEATURE-GATING.** The evidence architecture is coherent enough to preserve. After the bounded semantic fixes below, proceed to one four-case physical smoke, then seek the separately required commit authorization. **DO NOT DEPLOY YET.** A known presence false accept is a product release blocker, not a reason to discard the architecture or reopen tracker/VAD search.

## Seven decisions

| Decision | Result |
|---|---|
| 1 — Graph/evidence architecture | **ARCHITECTURE COHERENT AND CHECKPOINTABLE** |
| 2 — Learner-facing safety | **CURRENT UI IS SUFFICIENTLY CONSERVATIVE** after containing the legacy screen and default setting |
| 3 — Presence limitation | **KNOWN AND CONTAINED ENOUGH FOR BRANCH CHECKPOINT**; turn acceptance itself is unresolved |
| 4 — Research stack | **RESEARCH ARTIFACTS SUFFICIENTLY REPRODUCIBLE**, subject to private-input and optional-environment boundaries |
| 5 — Checkpoint | **READY FOR FINAL PHYSICAL SMOKE THEN COMMIT**; no commit authorization implied |
| 6 — Deployment | **DO NOT DEPLOY YET** |
| 7 — Exactly one next step | **RUN FOUR-CASE FINAL PHYSICAL SMOKE** |

## What this stack is

An immutable, character-free acoustic evidence foundation with transcript-conditioned timing and conservative pitch visualization. Acoustic completeness, linguistic interpretation, reference comparison and speech presence have separate responsibilities. Perceived characters are not independently detected segmental identities. An utterance graph is not a full pronunciation assessment.

Safe claim: **Benma visualizes measured pitch aligned, where timing is available, to what it perceived. Missing evidence stays missing, incomplete or unstable evidence suppresses gesture interpretation, and tone comparison remains uncertain. Pitch gestures are experimental descriptions, not pronunciation grades.** Acceptance as speech remains fallible.

## Findings and changes in this pass

The primary graph already held every comparison uncertain. The audit found a separate reachable legacy `/pronunciation` view displaying “Evaluator detected Tone …” and saved interpretation messages in its default and A/B views; `enable_experimental_tone_interpretation` also defaulted true.

This pass sets that existing flag's code/example default to false, labels new API provider observations as uncalibrated/experimental, increments the interpretation policy version, and keeps legacy default/A/B displays neutral. Historical provider/interpretation payloads remain available only in explicitly labeled advanced diagnostics. A screen regression covers a cached old message; a backend regression covers the conservative default. The final XFAIL audit also narrows expected assertion handling to a dedicated presence-failure exception, so corrupted corpus hashes and unrelated assertions cannot be hidden. Home copy now describes measured pitch. No UI redesign, classifier, presence threshold, acoustic heuristic or model integration was introduced.

The local ignored `.env` still explicitly enables legacy experimental diagnostics and Azure timing. It is not staged or edited; its credentials were not printed. That diagnostic override does not enable graph grading. Checked-in code and example configuration both default the experimental interpretation flag off; categorical grading remains unavailable. No production source imports the Silero/RMVPE/CREPE research adapters, and dependency manifests are unchanged.

Research retention excludes generated figures, the generated Silero viewer, local archive receipt, stale Git snapshots and raw validation logs through exact `.gitignore` entries. Nothing was deleted. The source HTML template is retained. Historical research conclusions/metrics remain unchanged; the development overview now supersedes older proposed experiments and readiness statements.

## Three checkpoint options

| Option | Assessment |
|---|---|
| A — Full checkpoint, not production ready | A coherent architecture/research checkpoint is legitimate despite the presence issue. However, “entire stack” must still exclude private/generated artifacts, and the discovered legacy semantic exposure needed containment. Not the selected posture. |
| B — Checkpoint with feature-gating | **Selected.** Preserve architecture and experimental diagnostic vocabulary; retain always-uncertain primary comparison and neutral legacy views; use the existing laboratory flag with an off default. No new flag system. |
| C — Do not checkpoint | Not warranted by the remaining documented limitations. Relevant deterministic/integration coverage passes within explicit scope; expected presence failures are visible and strict, not silently accepted as correct behavior. |

## Release limits

Known accidental silence passes the retained presence guard and can create misleading text/history. In Conversation it can become an assistant input, produce a durable reply and lead to a TTS request. Honest pitch plots cannot make that turn legitimate. Neither the small smoke nor this report establishes general tone-grading reliability or production Conversation acceptance safety.

Tracker search and VAD-model search are closed. The saved Silero result rejects integration, not the negative label: its apparent high confidence did not fix the critical recording. No provider calls, new recordings, model downloads, tracker/VAD evaluation, staging, commit, push or deployment were performed in this pass. Tests use local fixtures, saved artifacts and isolated PostgreSQL schemas.

## Report map

- [Working-tree inventory and private/large artifact audit](working-tree-inventory.md): every initial/final candidate, exact include/exclude boundary, ignored private categories.
- [Product semantics](product-semantics.md): live wording, activation conditions, policy, every new API field and dead/duplicate paths.
- [Presence blast radius](presence-blast-radius.md): Practice, Free Practice, Conversation and graph versus turn trust.
- [Validation](validation.md): exact tests/counts, failures, exclusions, static checks and reproducible commands.
- [Commit plan](commit-plan.md): four-case smoke, exact staging allowlist source, retained artifacts and one proposed message.

The [current development summary](../../../development/tone-graph-v2.md) is the single-file entry point. This report supersedes earlier research requests for additional F0 or VAD work without altering those historical reports.
