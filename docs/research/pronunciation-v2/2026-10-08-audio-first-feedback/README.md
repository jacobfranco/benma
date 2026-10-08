# Audio-first pronunciation evidence cards — October 8, 2026

Audio-first timing-unit cards are the preferred product direction after the six-take
desktop/phone-width review. They let a learner find the heard unit and replay its
own recording without interpreting a sentence-wide F0 domain. This is a prototype
finding, not a physical listening study or permission to deploy.

**Current pass: EXACT MINE + WITH-CONTEXT PLAYBACK REFINEMENT.**
**Implementation gate: pending physical listening; production unchanged.**
**Checkpoint: AUDIO-FIRST REPRESENTATION STILL NEEDS ONE SPECIFIC REFINEMENT.**

The prototype now has separate **Mine** (always exact, 0 ms) and **With context**
buttons on every accepted timing card. Only the secondary action responds to the
40/80 ms research selector. No product padding has been chosen. All 30 cards have
an A/B/C [physical listening sheet](listening-review.md); subjective findings remain
pending. The remaining issue is whether context helps listening and which single
window to use. See the current [context playback report](context-playback.md).

Production mobile and backend files were not changed in this pass. All preceding
uncommitted work remains intact. No commit, push, deployment, provider request,
new audio collection, model download, tracker/VAD evaluation, or acoustic rerun.

## Open the local prototype

From the repository root:

```sh
python benchmark/pronunciation_v2/audio_first_report.py
node benchmark/pronunciation_v2/test_audio_first.cjs
node benchmark/pronunciation_v2/audio_first_browser_check.cjs
```

Open [the generated viewer](../../../../services/api/var/audio-first-feedback/viewer.html)
in a browser. It is a standalone local file containing the six full canonical WAV
recordings and frozen analyses. It makes no network requests. No server or package
installation is required. The ignored local inputs must already exist; the build
fails if an audio hash or duration does not match. Chromium checks may need execution
outside the filesystem sandbox on this machine.

- [Product model and mobile capability audit](product-model.md)
- [Six-take review and all accepted bounds](six-take-review.md)
- [Playback architecture and padding](playback.md)
- [Validation and limitations](validation.md)
- [Machine-readable card review](replay.json)
- [Local screenshots](../../../../services/api/var/audio-first-feedback/figures/)

## Prior audio-first pass decisions (historical)

1. **AUDIO-FIRST TIMING-UNIT CARDS ARE BETTER DEFAULT** — design preference from
   this local comparison; mobile integration has not earned gate A.
2. **TIMING-BOUNDED USER PLAYBACK IS USEFUL AND HONEST** — exact canonical source,
   accepted spans, whole-recording fallback; audible usefulness still needs a listener.
3. **GROUPED CARDS PRESERVE EVIDENCE GRANULARITY WELL** — 雨伞 is one sentence
   selection, card and playback span. No 雨/伞 segment buttons.
4. **CARDS HANDLE UNCERTAIN PITCH WITHOUT FALSE PRECISION** — no chart inference,
   no grade, no shape on ineligible/grouped units, low confidence becomes “Unclear,”
   other displayed gestures explicitly remain tentative. This does not validate F0.
5. **ABSOLUTE GRAPH WORKS WELL AS OPTIONAL DETAIL** — complete saved selected
   samples, one fixed recording baseline, real seconds, preserved gaps. Raw remains
   diagnostic. No local centering, overflow policy or new acoustic selection.
6. **AUDIO-FIRST REPRESENTATION NEEDS ONE SPECIFIC REFINEMENT.**
7. **Separate exact “Mine” from a card-level “With context” replay.** Implemented
   in the current prototype; listening remains pending. Current seven decisions
   are in [context-playback.md](context-playback.md#seven-decisions).

The independent speech-presence blocker persists: falsely accepted non-speech and
hallucinated perceived text may still acquire timing and cards. This product
representation does not make deployment safe.
