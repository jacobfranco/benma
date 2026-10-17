# AISHELL-3 playback QA — completed 2026-10-17

Round 2 was ingested from `/home/jacob/Downloads/aishell3-round2-decisions.json`:
**18/18 whole-unit PASS and 18/18 tone-bearing PASS**, with required listening,
reviewer, timestamps, packet and item hashes verified. The human playback gate is
satisfied. Round-1 and Round-2 exports remain unchanged in the immutable
[dataset release](data/generated/aishell3/releases/aishell3-nucleus-coda-context-v1-20261017/release.json).
The two original long-phone quarantines remain excluded; 787 accepted units include
729 numbered tones and 58 neutral tones. No further alignment remediation is required.
See the [training report](aishell3-training-report.md) for the released experiment.

The following handoff is archived provenance. Its pending status and next-pass
instructions describe the state before the completed review, not a current blocker.

# Archived playback handoff — Round 2

**Round 1 failed: 26 reviewed, 18 PASS, eight non-PASS. Training remains blocked.**

Open this exact file:

`/home/jacob/benma/research/perceptual-tone-model/data/generated/aishell3/round2-final/index.html`

[Open Round 2](data/generated/aishell3/round2-final/index.html).
The page has **18 items**: all eight former failures, eight representative PASS
controls, and two additional 20/30 ms tone-bearing outliers. The UI does not disclose
prior verdicts. All 26 original comparisons were generated and audited; the small
page is the human review subset. The draft `round2/` directory is retained as
intermediate evidence; review **round2-final/**.

1. Enter your name. For each item, play **CONTEXT**, **ORIGINAL TARGET**, and
   **TONE-BEARING TARGET**. Use **UTTERANCE** if ownership is unclear.
2. Answer **whole-unit integrity** independently: PASS / START ISSUE / END ISSUE /
   BOTH / WRONG UNIT.
3. Answer **tone-bearing integrity**: PASS / CLIPPED / CONTAMINATED / WRONG UNIT /
   TOO LITTLE MATERIAL. The candidate intentionally starts at the vowel or syllabic
   nucleus, excluding onset consonants and medial glides, and retains its aligned
   ending/coda. Check intended ownership, final completeness and sufficient material.
   Do not judge whether the speaker's tone is T1/T2/T3/T4.
4. Check the listening box. Add notes whenever either decision is non-PASS; describe
   which sound is missing or intruding and which edge is affected. A fuzzy whole-unit
   transition and a trustworthy tone-bearing span may receive different answers.
5. Click **EXPORT COMPLETE DECISIONS** and save as
   `/home/jacob/Downloads/aishell3-round2-decisions.json`.
   Draft export/import and packet-specific local storage support pausing.

If direct file playback is restricted, serve locally:

```sh
cd /home/jacob/benma
benchmark/pronunciation_v2/.venv/bin/python -m http.server 8765 --bind 127.0.0.1 \
  --directory research/perceptual-tone-model/data/generated/aishell3/round2-final
```

Then open [the local review page](http://127.0.0.1:8765/).

After review, the next continuation can ingest both answers without releasing:

```sh
cd /home/jacob/benma
benchmark/pronunciation_v2/.venv/bin/python \
  research/perceptual-tone-model/scripts/aishell3_round2.py ingest \
  --input /home/jacob/Downloads/aishell3-round2-decisions.json \
  --output research/perceptual-tone-model/data/generated/aishell3/round2-final/developer-decisions.jsonl
```

Ingestion preserves both original choices, notes, identity, timestamps, packet hash
and item hash. It verifies both media representations and does not train or release.
Do not pass this two-question export to the old Round-1 continuation command.

The next continuation must adjudicate tone-bearing failures, the 22 under-60 ms
flags, and control regressions. Explicitly quarantine genuine clipped finals,
unassignable material, wrong units or structural mismatches; do not quarantine
solely for fuzzy onsets. If tone-bearing ownership and controls pass, retain the
original read unit, use the context window for encoder input and the reviewed
candidate span for pooling. Recheck split/coverage after any quarantine, freeze the
accepted representation, then release and train in that subsequent pass.

See the [diagnosis and full dataset audit](aishell3-boundary-remediation-report.md).

---

The following is the archived Round-1 handoff, retained for provenance. Its pending
status and continuation instructions are historical, not the current next step.

# AISHELL-3 playback handoff — 26 targets

**The AISHELL-3 automatic data-quality gate passes, but human playback QA is still required before model training.**

Open:
`/home/jacob/benma/research/perceptual-tone-model/data/generated/aishell3/pilot/audit/review/index.html`

There are **26 targets and 78 WAV clips**: target, ±250 ms context, and full utterance
for each target. The packet has 5 T1, 5 T2, 6 T3, 5 T4 and 5 neutral examples. Each
shows stable ID, speaker/utterance, Hanzi/read unit, corpus pinyin/tone, neighbors,
boundaries, aligned phones, diagnostics, plots, RIFF notes and dictionary corrections.

From repository root, open the page directly:

```sh
xdg-open /home/jacob/benma/research/perceptual-tone-model/data/generated/aishell3/pilot/audit/review/index.html
```

If the browser restricts local playback/storage, serve only this packet locally:

```sh
cd /home/jacob/benma
benchmark/pronunciation_v2/.venv/bin/python -m http.server 8765 --bind 127.0.0.1 \
  --directory research/perceptual-tone-model/data/generated/aishell3/pilot/audit/review
```

Then open [the local review page](http://127.0.0.1:8765/).

1. Enter your name. For every target, use **PLAY CONTEXT** and **PLAY TARGET**.
   Use **PLAY UTTERANCE** if ownership is unclear. The native audio controls also work.
2. Choose **PASS**, **BOUNDARY EARLY**, **BOUNDARY LATE**, **WRONG UNIT**,
   **AUDIO/TRANSCRIPT MISMATCH**, or **OTHER**. Check the explicit listening box.
3. **PASS** means the intended corpus read unit occupies the target span, boundaries
   are plausible and there is no obvious transcript/audio mismatch. Do not judge
   whether its tone is textbook-perfect; the corpus provides the tone label.
   Mark clipped onsets/tails, included neighboring units or uncertainty as non-PASS
   and add notes. Every non-PASS blocks training until investigated.
4. Click **EXPORT COMPLETE DECISIONS** after all 26. Draft export/import and local
   browser storage support pausing; incomplete drafts cannot clear the gate.
   Save the completed export as
   `/home/jacob/Downloads/aishell3-playback-decisions.json` for the commands below.

Ingest the exported decisions, then continue the gate:

```sh
cd /home/jacob/benma
P=research/perceptual-tone-model
D="$P/data/generated/aishell3"
PY=benchmark/pronunciation_v2/.venv/bin/python

$PY "$P/scripts/aishell3_continue.py" ingest \
  --input /home/jacob/Downloads/aishell3-playback-decisions.json \
  --output "$D/continuation/playback-decisions.jsonl"

$PY "$P/scripts/aishell3_continue.py" continue \
  --reviews "$D/continuation/playback-decisions.jsonl" \
  --output "$D/released-after-playback"
```

The exact continuation command rechecks source/model hashes, saved alignments,
clip integrity, split isolation, class coverage and every packet decision. It
releases `released-after-playback/dataset.jsonl` (729 T1–T4 candidates) and
`gate.json` only if all checks pass. It **does not train models**. Resume the bounded
model-comparison stage using those released artifacts; the inherited package has
no complete native-tone training/selection runner yet. No pilot MFA rerun is needed.

Ingestion retains non-PASS findings, but continuation refuses release. Do not edit
old decisions or timing files to force a PASS. Investigate, quarantine or correct
identified issues with a new version and review any changed target. Existing
normalized decisions and release files are write-once; a revised review needs a
new output path. Never fill positive decisions from plots or automatic test output.

## Completed engineering checks

- Pilot: 200/200 automatically accepted; 80–550 ms, median 220 ms; no outliers.
- Combined: 189/189 utterances, 787/789 accepted, 16 speakers, 729 four-tone candidates.
  Two T1 units with 510/530 ms phones are quarantined under the original 500 ms rule.
- 78/78 clips match exact source PCM, decode and contain nonzero samples.
  All 26 plots and metadata references are present.
- Chromium loaded 78/78 audio controls and exercised playback/export validation.
  Synthetic test answers existed only in an isolated profile; no human decisions
  were written. Human playback remains **0/26**.
- All 26 plots were visually inspected in the earlier pilot pass. That found no
  systemic empty/duplicate spans but did not certify audible unit ownership.

| Targets | Prior visual observations | Playback focus |
| --- | --- | --- |
| 01–05 | Visible vowel energy; continuous `hun1 → yin1` transition in 02. | Intended unit and continuous boundaries. |
| 06–10 | Plausible initial/vowel spans; 08 has a weak final tail; 09 is corpus `wo2`. | Tail ownership and complete 我 span, without relabeling its tone. |
| 11–15 | No empty/duplicated spans; 14 `ye3` is 130 ms; 11 has a weak tail. | Short connected units and clipped endings. |
| 16–20 | Plausible frication/vowels; 20 `shi4` is 140 ms with a short vowel. | Complete read unit despite reduction. |
| 21–25 | Low-energy neutral `de5`; 23/24 are 130/110 ms. | Correct syllable and neighboring audio, not a neutral-tone judgment. |
| 26 | One 440 ms `哪儿 nar3` unit includes /ɻ/. | Complete rhotic read unit. |

See [the full report](aishell3-recovery-report.md) for split IDs, tone/T3 counts,
duration percentiles, source limitations and unavailable model metrics.
