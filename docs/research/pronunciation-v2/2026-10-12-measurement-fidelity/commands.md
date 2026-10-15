# Validation and diagnostic commands

Run mobile commands in `apps/mobile`:

```sh
npm test -- --runTestsByPath src/__tests__/pitchMeasurement.test.ts src/__tests__/pitchShape.test.ts src/__tests__/toneLikeness.test.ts src/__tests__/pitchPlot.test.ts src/__tests__/sentenceToneGraph.test.ts src/__tests__/sentenceToneGraph.web.test.ts src/__tests__/learnerPitchGrade.test.ts src/__tests__/chunkPitchGrade.test.ts src/__tests__/toneFeedbackWorkspace.test.ts src/__tests__/toneFeedbackWorkspace.web.test.ts src/__tests__/pronunciationChunks.test.ts src/__tests__/pronunciationChunks.web.test.ts src/__tests__/pronunciationWorkspace.test.ts src/__tests__/pronunciationWorkspace.web.test.ts
npm run validate
CI=1 ./node_modules/.bin/expo export --platform web --output-dir /tmp/benma-measurement/web
```

Run backend/research commands in the repository root:

```sh
services/api/.venv/bin/python -m pytest services/api/tests/test_acoustic_frontend.py services/api/tests/test_canonical_audio.py services/api/tests/test_pitch_projection_contract.py services/api/tests/test_utterance_pitch.py services/api/tests/test_sentence_tone_graph.py services/api/tests/test_tone_evidence_region.py services/api/tests/test_pronunciation_chunks.py benchmark/pronunciation_v2/test_raw_tracker_audit.py benchmark/pronunciation_v2/test_gesture_readability.py benchmark/pronunciation_v2/test_product_feedback.py -q
services/api/.venv/bin/ruff check benchmark/pronunciation_v2/raw_tracker_audit.py benchmark/pronunciation_v2/test_raw_tracker_audit.py services/api/tests/test_pitch_projection_contract.py
node benchmark/pronunciation_v2/test_measurement_audit.cjs
node benchmark/pronunciation_v2/tone_feedback_audit.cjs
node benchmark/pronunciation_v2/test_tone_feedback.cjs
services/api/.venv/bin/python -m benchmark.pronunciation_v2.gesture_readability_audit
git diff --check
git diff --stat
git status --short
```

The two generator commands replay existing numeric evidence; their corpus and
report files were verified byte-identical to the starting tree. Source metadata
and diagnostic snapshots are local/private under `/tmp/benma-measurement/`.

Portable graph/ownership audit (no private audio or database needed):

```sh
node benchmark/pronunciation_v2/measurement_audit.cjs --summary services/api/tests/fixtures/pitch_measurement_430fcc2e.json
node benchmark/pronunciation_v2/measurement_audit.cjs services/api/tests/fixtures/pitch_measurement_430fcc2e.json > /tmp/benma-measurement/physical-full-pipeline.json
```

Raw diagnostic on the saved local snapshot, including all candidates and exact
local-replay path scores in the problematic interval:

```sh
services/api/.venv/bin/python -m benchmark.pronunciation_v2.raw_tracker_audit /tmp/benma-measurement/430fcc2e-1975-4773-b6be-fe1176349237.json --retrack --frames --start 1.2 --end 1.47 > /tmp/benma-measurement/mai-raw-audit.json
services/api/.venv/bin/python -m benchmark.pronunciation_v2.raw_tracker_audit /tmp/benma-measurement/????????-????-????-????-????????????.json services/api/var/gesture-readability/saved/874ae05a-bd67-4836-a53c-f78df5d129b0.json services/api/var/gesture-readability/saved/44075f37-3359-4efb-8f88-73e373470fdd.json services/api/var/gesture-readability/saved/aa12a29b-3080-4c20-9a3a-7ad9c5828ef1.json --retrack > /tmp/benma-measurement/raw-comparison.json
```

For a subsequent saved take, pass its diagnostic snapshot in place of that path.
The accepted shape is `{id, data, audio: {storage_key, sha256}, acoustic:
{algorithm, version, parameters, result}}`; the existing gesture-readability
`{analysis, audio, acoustic}` snapshot shape is also supported. Omit `--retrack`
to inspect saved candidates without reading audio. `--frames`, `--start` and
`--end` only select diagnostic output; they never change tracker inputs.

Serve the exported site on loopback, then run browser commands in another shell
from the repository root:

```sh
python -m http.server 8097 --bind 127.0.0.1 --directory /tmp/benma-measurement/web
```

```sh
BENMA_WEB_URL=http://127.0.0.1:8097 PLAYWRIGHT_MODULE=/home/jacob/filefruit/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright BENMA_BROWSER_OUTPUT=/tmp/benma-measurement/browser node apps/mobile/scripts/measurement-fidelity-browser.cjs
BENMA_WEB_URL=http://127.0.0.1:8097 PLAYWRIGHT_MODULE=/home/jacob/filefruit/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright BENMA_TONE_AUDIO=/home/jacob/benma/services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical/19d8333bc4e04ce4bf026e393ea1f3e7.wav BENMA_BROWSER_OUTPUT=/tmp/benma-measurement/tone-browser node apps/mobile/scripts/tone-feedback-browser.cjs
```

The browser tools mock all API responses, preserve source evidence, and test
320/390/412 px widths. The measurement replay verifies actual DOM line geometry;
the existing tone replay also checks exact saved playback and learner behavior.
No dependencies, browser binaries or services were installed or deployed.
