# Blinded native-listener realized-tone validation, v1

Status: preparation only; no human responses or realized-tone labels have been collected.
The pooling-blocker audit remains **TWO_BLOCKERS**; acoustic pooling integration is
**NOT READY**, and head-only refitting is **NOT JUSTIFIED**. This experiment addresses
only independent perception of the seven sealed natural learner disagreements.
It does not address native RIGHT-edge concentration sensitivity.

## Fixed scope and separation

The exact seven disagreements and seven matched learner agreement controls are copied
from `pooling-blocker-audit-v1/selection.json`, SHA-256
`5c4ac1ad525691648044362cecba32495acace05165b9536819ffdef23aabe6e`.
Agreement controls are comparisons, never truth. The previous failed solo perceptual
annotation is not consumed. No F0, encoder or classifier inference, pooling changes,
new learner recordings, fitting, threshold tuning, ownership changes, product changes,
commit, push or deployment is part of this experiment.

The private key records recording/unit IDs, original recording provenance, canonical
WAV and PCM hashes, frozen owner/crop and context sample/time boundaries, exact output
clip hashes, native label provenance, concealed repeats and listener orders. It has
no learner labels or head predictions. Prediction access is isolated in a separate
private reference file consumed only by the final unblinding command.

## Native controls fixed before collection

Select 16 existing AISHELL-3 units from speakers assigned to the frozen **test** split:
12 positive controls (three each T1–T4), plus four challenge controls (one each T1–T4).
Exclude quarantined units, quality flags, unusual read units, erhua and adjacent T3
chains. Select unique utterances, preferring the least represented speaker, then
ascending SHA-256 of `[20261022, unit ID]`; visit positive passes 1–3 and then the
challenge pass, visiting T1–T4 in each pass. No classifier outputs enter selection.
Positive controls require frozen nucleus/coda duration 180–450 ms; challenges require
60–120 ms. These are stimulus-selection rules, not new acoustic/model thresholds.

Labels are the frozen corpus's actual pronunciation transcription, verified directly
against the hashed source transcript, not a Hanzi dictionary conversion or previous
solo annotation. Frozen release quality checks provide the ownership basis. These
longer clean positives are intended to be clearly recognizable; perceptual clarity
is a design assumption, not a newly established human finding. Report native control
confusion and item-level performance; if qualification fails broadly, investigate
control suitability in a separately preregistered follow-up, never relax bars or
replace controls using this study's answers. Shorter challenges measure robustness
and do **not** affect listener qualification. No new model is fit in this pass;
test speakers are held out from the existing multispeaker training split.

## Presentation and trial count

There are 30 distinct source items: 7 disagreement + 7 agreement + 16 native.
Each appears in two separately randomized views, for 60 primary trials:

- Crop: exact frozen `playback_read_unit` owned syllable, including onset.
- Context: exact frozen short local context, followed after 350 ms by the identical
  target crop. A playback timing bar highlights its interval; no lexical text is shown.

For learner units the crop boundaries must equal the sealed acoustic BASE owner.
Neither ownership nor source audio is changed. Existing context is approximately
250 ms on each side, clipped to source endpoints, and is preserved exactly.
Crops are unnormalized, unfiltered PCM16 WAV at source rate with metadata removed.
Every trial requests ONE categorical response for its target. Cross-view comparison
uses two trials, never two contradictory required answers on a single trial.
Crop/context trials are separated by at least eight positions. Listeners may remember
items; these paired observations are dependent and are never treated as extra raters.

Eight additional context trials are concealed repeats: three disagreements, three
agreement controls and two positive native controls, selected within each group by
ascending SHA-256 of `[20261022, "repeat", ID]`. Thus **68 trials per listener**.
Repeats contain exactly the same target and context WAV bytes but distinct opaque
trial IDs. No repeat markers, source names, labels, answers or correctness feedback
appear in the interface. Any same-source presentations, including the alternate
view, are at least eight positions apart (seven intervening trials).

Order uses Python's seeded `Random.shuffle`, rejection sampling of the fixed multiset,
with a listener seed derived from SHA-256 of `[20261022, listener ID]`. Each complete
12-trial block includes disagreement, agreement and native material. Tone and model
predictions are not inputs. Five orders and accepted shuffle-attempt counts are saved;
the sealed persisted orders are authoritative across Python versions.

## Responses and eligibility

The fixed choices are Tone 1, Tone 2, Tone 3, Tone 4, Neutral / light tone, and
Unclear / cannot tell. Neutral is distinct from unclear. Abstention is encouraged for
clipped, incomplete or unjudgeable sound. No confidence question is collected.
Playback must finish and a category must be selected before advancing. Replay is
unlimited; no speed cutoff is used. Timestamps/order/play counts are recorded.
There is no feedback or access to another participant's answers.

Recruit **five** independent adult native Mandarin listeners (L01–L05) who grew up
with Mandarin/Standard Chinese as a primary spoken language. Minimum is **three
qualified** listeners, not merely three submissions. Ask region of acquisition,
other Chinese variety at home, and current primary language descriptively and
optionally; bilingual/regional speakers are not excluded for that background.
Use an anonymous assigned ID, no name, email, birth date or contact details.
Listeners must not have seen study answers or participated previously. The coordinator
must confirm independence and eligibility and must not coach participants.

Assign the five IDs once. Seek all five; close collection after all respond or state
that they cannot participate. Seal every received final submission, including incomplete
ones, and record missing IDs. No outcome-dependent replacements or repeated attempts
at qualification. Fewer than three qualified listeners yields unresolved cases.
Any additional cohort, changed controls, changed bars or bug fixes after sealing
requires a new version, an explicit deviation record and new preregistration.

## Preregistered reliability gates

A listener qualifies only if eligibility is attested, the export passes the full
schema/order/packet/playback/timestamp checks, AND both gates pass:

1. At least **10/12 (83.33%)** correct first-designated context-view responses on
   positive native controls, with **at least 2/3 in every tone**. Unclear/neutral are
   incorrect for these numbered controls. Crop responses and challenge responses
   are descriptive and not part of this gate. A randomized repeat may occur earlier
   than its designated primary; scoring uses the preassigned primary occurrence.
2. At least **6/8 (75%)** exact matches between designated context primaries and
   concealed repeats. Neutral–neutral and unclear–unclear count as exact stability;
   neither supplies a numbered-tone answer or case evidence. No compatible-tone
   remapping is allowed. Report repeat consistency by source group as well.

The native bar allows two errors but prevents a listener from passing while missing
an entire tone; the repeat bar tolerates two unstable short clips. Small fixed counts
are reliability screens, not population-level guarantees. Confidence cannot replace
these gates. Qualification never uses learner expected tones or either head's output.

## Case evidence rules (ordered and exhaustive)

Use only qualified listeners, one primary answer per view per listener. All qualified
listeners remain in each denominator. If a learner item's concealed context repeat
conflicts with that listener's primary context answer, replace BOTH of that listener's
case-view votes by UNCLEAR for case adjudication; record the conflict. A stable vote
requires the same non-UNCLEAR category in crop and context. NEUTRAL can be a stable
category. Apply these rules to all 14 learners; only the seven disagreements are later
compared to heads.

- **STRONG:** at least five qualified listeners; the same category has paired stable
  support from at least 80% of all qualified listeners; each view has at most 20%
  UNCLEAR after the local-repeat rule. Emit that consensus category.
- **MODERATE:** at least three qualified listeners; paired stable support for one
  category is at least two-thirds; each view has at most one-third UNCLEAR. Emit
  that category. This means 2/3, 3/4 or 4/5 support, respectively.
- **AMBIGUOUS:** at least three qualified listeners and at least two non-UNCLEAR
  votes in each view, but neither rule above passes. Emit no consensus tone; retain
  distributions and cross-view discordance.
- **UNRESOLVED:** all other situations, including insufficient qualified listeners
  or insufficient judgeable votes. Emit no consensus tone.

STRONG/MODERATE describe evidence, not guaranteed phonetic truth. Repeats do not
increase sample size. No majority over unqualified listeners is used. Cases without
repeats have no local consistency observation; overall listener reliability still
applies and the private key identifies this limitation.

Report exact pairwise inter-rater agreement and nominal six-category Fleiss kappa
separately by view and source group, using primary trials only. Include category
counts and UNCLEAR rates, plus pairwise agreement excluding UNCLEAR pairs (report
its denominator). Kappa is undefined when fewer than two raters or expected agreement
is one. Report crop/context agreement and native per-item confusion for both all valid
submissions and the qualified subset. These are
descriptive diagnostics, not post-hoc qualification gates, hypothesis tests, or
independent-syllable population estimates. The seven learners span only three existing
recordings from one speaker; conclusions do not establish broader learner generality.

## Five phases and cryptographic checks

1. Collect only independent listener exports. Do not inspect head comparisons.
2. Close collection; copy exact raw JSON bytes into `responses/raw/` and hash them
   in `response-seal.json`, bound to the preregistration/package seal. Do not correct
   raw answers. Partial or invalid responses are retained and fail qualification.
3. Verify preregistration, code, protocol, schema, packets and raw hashes; qualify
   listeners with the fixed rules. No head predictions are opened.
4. Derive all case evidence and descriptive reliability results, write
   `perceptual-consensus.json`, and hash it in `consensus-seal.json` bound to the raw
   seal. No human result files are created by the package-building command.
5. Only the `unblind` command, after verifying both seals and reproducing consensus,
   opens the separately hashed frozen predictions. It emits the seven cases' evidence
   state, consensus tone, expanded/pilot predictions and match booleans. Ambiguous or
   unresolved cases have null matches, not errors. Neutral consensus can mismatch both.

These hashes enforce workflow integrity and detect accidental edits; they are not
cryptographic access control against a coordinator with filesystem access. The
coordinator already has the prior audit. Neither listeners nor the qualification
pipeline receive head outputs. Programmatic public-field allowlists, source-ID and
forbidden-field scans, exact public-folder inventories, and WAV chunk checks guard
both visible and hidden leakage. Public packets carry only opaque IDs, ordering,
view, playback timings and audio. Their packet hash is integrity metadata only.

## Future interpretation

If reliable evidence consistently favors one head, a head/distribution investigation
may be justified; retraining is not automatically justified. Mixed head support may
reflect perceptual ambiguity or multiple model issues. Many unresolved items mean
realization evidence remains insufficient and conservative treatment remains warranted.
If listeners cannot pass controls, their judgments must not select a model. The
separate native RIGHT-edge blocker and the absence of a justified generic weight cap
remain unchanged in every branch.

## Local operation and sharing

Generated root: `research/perceptual-tone-model/data/generated/native-listener-validation-v1/`.
This directory follows the repository's existing ignored generated-artifact policy.
Keep it locally backed up. Share **only one assigned `listener-packages/L01/` folder**
(or `share/L01.zip`) with the first listener. Never share the generated root, this protocol,
private key, preregistration, other participants' exports or the repository.

1. Confirm the adult/native/childhood-language/independence criteria. Assign L01;
   send that listener the entire three-file L01 folder. Do not mention controls,
   disagreements, source identities or model behavior.
2. Ask the listener to extract the folder, open `index.html` in a current desktop
   Chromium/Chrome/Edge browser, use headphones in a quiet place, and work alone.
   No server, installation, account or network is needed. Keep all three files together.
3. They confirm eligibility, optionally enter language background, press Start,
   complete playback, choose one of six options, and continue through 68 trials.
   They may replay. Before a break they download a partial JSON backup; the same
   browser/file location can resume from local storage. If storage is unavailable,
   finish in one session. Contact the coordinator if playback fails; do not guess.
4. At completion they press Download results JSON and return `L01-responses.json`
   through the agreed private channel. CSV is optional and not the analysis input.
   No upload or communication is performed by this software.
5. Place each final JSON export in `.../native-listener-validation-v1/incoming/`.
   Keep only the final submission per assigned ID in that intake directory; retain
   partial backups separately. No listener should use another listener's browser
   profile, ID or folder. Use L02–L05 for the other four listeners.

After collection is explicitly closed, from repository root:

```sh
export PYTHONPATH=research/perceptual-tone-model
python -m perceptual_tone.native_listener_analysis seal --collection-closed \
  --incoming research/perceptual-tone-model/data/generated/native-listener-validation-v1/incoming \
  --responses research/perceptual-tone-model/data/generated/native-listener-validation-v1/responses
python -m perceptual_tone.native_listener_analysis analyze \
  --responses research/perceptual-tone-model/data/generated/native-listener-validation-v1/responses
python -m perceptual_tone.native_listener_analysis unblind \
  --responses research/perceptual-tone-model/data/generated/native-listener-validation-v1/responses
```

The schema is `response-schema.json`; canonical exports contain version, anonymous
listener ID, packet hash, eligibility, optional background, start/completion timestamps,
and 68 `{trial_id, position, answer, answered_at, play_count}` records. Partial exports
have fewer rows and null completion and intentionally fail the complete-response schema.
CSV contains listener ID, packet hash and the five per-trial fields. Nothing in this
pass fabricates actual human submissions or runs these commands on human data.
