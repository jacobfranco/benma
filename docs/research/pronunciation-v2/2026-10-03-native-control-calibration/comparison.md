# Critical control comparison

| Control | Char | Timing quality | Raw F0 coverage | Retained coverage | Observed | Confidence | Comparison | Primary cause / limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DIRECT NATIVE | 要 | NA (no cached alignment) | NA | NA | NA | NA | uncertain | TIMING: unavailable |
| DIRECT NATIVE | 一 | NA (no cached alignment) | NA | NA | NA | NA | uncertain | TIMING: unavailable |
| DIRECT NATIVE | 苹 | NA (no cached alignment) | NA | NA | NA | NA | uncertain | TIMING: unavailable |
| PHONE TTS | 要 | Direct grapheme; mapped exactly | 38/39 (97.4%) | 31/39 (79.5%) | 4-like | moderate | uncertain | COMPARISON: unresolved reading |
| PHONE TTS | 一 | Direct grapheme; mapped exactly | 28/37 (75.7%) | 0/37 (0.0%) | unclear | low | uncertain | RAW_F0: low-frequency path; energy rejection |
| PHONE TTS | 苹 | Direct grapheme; mapped exactly | 42/69 (60.9%) | 0/69 (0.0%) | unclear | low | uncertain | RAW_F0: near quarter-frequency path |
| HUMAN | 要 | Direct grapheme; mapped exactly | 31/33 (93.9%) | 20/33 (60.6%) | 4-like | moderate | uncertain | COMPARISON: unresolved reading |
| HUMAN | 一 | Direct grapheme; mapped exactly | 16/21 (76.2%) | 15/21 (71.4%) | unclear | low | uncertain | NO_FAILURE: conservative abstention |
| HUMAN | 苹 | Direct grapheme; mapped exactly | 27/37 (73.0%) | 27/37 (73.0%) | 2-like | moderate | consistent | NO_FAILURE |
