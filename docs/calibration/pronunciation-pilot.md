# Pronunciation calibration pilot

The minimum pilot is 50 real recordings: 10 deliberate tone errors, 10 deliberate initial errors,
10 deliberate final errors, 10 native controls, and 10 nonsense/poor/low-confidence controls.
Synthetic and replay assets never count. The stronger paired tier adds at least 12 learner-correct
controls from the same speaker/target/device/session where practical.

The development-only mobile route `/calibration` presents 50 capture prompts and supports record, replay, retry, and save. A saved capture remains production evidence. It does not enter `benchmark/` automatically.

Explicit export is:

```bash
cd services/api
uv run python scripts/export_pronunciation_attempt.py ATTEMPT_UUID \
  --output ../../benchmark/corpus/imports \
  --requested-production wrong_tone \
  --confirm-research-export
```

Then choose the planned benchmark sample and use `python -m benchmark import-audio SAMPLE_ID EXPORTED/canonical.wav`. Review and copy metadata deliberately. Public-user collection will require consent, retention, withdrawal, and provider-data-flow design; the personal-development confirmation flag is not that design.

The screen stores `pair_id` and `requested_production_is_ground_truth=false`. The 174-entry plan
covers all 12 ordered T1–T4 substitutions, paired initial/final contrasts, 10 native controls, and
10 negative controls. Every entry remains `planned` until audio exists.

`python -m benchmark pronunciation-calibration` writes real-only JSON and Markdown. It preserves individual annotations, reports confusion and detection separately from diagnosis, lists score distributions without choosing a threshold, and excludes replay/synthetic data.

Preliminary gates are 30 deliberate learner errors, 10 native controls, 10 negative controls, and three independent listeners per critical sample. Passing the small pilot permits preliminary behavior only; it does not establish general accuracy.

For a usable browser workflow run `python -m benchmark annotation-workbench`; Stage A receives an
opaque audio token and Stage B is unavailable until the hashed blind response commits. See
`manual-action-kit.md` for remote access and export/import.

Current state: **CALIBRATION BLOCKED: 0/50 real pilot recordings.** Categorical pronunciation calibration remains incomplete.
