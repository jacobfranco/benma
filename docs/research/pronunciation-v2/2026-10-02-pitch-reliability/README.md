# Bounded connected-speech pitch reliability audit — 2026-10-02

> **Superseded by the [Trust Pass](trust-pass.md).** The second real silence case exposed a periodic-background false accept. Current behavior adds post-ASR acoustic corroboration, removes default reference-tone labels, and keeps the primary pitch tracker. The content below records the earlier pass.

**KEEP CURRENT extraction and selection.** No alternative demonstrated a repeatable,
production-safe overall improvement. Cross-correlation often increases both coverage
and fragmentation. The lower floor fails to recover either missing 吧 window. No new
pitch repair, adaptive range, jump rejection or display interpolation is enabled.

**The reproduced no-speech hallucination is blocked.** The audio-only presence guard
rejects the exact saved recording and accepts the other nine identified recordings,
18 attenuated variants and nine provider-timed single-character excerpts. This is a
bounded regression result, not a validated general-purpose VAD accuracy claim.

The learner graph now gives every perceived Han character an equal-width cell, including
untimed 雨/伞. Measured gestures sit above 34 px characters and compact reference labels.
Technical explanation and evidence availability move behind tap / More detail / Raw.
See [product behavior](../../../development/tone-graph-v2.md), [method](method.md),
[results and exact recording inventory](results.md), and [validation](validation.md).

Local-only artifacts: `/tmp/benma-pitch-reliability/`. `recordings.json` holds the
read-only database provenance; `audit.json`, `attrition.csv`, `tracker-metrics.csv`,
`report.html` and `gate-replay.json` hold the diagnostic results. `audit.py`,
`inventory.py`, `gate_replay.py` and the frozen `method.txt` reproduce the procedure
with the existing local audio. HTML contains waveform, periodicity, current raw/selected
F0 and all candidate traces. **Final proposed production is the unchanged selected
production trace.** Audio remains in ignored existing storage; no audio is added to Git.
No provider calls, model downloads, training, commits, pushes or deployment.
