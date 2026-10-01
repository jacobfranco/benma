# Experiment 3 runner locked; test unopened

Final read-only verification: **VERIFIED_SEALED_UNOPENED**, all 18 speakers and
720 clips, with every selected source/file/original-PCM/mono16k-PCM hash matched.
No sealed-panel embeddings or predictions were computed. `evaluate` was not
invoked, and no `opened/` claim or test-result artifacts exist.

Runner lock timestamp: `2026-10-01T15:13:05.990560+00:00`.
Runner lock SHA-256: `12f6c27d186ce2698f1e6a4b2eefca938e26eae001db4d460e9ea6cf862d7e70`.
Git HEAD: `d8b28ff0b91dc103fb920f13be3c9a535a609a41` on `pronunciation-v2-research`.

See runner-spec.md for all metric/decision/bootstrap definitions and the exact
output contract; the machine-readable schema is
`benchmark/pronunciation_v2/experiment3-output-schema.json`, version
`experiment3-evaluation-v1`. The lock hashes code, tests, schema, specification,
validation receipt, preprocessing, environment and all frozen inputs. The external
SHA above is the trust anchor; the runner refuses changed bytes and lock overwrite.

Validation: 24 focused synthetic runner tests, 39 relevant model/control tests,
and 116 data/preflight tests passed (179 total). Changed Python files pass Ruff
check and Ruff format check. Git diff --check passes; untracked source/schema/spec
files also passed git diff --no-index --check. No raw audio is staged.

The broader pronunciation_v2 Ruff scan has an existing E501/format violation in
unchanged report.py:95. This is recorded separately in validation.json. No existing
research/model/protocol/seal or production files were edited. No commit or push.

Only in a future explicitly authorized opening pass, from /home/jacob/benma:

```sh
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/evaluate_experiment3.py evaluate --lock-sha256 12f6c27d186ce2698f1e6a4b2eefca938e26eae001db4d460e9ea6cf862d7e70
```

This command verifies all frozen inputs and the literal lock digest before model
access, then exclusively claims the opening. Any failure after that claim leaves
an incomplete run and prohibits automatic retries. Bootstrap uncertainty is
speaker-level descriptive uncertainty from 18 speakers, not population guarantees;
bootstrap and status subgroups cannot alter the nine-condition promising rule.
