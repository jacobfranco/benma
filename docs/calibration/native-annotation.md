# Native-listener annotation

Annotation remains two-stage and append-only.

Stage A plays audio without target or deliberate-error metadata. The listener records what they heard, whether it was understood first try, whether repetition would be requested, and confidence. `python -m benchmark annotate-blind ...` commits and hashes this response before any target reveal.

Stage B reveals the target, then records tone, initial, final, rhythm/prosody, severity, and whether the attempt remains understandable. `python -m benchmark annotate-reveal ...` references the Stage A hash. It cannot rewrite Stage A.

The preferred practical route is `python -m benchmark annotation-workbench`. It runs a tokenized
localhost browser UI, assigns opaque audio tokens so descriptive sample IDs cannot leak intent,
supports replay and local autosave/recovery, and exposes no provider data. A committed Stage A
unlocks Stage B. Annotation bundles are audio-free and create-only on import.

Use three independent native listeners for every critical pilot sample. Reports preserve every rating and display ratios such as 3/3, 2/3, 1/3, or 0/3; 2/3 is agreement evidence, not unquestionable truth. Listener IDs must represent independent people, not repeated sessions from one person.

Rater profiles store only pseudonym, native-Mandarin self-report, ordinary/trained role, and an
optional region/accent note. The report does not weight trained listeners more heavily by default.

The listener must not see requested-production or deliberate-error metadata before Stage A. Randomize order across correct, learner-error, native, nonsense, and low-quality controls. Record listening conditions rather than silently assuming them.
