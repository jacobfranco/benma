# Candidate-aware octave ambiguity and graph robustness

**Latest continuation: [sustained high branch forensics](sustained-high-branch.md) — Outcome D, acoustically ambiguous; production unchanged; GRAPH QUALITY STILL BLOCKS CHECKPOINT.** Exact extraction confirms 25 raw high frames at 4.1002–4.3402 s, of which 24 reach selected evidence. Original/native audio reproduces the branch within .014 st; canonicalization is exonerated. Only 8/25 frames have credible octave-related half candidates, with four candidate-absent tail frames. The central spectrum/waveform instead has roughly 94 Hz harmonic spacing. No safe sustained-half-path rule emerged; all 617 protected samples survive the diagnostic, which also misses the target/historical failures. No parameter search or production implementation followed.

New review artifacts: [full frame table](sustained-high-frames.csv), [run-level/spectral replay](sustained-high-evidence.json), and [focused private viewer](../../../../services/api/var/octave-ambiguity/sustained-high/viewer.html) comparing the target with protected 54.610 Hz, including a private listening crop. **30 research tests pass**; the seven updated decisions and validation are in the new report. The one remaining issue is trustworthiness of this irregular terminal high run, especially its candidate-poor 4.3002–4.3402 tail. The earlier pass below is retained as history; its sustained-half-path premise did not survive the focused continuation.

## Previous candidate-aware pass

**Outcome B: physical artifacts explained, but the tested rule is not safe. Production is unchanged. GRAPH QUALITY STILL BLOCKS CHECKPOINT.**

The six requested Oct 6 canonical WAVs were replayed through the current production Praat analyzer. Candidate frequencies and strengths already exist in the acoustic result and immutable `UtterancePitchTrack`; no extraction extension is needed. A bounded, candidate-aware experiment removes seven frames from the first take but also rejects **protected 54.610 Hz evidence at 2.5124 s in `7787300e`**. All nine nearby parameter settings repeat that safety failure. Requiring complete-run candidate agreement preserves all 617 protected low-register samples, including all ten protected samples below 70 Hz, but removes only four physical frames and leaves the graph problem unresolved.

The dominant residual artifact family is octave/subharmonic path ambiguity. That is an acoustic inference from candidate structure, abrupt branch changes and harmonic support, **not a claim that every low or high excursion has known erroneous F0**. Several candidate-poor low islands remain unresolved. Real low dips and broad motion must not be discarded to make the graph attractive.

## Review artifacts

- [Physical forensics and exact cleanup order](physical-forensics.md): six file identities, all major suspicious events, candidate examples, old-rule failures and spectral limitations.
- [Candidate rule and falsification](candidate-rule.md): small context model, one-sided/gap handling, run variant, parameter neighborhood, low-F0 and historical safety.
- [Graph scale and before/after](graph-scale.md): selected counts, semitone ranges, domains, visual conclusions and rejected scale policy.
- [Validation and reproducibility](validation.md): commands, results, scope and known unrelated limitations.
- [Frame-level table, CSV](frame-forensics.csv) and [structured JSON](frame-forensics.json): **92 voiced-frame rows** across 12 physical review windows and the protected counterexample. These include stable neighbors and their timestamps, jumps, every stored candidate/strength, margins, octave ratios/errors, spectral peaks, exact old-rule diagnostics, Mine reachability and domain influence.
- [Replay and per-file islands](replay.json): all six takes, 49 frozen production controls, exact rejected indices, nine parameter settings, interval eligibility and observed results.
- [Local interactive viewer](../../../../services/api/var/octave-ambiguity/viewer.html): waveform, spectrogram, raw Praat selections, candidate branches, current/proposed selected evidence and independently scaled before/after Mine. Seven recordings, 13 event zooms, hoverable candidate strengths, frame/complete-run toggle; no external assets.
- [Local saved plots](../../../../services/api/var/octave-ambiguity/figures/): 20 PNGs, comprising six physical overviews, 12 physical zooms, and the protected control overview/zoom. These are private generated artifacts under ignored `var/`, not checkpoint inputs.

The viewer uses real acoustic time with Mine's full-resolution smoothed pitch values and actual Y-domain, before the <=.15 st display simplification. It does not invent character boundaries or impersonate an equal-cell mobile screenshot. Every selected point contributes to Mine's source geometry; client cell attribution still requires trusted timing. All six overviews and the decisive zooms were visually reviewed.

## Seven decisions

| Decision | Result | Evidence / limit |
| --- | --- | --- |
| 1 — physical root cause | **OCTAVE/SUBHARMONIC CANDIDATE PATH ERRORS ARE THE DOMINANT RESIDUAL GRAPH ARTIFACT** | Strong evidence for the branch-ambiguity family, especially the high branches; individual candidate-poor low islands remain unresolved. No reference tones used. |
| 2 — normalization | **INPUT NORMALIZATION NOT MATERIAL** | The supplied prior six-take check changed Praat by only ~0.003 st at most and retained the same energy-gated frames. Accepted as supplied; not rerun. |
| 3 — candidate rule | **NO SAFE GENERIC RULE** | No tested generic rule satisfies all acceptance criteria. The frame rule loses protected 54.610 Hz; complete-run agreement misses most physical artifacts. This is not a proof that every possible future rule must fail. |
| 4 — low-F0 / expressive safety | **REGRESSION REMAINS** | In the rejected frame-rule experiment, not in production. Smooth large sweeps and healthy controls survive; the protected low-F0 false rejection vetoes integration. |
| 5 — graph scale | **GRAPH SCALE STILL UNSOLVED** | Candidate rejection does not shrink the problematic domains. No truth-preserving independent scale fix is justified by the remaining evidence. |
| 6 — graph quality | **GRAPH QUALITY STILL BLOCKS CHECKPOINT** | Takes 1, 2, 3 and 6 retain conspicuous unresolved branches; takes 4 and 5 remain coherent. |
| 7 — next step | **FIX ONE SPECIFIC REMAINING GRAPH ISSUE** | Address the sustained 353–434 Hz branch at 4.1002–4.3402 s in `8d252264`, using the existing evidence and the protected 54.610 Hz counterexample as a mandatory safety control. |

**One next step:** fix that sustained high-branch reliability issue on the frozen evidence. Four-case physical re-smoke is not ready yet.

## Contract and change scope

No backend or mobile production file changed in this pass. No third production rejection rule, new reason taxonomy, schema/version change, new public payload, graph-domain heuristic, linguistic dependency, grading behavior or frequency repair was introduced. The research-only reason is `octave_candidate_ambiguous`; experimental track copies are explicitly versioned `REJECTED-EXPERIMENT-not-production`. Original tracker frequencies, candidates, timestamps, energy-gated values and analyzer selections are byte/value-preserved in replay.

More Detail and Raw keep their current semantics. Eligibility and observed geometry continue to consume production selected support. Counterfactual removals preserve raw support in the denominator, all missing intervals and original jumps; no formerly non-sufficient historical interval becomes sufficient. A focused test also proves a material removal remains incomplete and suppresses observation, while grouped projection retains exact source indices.

Added source: `benchmark/pronunciation_v2/octave_ambiguity.py`, `octave_ambiguity_report.py`, `octave_ambiguity_viewer.html`, `octave_ambiguity_browser_check.cjs`, and `test_octave_ambiguity.py`. Added documentation/data: this directory. The development current-state document was not rewritten because the requested production-change condition was not met; this report supersedes the earlier graph readiness assessment for this pass, without rewriting research history.

Validation: **233 targeted backend tests, 69 connected-speech tests and 16 research checks passed**; 49 saved production controls replayed; viewer/browser checks, API/research Ruff, touched formatting, source mypy and diff checks passed. Research checks explicitly record the failed safety requirement; their green status is not product acceptance. See [validation](validation.md) for limits and exact commands.

The existing uncommitted working tree and branch were preserved. No commit, push, deployment, provider/API request, model download, new recording, alternative tracker/VAD evaluation, volume-normalization retest, or speech-presence/reference-tone research occurred.
