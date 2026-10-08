# Checkpoint boundary and four-case physical smoke

**Option B: checkpoint with existing conservative semantics/gates.** Checkpoint status: **READY AFTER FOUR-CASE PHYSICAL SMOKE**. Deployment: **NOT READY / NOT CERTIFIED**, because speech-presence false acceptance remains and general tone interpretation is experimental. A passing graph smoke does not qualify Conversation turn acceptance.

Nothing has been staged, committed, pushed or deployed. The branch remains `pronunciation-v2-research`; the existing deletion of `PronunciationFeedback.tsx` stays part of the intended checkpoint. Commit authorization must arrive in a later user turn.

## Exactly four primary smoke cases

Perform these in the existing Practice flow in a separately authorized physical test session. This pass does not initiate recordings or provider calls. A single case exercises the shared graph used by Free Practice, target Practice and Conversation; there is no additional per-mode matrix. Use More detail or tap only where needed to inspect the stated boundary.

| Case | Action | Expected behavior |
|---|---|---|
| **1 — Normal speech** | In Free Practice, say naturally **我要一个苹果**. | Perceived text should be sensible; the character graph follows what Benma heard. Measured fragments should broadly resemble the produced voice. Incomplete regions remain neutral. No authoritative correct/wrong grade or stale “Evaluator detected Tone …” wording. |
| **2 — Alter 苹** | Say **我要一个苹果**, making **苹 strongly falling**. | If tracking/timing is sufficient, the measured 苹 region should show the falling movement. It must not be repaired toward reference T2. Missing/incomplete evidence must yield abstention, not an invented complete contour. Comparison remains uncertain even if an experimental falling description is available. |
| **3 — Perceived truth versus target** | Set target **广州**; deliberately say **贵州**. | Graph identity follows perceived text, ideally 贵州. The pitch track belongs to the actual waveform. A target text difference is separate; target 广 must not replace perceived 贵 or alter its measured contour. If ASR hears something else, preserve that actual output and record the recognition issue rather than substitute the intended answer. |
| **4 — Grouped timing** | Say **我想买五把雨伞**. | Use trustworthy per-character timing if supplied. If only trustworthy word timing exists for 雨伞, show one grouped measured span. Do not invent an equal split or individually grade 雨/伞. If neither timing tier is trustworthy, show missing timing conservatively. |

The smoke answers only:

1. Does the graph broadly look like the voice actually produced?
2. Does poor evidence visibly abstain instead of overclaiming?
3. Does perceived text remain the graph identity, separate from the target?
4. Does grouped timing avoid fabricated precision?
5. Does any stale authoritative tone-grading UI leak through?

If those hold, the intended architecture smoke passes. A consistently absent/unusable graph, measured contour replaced with a reference, invented timing or grading leakage is a concrete checkpoint blocker. Do not require an exact gesture label for incomplete evidence, force a grouped result when real character timing exists, or treat an ordinary ASR error as permission to overwrite the graph.

**Silence is not one of the four pass/fail cases.** If the user incidentally tries silence, record what happens. Successful silence rejection is not a prerequisite for this graph checkpoint; the already established false acceptance remains a deployment concern. No fifth required test and no new presence research are proposed.

## Exact proposed commit boundary

The boundary contains **258 KEEP paths** (A: 24, B: 24, C: 13, D: 2, E: 21, F: 174) and **25 excluded generated/local paths**.

The authoritative **file-by-file allowlist is the “KEEP IN COMMIT” table in [working-tree-inventory.md](working-tree-inventory.md)**. It lists each path, status and exactly one category. It includes these six report files themselves. The accompanying “EXCLUDE AS GENERATED/LOCAL” table is a denylist of the 25 initially visible research outputs now ignored. The ignore rules preserve those files locally; none was deleted or staged.

| Include | Reason |
|---|---|
| **A — Production core** | Character-free immutable pitch evidence, shared AcousticRun reuse, projections/eligibility, exact perceived timing/reading/surface semantics, existing presence guards and downstream account-owned boundaries; the bounded legacy wording/default fixes; `services/api/.env.example` |
| **B — Production tests** | Backend evidence/timing/presence/Conversation regressions, private-corpus opt-in tests (metadata only), sanitized numeric pitch fixture, native/web/mobile tests and cached-legacy-wording regression |
| **C — Mobile product** | SentenceToneGraph, measured geometry, neutral comparison policy, shared workflows, conservative legacy display and existing superseded component deletion |
| **D — Generated API/client** | Both `apps/mobile/src/api/openapi.json` and `openapi.generated.ts`; they exactly match canonical generation and must travel with the schema |
| **E — Reproducible research tooling** | Research scripts/tests, acoustic-window manifest, browser-check source and **`benchmark/pronunciation_v2/f0_foundation_viewer.html` source template**; `.gitignore` retention rules |
| **F — Documentation/numeric research evidence** | Current development overview, mobile/API READMEs, the seven prior research directories' retained reports/manifests/tables/receipts and this six-file checkpoint report |

Retained numeric reports include 48 saved Silero probability timelines, corpus/default/threshold/model-provenance metadata, acoustic/eligibility replay and retention summaries. They document fixed decisions and permit artifact checks without repeating inference. The 1.20 MB sanitized numeric pitch fixture drives production regressions; the 1.67 MB utterance replay preserves region-level explanations. Neither contains raw waveform bytes. These are deliberate text evidence inclusions, not automatic retention of every generated file.

| Exclude | Boundary |
|---|---|
| **G — Generated/transient** | Generated Silero `viewer.html`, all 18 PNG figures under the speech-presence/Silero report directories, three old `git-state.txt` snapshots, two `validation-output.txt` logs and the local `archive-verification.json`; exact paths in inventory |
| **H — Private evidence/configuration** | Raw/canonical audio and provider capture files in ignored storage; local `.env` (including its research diagnostic opt-in); private corpus waveform inputs and local audio inventories; no force-add |
| **I — Weights/cache** | Silero/RMVPE/CREPE weights, downloaded dependencies, virtual environments, activation arrays/caches and runtime files |
| Local exports/scratch | `/tmp/benma-checkpoint/*`, ignored `services/api/var/checkpoint-scope/*`, other `services/api/var/`, Expo outputs and caches |

Research tests requiring private audio or models are opt-in/not in the portable checkpoint command. Generated presentation tests require local regeneration. Existing historical reports can mention excluded local artifacts; such references are historical output pointers, not claims that the bytes are in Git. Do not force-add them just to make an optional viewer test pass on a clean clone. Scripts, manifests, decisions and portable numeric checks remain available.

## Staging procedure for a later authorized turn

Use only the exact KEEP table paths, with deletion-aware staging for `PronunciationFeedback.tsx`. Do not stage all ignored storage or force-add any file. Recheck the actual staged paths against the allowlist and confirm `.env`, recordings, models, cache, PNGs, generated viewers and logs are absent. Recheck the generated contract pair and `git diff --cached --check`. Any new paths introduced after this report require classification first. These are review instructions, **not an authorization to stage or commit now**.

## One proposed commit message

```text
feat: add character-free perceived-speech tone graph
```

This describes the acoustic foundation and learner visualization without claiming tone-detection or grading accuracy.

## Final decisions

1. **ARCHITECTURE COHERENT AND CHECKPOINTABLE**.
2. **CURRENT UI IS SUFFICIENTLY CONSERVATIVE**.
3. **KNOWN AND CONTAINED ENOUGH FOR BRANCH CHECKPOINT** — presence is still a release blocker.
4. **RESEARCH ARTIFACTS SUFFICIENTLY REPRODUCIBLE** within documented private-input/environment requirements.
5. **READY FOR FINAL PHYSICAL SMOKE THEN COMMIT** — commit still requires later authorization.
6. **DO NOT DEPLOY YET**.
7. **RUN FOUR-CASE FINAL PHYSICAL SMOKE** — the only next step.
