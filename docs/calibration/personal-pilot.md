# Personal pronunciation pilot

This is a practical single-learner campaign, not a population study. Use the development-only
mobile Calibration Capture route to collect the 50-sample minimum: 10 tone errors, 10 initial
errors, 10 final errors, 10 native controls, and 10 negative controls. Add 12 learner-correct paired
attempts for the stronger tier. The checked-in 174-prompt corpus plan includes all 12 ordered T1–T4
confusions, paired segmental contrasts, sandhi, neutral tone, and quality controls.

Each mobile prompt records `pair_id`, requested production, and the explicit fact that requested
production is not ground truth. The normal Pronunciation result is not shown before a calibration
capture is finalized. Export each selected attempt explicitly; import its copied canonical WAV into
the planned manifest entry. Record pseudonymous `speaker_id`, device/microphone, session/pair ID,
and production recording-quality diagnostics.

Three native listeners then complete audio-only Stage A and target-revealed Stage B. Personal
calibration may use only samples with sufficient annotations and usable audio. If a threshold later
passes the held-out gate, its maximum scope is `PERSONAL` for that speaker and capture envelope.
It must not be used for another user or described as behavior of Mandarin learners generally.

Until then, raw/provider/acoustic observations remain useful, but no categorical tone judgment is
allowed. See [the executable campaign](manual-action-kit.md) and [gate definitions](calibration-gates.md).
