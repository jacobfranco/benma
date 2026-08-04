# Pronunciation calibration gates

The report defaults to real audio only. Replay, constructed fixtures, documentation examples, and
TTS are excluded from every headline count and metric.

## Collection gates

Minimum existing pilot:

- 30 human-reviewed deliberate learner errors: at least 10 tone, 10 initial, and 10 final;
- 10 native controls;
- 10 negative controls;
- three independent self-reported native Mandarin listeners for every critical sample.

Stronger paired pilot adds at least 12 learner-correct controls, preferably paired by
speaker/target/device/session with intentional errors. Requested production remains an instruction,
not ground truth. Audio-quality-invalid samples are excluded except from the explicitly separate
negative/audio-quality analysis.

## Categorical tone gate

All of these are required:

- at least 20 human-supported tone-error syllables;
- at least 20 human-supported acceptable-tone syllables;
- three native listeners on critical samples, with individual votes preserved;
- an immutable deterministic calibration/held-out split;
- threshold selection using the calibration partition only;
- explicit held-out review with acceptable tone-detection FAR, diagnosis FAR, and learner/native
  FRR by important confusion/surface-tone class;
- a recorded promotion decision, maturity, scope, speaker/population identity, interpreter/provider
  versions, and rollback flag.

No numeric target is silently invented for “acceptable.” A future promotion ADR must set the risk
limits before viewing held-out results. The threshold explorer reports counts, fractions, Wilson
95% intervals, sensitivity, specificity, balanced accuracy, precision, recall, and abstentions. It
does not select a winner.

Current state: every real count is zero, no split contains real data, no threshold was explored,
selected, held-out validated, or promoted, and categorical judgment is disabled.
