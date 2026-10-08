# Five thresholds; no acceptable operating region

The unmodified default was recorded and inspected first. Then exactly five thresholds centered on 0.50 were evaluated from the **same saved probabilities**. Minimum speech stayed 250 ms, minimum silence 100 ms, padding 30 ms, and maximum speech infinite. Exit threshold followed the official `max(threshold - 0.15, 0.01)` formula. No additional threshold or duration policy was evaluated.

| Start threshold | Exit threshold | Negatives rejected /10 | Accidental silence | Positives retained /37 | Short /6 | Quiet RMS /12 | Quiet gain /1 | Low-F0 /5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.30 | 0.15 | 9 | Accept | 34 | 3 | 12 | 1 | 5 |
| 0.40 | 0.25 | 9 | Accept | 33 | 2 | 12 | 1 | 5 |
| **0.50** | **0.35** | **9** | **Accept** | **33** | **2** | **12** | **1** | **5** |
| 0.60 | 0.45 | 9 | Accept | 32 | 1 | 12 | 1 | 4 |
| 0.70 | 0.55 | 9 | Accept | 31 | 0 | 12 | 1 | 3 |

The unresolved `277e9941` is rejected at all five settings, with peak 0.048610 and zero detected speech. It remains outside both scored denominators.

| Threshold | Accidental region (seconds, including pad) | Duration |
| --- | --- | --- |
| 0.30 | 1.026–2.942 | 1.916 s |
| 0.40 | 1.026–2.910 | 1.884 s |
| 0.50 | 1.026–2.878 | 1.852 s |
| 0.60 | 1.026–2.878 | 1.852 s |
| 0.70 | 1.058–2.846 | 1.788 s |

**No tested threshold rejects the critical false accept.** Its 0.997681 peak and long high-probability run are not a near-threshold anomaly. No extreme threshold was tested to force rejection.

The 0.40–0.50 pair has identical accept/reject decisions, but those decisions include the blocker and four short false rejects. The best raw retention, 34/37 at 0.30, still loses three human excerpts and accepts the blocker. Raising the threshold to 0.60/0.70 introduces low-F0 excerpt failures as detected onset moves later. There is no safe robust operating region to recommend, and no “best threshold” is promoted.

## Why no minimum-duration sweep

The original authorization permitted duration tuning only if the threshold-only sweep nearly solved the corpus. It did not. The critical event is approximately **1.852 s including 60 ms of segmentation padding**, corresponding to a **1.792 s unpadded default region**. Raising the minimum above that unpadded duration to remove this event would be incompatible with valid 110–300 ms speech. The distinction between padded and unpadded duration does not change the conclusion.

Lowering the 250 ms minimum could address some short-speech losses, but cannot reject an already accepted long, high-confidence negative. Since a hard acceptance criterion already fails throughout the sweep, no duration search is justified. No minimum duration is selected for Benma.

## Why no acoustic combination

The optional combination was conditional on a strong Silero result with a small understandable edge case. The exact trust blocker has near-one scores over sustained changing acoustic structure. It is not a small threshold or timing edge case. The preceding five-policy acoustic pass also failed to reject it safely. None of those policies was reopened, and no Silero-plus-acoustics rule was evaluated.

[Complete per-file threshold results](threshold-results.json) preserve every decision and speech interval. The saved default result hash is embedded in that file so the sequence of analysis is reviewable.
