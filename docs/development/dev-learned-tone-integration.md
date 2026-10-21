# Normal dev learned-tone integration

**READY FOR PHYSICAL PRODUCT TESTING.** Production defaults remain unchanged.
No training, tuning, calibration, research comparisons, commits, pushes or deployments.

## API failure triage

The wider suite finished with **642 passed, 67 skipped, 3 failed**. Each failure
reproduces with the pre-integration API source extracted from HEAD into
`/tmp/benma-before-integration`, selected using `PYTHONPATH`. The initial tracked
working tree was clean; existing untracked research work was preserved.

| Failure | Classification | Evidence |
|---|---|---|
| `test_final_acoustic_calibration.py::test_api_target_revision_preserves_acoustic_evidence[1]` | PRE_EXISTING | The existing `ma2` pinyin-correction request returns 422; the test then reads the missing `id`. Same failure on pre-integration source. |
| Same test, `[3]` | PRE_EXISTING | Same 422 and missing `id` on pre-integration source. |
| `test_pronunciation_laboratory.py::test_analysis_orchestrates_separate_evidence_and_is_idempotent` | PRE_EXISTING | Test expects `enable_experimental_tone_interpretation=False`; local `.env` enables that existing setting. Same mismatch on pre-integration source. |

No integration regression was found in these failures. No unrelated production
code or historical tests were changed to make them pass. Local baseline logs are
`/tmp/benma-api-baseline-tests.log` and `/tmp/benma-api-baseline-lab.log`; the wider
suite log is `/tmp/benma-api-tests.log`. The initial sandbox run stalled at worker
tests; the completed run used the same fixture suite outside that restriction.

## Integration and boundaries

Before integration: `useAudioCapture` → `submitSpeech` → upload/canonicalization
→ unknown-target ASR → persisted perception → speech-analysis endpoint →
conservative readings/surface expectations, Azure timing and Praat pitch →
persisted analysis → `PronunciationWorkspace` deterministic feedback/chart.
Prepared targets additionally invoked the laboratory assessment branch.

The integration point is `PerceivedSpeechAnalysisService.run`, immediately after
the existing full-resolution sentence pitch evidence is assembled. It consumes
the same validated Azure grapheme/one-character-word spans. It makes **no second
Azure request**. The new optional response is `data.dev_learned_tone`; absent
values are omitted from feature-off responses. The existing empty request remains
valid. A dev-only optional `dev_learned_target_id` selects an account-owned target
for downstream comparison; it never changes ASR, alignment reference, or audio.

Both explicit gates are required for prepared-target physical testing:

- API: `BENMA_ENABLE_DEV_LEARNED_TONE=true`, default false; production rejects it.
- Expo: `EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE=true`, also guarded by `__DEV__`.

The client preserves the attempt record but skips the laboratory assessment in
this mode. Free speech uses the same analysis endpoint without a target ID.
Feature-off paths retain existing behavior and response contents. Analysis cache
identity distinguishes learned mode and the selected target.

Refinement uses the first/last retained 10 ms F0 cells, clamped to the Azure span.
A retained-center gap **greater than 15 ms** with intervening energy below the
existing recording gate abstains. A pitch dropout without below-gate energy does
not trigger this rule. Missing validity metadata, missing timing, absent voiced
support, and the frozen 60 ms minimum pool fail closed. Context remains ±250 ms.
Tests compare only saved spans/guard outcomes with the frozen policy; no research
inference or timing experiments were repeated.

The inference boundary strictly accepts only `audio_reference`, `audio_sha256`,
`read_unit`, `pooling`, and `context`. Text, tones, grades and speaker fields are
rejected. Neutral scope is handled outside inference. Output includes T1–T4
probabilities, argmax, raw confidence, model/encoder identity, spans, continuity
evidence, frame counts and abstention reason. Absolute processing/cache paths are
excluded from the public result.

The process-global runtime lock covers lazy initialization and inference. One
worker retains its frozen encoder and expanded classifier across recordings.
Per-request scratch caches are removed; residency does not rely on repeated-audio
embedding hits. Initialization failure yields explicit abstention and preserves
the pitch chart. Runtime verification checks only required inference artifacts,
not the research MFA archive or corpus releases. MFA is neither executed nor
required to produce normal learned feedback. The gate rejects MFA alignment.
The unchanged explicit laboratory/research tooling remains separate.

Frozen identities:

- Chinese HuBERT: `TencentGameMate/chinese-hubert-base`, layer 9, revision
  `fce0375452b1dd6c080ac3248d423d4d037bc831`.
- Encoder weights SHA-256:
  `2fefccd26c2794a583b80f6f7210c721873cb7ebae2c1cde3baf9b27855e24d8`.
- Expanded balanced logistic classifier, C=0.1, SHA-256:
  `b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b`.
- Frozen runtime lock SHA-256:
  `cdae4b423e77dc3698cf75beee761f987b29ffd896fdd1c64c584b427233ca61`.

## Product behavior

Learned families are the experimental observed result. A resolved surface target
allows an unthresholded experimental match/difference; neither becomes a confirmed
error. Raw probability is explicitly not calibrated correctness. The current
rules leave 我/想/买 unresolved: families remain visible, with no correctness
correction. Neutral 个 receives no numbered-tone correction. Abstained cases are
insufficient evidence, never failures. A target/transcript mismatch explicitly
marks target mapping unresolved and withholds comparison.

The dev workspace keeps the existing `PitchPlot`, full and selected contours,
timed playback, lexical and surface expectations, schematic expected contour
when resolved, and acoustic evidence. It displays the same syllables with changed
tone marks, labels this **Heard-tone rendering**, and explicitly distinguishes it
from lexical ASR. It never substitutes Hanzi based on tone. Unknown numbered tones
render `[unclear]`; neutral readings remain contextual and clearly described.

Specific coaching requires sufficient existing pitch eligibility, supported
deterministic movement and a measured signed pitch change. Otherwise the learned
result remains visible with no invented diagnosis. Deterministic classification
is not the final family authority. **Dev evidence** exposes probabilities, spans,
continuity, F0 evidence, expected state, comparison, model identity and latency.
Existing client console timing covers upload, ASR and stop-to-chart rendering.

## Measured live product-path latency

Exactly two approved saved recordings went through real HTTP upload, configured
ASR, the existing Azure timing request and the normal dev analysis endpoint.
An isolated temporary SQLite database and audio directory were used; the smoke
server was stopped afterward. No MFA, research comparisons or new microphone
recording was involved. These measurements have not been repeated.

| Stage | Cold attempt | Warm attempt |
|---|---:|---:|
| Upload HTTP | 141 ms | 132 ms |
| ASR HTTP | 1,946 ms | 1,357 ms |
| Azure timing | 970 ms | 640 ms |
| Praat/F0 work | 73 ms | 63 ms |
| Local refinement/guard | 1.16 ms | 0.50 ms |
| Model setup | 3,654 ms | 0 ms |
| HuBERT/classifier inference | 261 ms | 187 ms |
| Experimental comparison | 0.17 ms | 0.13 ms |
| Pronunciation backend total | **4.93 s** | **0.84 s** |
| Upload through result, including ASR | **7.10 s** | **2.36 s** |

Stages overlap where the application runs timing and acoustics concurrently; do
not sum them as serial work. Warm runtime load count remained 1, with zero
embedding-cache hits. The 7.10 s cold total is not intended per-attempt latency:
the observed repeated-attempt path was 2.36 s including upload/ASR, with under
one second of pronunciation backend work. Actual microphone stop, device/network
conditions and UI rendering remain for physical testing. Model setup includes
imports, verification and loading, not encoder loading alone. See the retained
[structured smoke evidence](dev-learned-tone-smoke.json).

## Checks and freeze

- Focused final backend selection: **83 passed**, including prepared-target,
  free-speech, disabled responses, ownership/mapping, Azure reuse, no MFA,
  continuity, neutral, unresolved expectations, output schema, F0 coaching,
  inference allowlist and concurrent resident reuse.
- Previous full mobile run: **763 passed**, 47 suites across native/web.
- After the final small UI label change: **25 passed**, three relevant suites.
- API Ruff and mypy passed. Mobile TypeScript and lint passed.
- Wider API results and their three pre-existing failures are classified above.
- `git diff --check` passed; new source whitespace was also checked.
- **918 research snapshot files, 7,839 native artifacts and both frozen heads**
  verified unchanged. The three original recordings, fast-timing artifacts,
  prior outputs, deterministic family/grade functions, Praat and sandhi rules
  remain unchanged. The historical 2,102-file manifest has exactly nine intended
  product source/schema changes and 2,093 unchanged files; it was not rewritten.
  See [freeze verification](dev-learned-tone-verification.json).

## Normal physical testing

Use the existing dev database/schema and credentials in `services/api/.env`.
From the repository root, stop any API already occupying port 8000, then run:

```bash
BENMA_ENVIRONMENT=development \
BENMA_ENABLE_DEV_LEARNED_TONE=true \
BENMA_ALIGNMENT_PROVIDER=azure \
BENMA_ACOUSTIC_PROVIDER=praat \
benchmark/pronunciation_v2/.venv/bin/python services/api/scripts/dev_learned_server.py
```

This launcher uses the already-installed frozen inference environment and appends
the API environment's dependencies. It modifies neither environment, downloads
no model, and runs the normal API in one long-lived process. Existing Azure and
ASR credential configuration is reused. A restart pays the cold cost again.

In another terminal:

```bash
EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE=true \
EXPO_PUBLIC_BENMA_API_URL=http://YOUR_LAN_IP:8000 \
npm --prefix apps/mobile start -- --clear
```

Use `http://127.0.0.1:8000` for a browser on this machine; use the machine's LAN IP
for a physical phone. The existing browser CORS allowlist must contain the exact
Expo page origin for LAN web testing. Native requests do not need browser CORS.

1. Open normal Benma **Practice** (`/practice`) and use the existing dev account.
2. Select **Add target**, enter **我想买这个**, and choose **Prepare target**.
   Reference playback failure does not prevent recording.
3. Record and stop normally. Expect the first usable recording to pay cold setup.
4. Confirm **Experimental tone realization**, target reading and **Heard-tone
   rendering** appear. Tap syllables to inspect pitch, playback and comparison.
5. Open **Dev evidence**. Check Azure/refined spans, continuity, probabilities,
   expected state and `runtime.cold_start`. Record a second attempt without
   restarting the API: `cold_start` should be false and `load_count` remain 1.
6. Check that unresolved 我/想/买 and neutral 个 have no corrections; missing or
   interrupted evidence stays unclear. Assess perceived latency, chart behavior,
   playback, rendering, abstention and feedback usefulness. Free Practice can
   also be tested without a target; it labels its expectation as transcript-based.

No standalone research recorder is needed. The next work is physical product
testing; do not tune the model or policy from observations during this integration.

## Files changed

API: `config.py`, `schemas.py`, `api/routes.py`, `pronunciation/perceived.py`;
new `pronunciation/learned.py`, `learned_contracts.py`, `learned_runtime.py`,
`tests/test_dev_learned_tone.py`, `scripts/dev_learned_server.py`,
`scripts/dev_learned_smoke.py`.

Mobile: `src/api/client.ts`, `openapi.json`, `openapi.generated.ts`,
`src/speech/workflow.ts`, `PronunciationWorkspace.tsx`; new
`LearnedToneWorkspace.tsx`, `src/__tests__/learnedTone.test.ts` and
`learnedTone.web.test.ts`.

Documentation: this report, `dev-learned-tone-smoke.json`,
`dev-learned-tone-verification.json`. All pre-existing research files were retained.
