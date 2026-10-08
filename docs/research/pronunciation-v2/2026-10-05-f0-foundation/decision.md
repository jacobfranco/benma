# Final RMVPE foundation decision

**RMVPE does not earn migration. The final foundation winner is NO TRACKER GOOD ENOUGH. Stop tracker search.**

The exact frozen 49-file evaluation gives RMVPE meaningful advantages over Praat: old Google low/subharmonic recovery, avoided doubled onset/high 州 branch, more supported later rising evidence, 2.07 seconds of closest-repeat mutual voice with .096-st p90 disagreement, full known-70-Hz coverage, and CPU latency of .286 seconds for the 2.856-second clip. These gains are acknowledged, not dismissed by an aggregate score.

They do not meet joint product acceptance. Native RMVPE emits 374/1947 known-negative frames; the predeclared .05 confidence view still emits 326, with runs up to .90 seconds and salience up to .947. Every nearby threshold fails this safety requirement. The weak-fundamental synthetic contains 79 known doubled-frequency errors. Three of eleven protected lowest real samples are one octave above the baseline, although all eleven are retained and the other eight agree. The real proxy is small and biased; its uncertainty cannot erase the independently observed negative and synthetic failures.

## Decision 1 — RMVPE quality

**RMVPE DOES NOT CLEARLY IMPROVE THE FOUNDATION.** This means a trustworthy foundation across the full product criteria, not that every individual acoustic metric fails to improve. Real-speech harmonic tracking, closest-repeat coverage and speed improve; reliable voice attribution and octave safety remain unestablished. Gains do not qualify the foundation for migration.

## Decision 2 — RMVPE safety

**NOT SAFE ENOUGH.** Persistent high-confidence background, actual weak-fundamental doubling, and unresolved lowest-register disagreement remain. Native confidence is neither a calibrated learner-voice probability nor an octave-error detector. The single five-value sweep does not yield a robust safe region. No wider threshold search, bespoke acoustic stack, or production silence-guard change is proposed here.

## Decision 3 — Foundation winner

**NO TRACKER GOOD ENOUGH.** All six configurations fail the combined acceptance criteria. This is a bounded judgment on the evaluated configurations/corpus, not a universal statement about pitch estimation. Production remains unchanged; that is not an endorsement of Praat AC or its known destructive filtering.

## Decision 4 — Tracker search

**STOP TRACKER SEARCH — DESIGN AROUND EVIDENCE LIMITS.** This completes the final authorized estimator experiment. There is no seventh candidate, further neural tracker, or broad bakeoff recommendation. Do not substitute a perpetual estimator search for a product decision.

## Decision 5 — Next pass

**DESIGN TRUSTWORTHY PRODUCT BEHAVIOR AROUND PARTIAL/UNCERTAIN ACOUSTIC EVIDENCE.** Define how the product represents measured pitch, gaps, uncertain fundamentals and uncertain source ownership, and when it should decline a graph interpretation or judgment. Do not equate acoustic periodicity with the learner's voice or impose a lexical target to manufacture evidence. The next pass is design around measured limitations; no such product change is implemented here.

## Architecture retained

**CURRENT RAW EXTRACTION ALREADY CHARACTER-FREE; ORCHESTRATION REFACTOR ONLY.** Canonical audio must produce immutable utterance evidence independently of transcript, character, pinyin, expected tone or target. Preserve the acoustic truth boundary before optional ASR/timing projection, character/group views and gesture/reference comparison. Acoustic extraction may eventually be scheduled and persisted concurrently with ASR using the existing audio-only service. No per-character switching or tone-informed correction.

The graph root cause remains **MIXED**: raw estimator/path failure plus production-filter attrition and source/capture uncertainty. Raw Praat correctly estimates synthetic 70 Hz; current production filtering removes all 145 valid core samples. That ablation is reused, not rerun or fixed in this pass.

## Evidence and limits

[RMVPE report](rmvpe.md) contains provenance, all 26 required summary items, native semantics, all 49-file completion, low-F0/negative/synthetic results, timing and blinded-review limitations. [README](README.md) contains the final six-tracker comparison. [Validation](validation.md) records tests, hashes, viewer verification and tree preservation. The [previous five-tracker decision](five-tracker-decision.md) remains historical provenance only.

Real F0 truth is incomplete, low proxies favor the baseline, and the single reviewer knew the candidate families. Repeat differences can include actual prosody. These limits restrict superiority claims; the known-negative pitch and known synthetic octave errors are sufficient concrete blockers regardless. No production extraction, tone classification, learner verdict, UI or silence-guard change; no new recording, provider inference, commit, push or deployment.
