> Historical five-tracker decision, superseded by [the final RMVPE decision](decision.md). Its next-pass recommendation was completed in this extension.

# Foundation decision

**D. NO TRACKER GOOD ENOUGH.** No production replacement, hybrid or foundation endorsement follows from this bakeoff. This is a decision about the five tested configurations on the frozen corpus, not a claim that every possible F0 estimator fails.

## Decision 1 — Current foundation

**PRAAT AC NOT ADEQUATE FOR BENMA.** It follows healthy/low voice cheaply and has excellent synthetic accuracy, but its raw whole-utterance evidence contains repeatable doubled onsets, the historical ~21.9-st 州 branch and sustained Google low/subharmonic paths. Those are upstream of character interpretation. Production filtering cannot select a missing correct path and further removes useful late rises and known-valid synthetic 70-Hz voice.

## Decision 2 — Best tracker

**NO CLEAR WINNER.** CREPE is the strongest candidate on the specific difficult Google/onset/late-rise trajectories, but a local win does not establish a dependable utterance foundation. With the same fixed cleanup, 289/1947 known-negative frames remain and only one of eleven lowest protected proxy frames survives, itself doubled relative to baseline. pYIN removes more background but discards clear voiced evidence and doubles the synthetic weak fundamental. Harvest over-voices heavily and has poor boundary repeatability. CC solves one branch without solving the broader failures.

The lowest real subset is small and baseline-selected; it is a reason to withhold a safety claim, not an independent gold error rate. CREPE/pYIN's known weak-fundamental doubling and real negative failures are separate, firmer counterexamples. Even free, instantaneous CREPE inference would not resolve those quality issues.

## Decision 3 — Foundation strategy

**NO SOLUTION YET.** A primary estimator plus its own native confidence is a valid simple design, and was evaluated explicitly. Neither CREPE nor pYIN's confidence view satisfies the combined real-speech, low-F0 and negative-control requirements here. No measured result supports per-character switching, five-way voting, or an additional complex ensemble. Production remains unchanged while one more bounded foundation experiment runs; this is not a KEEP CURRENT quality verdict.

## Decision 4 — Character-free architecture

**CURRENT RAW EXTRACTION ALREADY CHARACTER-FREE; ORCHESTRATION REFACTOR ONLY.** The existing acoustic service and analyzer accept audio and acoustic configuration without transcript, character, target, tone or alignment. Whole-file native evidence is reusable. The perceived-analysis entrypoint unnecessarily waits for successful text/transcript-aware presence before scheduling it; later alignment controls slicing and graph geometry. See [architecture.md](architecture.md) for exact service boundaries.

The later refactor should schedule acoustic extraction concurrently with ASR once canonical audio exists, persist its immutable evidence independently, then derive timing/gesture/reference views from that same track. Preserve raw native values, nullable confidence/voicing, source/version/configuration and waveform hash. Store any confidence/filter selection separately. Do not invent or remove linguistic conditioning in a raw estimator that already has none. This architectural recommendation is not implemented in this pass.

## Decision 5 — Graph root cause

**MIXED.** Raw estimation supplies wrong branches and missing evidence. Production filtering worsens some otherwise useful late rises and creates the synthetic-70-Hz rejection. Capture/source conditions and true prosodic differences also change the signal. Closest repeats reproduce some wrong shapes, so capture inconsistency alone cannot explain the problem. Conversely, unknown playback provenance prevents labeling all cross-capture disagreement as algorithm error. The specific [ablation](raw-results.md) separates these mechanisms.

## Decision 6 — Next product move

**EVALUATE ONE SPECIFIC REMAINING TRACKER — RMVPE.** Run one fixed, provenance-checked RMVPE implementation/checkpoint on these exact 49 files, preserving raw outputs and evaluating at most its own native-confidence gate. Reuse existing extraction artifacts, acoustic-only alignment, synthetic truth, negative controls and post-hoc windows. Do not gather recordings, tune per character, change downstream UI/abstention behavior or build an ensemble in that pass.

| Possible next pass | Decision | Why |
| --- | --- | --- |
| A. Bounded F0 foundation search: one RMVPE configuration | **Choose** | Tests the remaining blocker: correct vocal F0 under the observed background/low-register conditions |
| B. Rebuild filtering around raw Praat | Do not choose now | Could recover removed rises/70 Hz, but cannot by itself recover the correct branch where raw AC already chose the wrong one |
| C. Character-free utterance-track refactor | Do not choose now | Valuable scheduling/data-contract work, but the current raw service is already character-free and estimator trust is still unresolved |

The missing experiment is whether a model designed for **vocal pitch amid accompaniment/noise** preserves CREPE's useful speech trajectories while avoiding background tracking and retaining the lowest human evidence. RMVPE's paper motivates this hypothesis; it does not prove transfer from music to Benma speech. The authors provide a [vocal-pitch/noise study](https://arxiv.org/abs/2306.15412) and [official implementation](https://github.com/Dream-High/RMVPE). No RMVPE model or extra runtime was downloaded here. The next pass must pin code/weights, verify applicable weight licensing, and measure CPU cost rather than assume suitability from the paper.

RMVPE is the most directly motivated single remaining experiment, not an automatic winner:

| Existing candidate | What the RMVPE experiment would test | Remaining tradeoff |
| --- | --- | --- |
| CREPE | Whether vocal-specific training handles competing/background periodicity better while preserving the improved speech paths | Both are learned estimators; neither model confidence nor faster CPU inference can be assumed |
| pYIN | Whether a learned vocal estimate preserves weak voice that conservative pYIN rejects | Must still pass the weak-fundamental and lowest-register checks |
| WORLD Harvest | Whether vocal confidence separates the background for which the tested wrapper gives no confidence | Adds model/runtime complexity; may still hallucinate vocal evidence |
| Praat AC/CC | Whether a different representation avoids repeatable wrong branch choices | Gives up Praat's measured speed and adds checkpoint provenance/deployment work |

The paper uses log-mel input, a deep U-Net plus bidirectional GRU, and a 32.7–1975.5-Hz output range; 54–70 Hz is representable. It defines a maximum-activation voicing confidence with a .5 threshold. Its noise experiments favor RMVPE, but use music datasets and retrained comparators, not this stock CREPE/Benma setup. Its clean-music results are competitive rather than uniformly best. These facts support a test, not transfer accuracy or calibrated confidence. See the [method and experiments](https://arxiv.org/html/2306.15412v2).

The original paper's 20-ms input hop differs from this bakeoff's common 10-ms setting; the next adapter must preserve and report the selected checkpoint's native cadence rather than silently oversample it. Bidirectional recurrence and a deep network do not establish a streaming or low-latency deployment. No verified CPU benchmark here demonstrates that RMVPE will beat the current CREPE runtime. Its hypothesized practical advantage must be measured, and its behavior near silence and weak/irregular human voice remains unknown.

Its decision must prioritize the same five product properties: supported real F0, repeat consistency, octave/subharmonic robustness, low-register safety and rejection of known background. Report exact behavior on the Google path, repeated onsets/rises, historical 州, all prior 吧 windows, weak-fundamental synthetic, protected low samples and known negatives. A native-confidence gate must be evaluated jointly on voice and background. Reusing this corpus permits a direct answer without changing the evaluation target.

No second next pass is proposed. Filter rebuilding, tracker migration and orchestration implementation are not authorized by this research recommendation.
