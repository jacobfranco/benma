# Acquisition and reproduction

Work from `/home/jacob/benma`, branch `pronunciation-v2-research`, starting commit `28766bd4608df3321ae55d798c301f269a638e27`. All tooling is isolated under `benchmark/pronunciation_v2/`. Raw audio and large response snapshots remain in `/tmp/benma-pronunciation-v2-pilot/`; nothing needs credentials. The existing API virtualenv supplies MIT-licensed pypinyin 0.55.0. System FFmpeg/ffprobe supplies decoding. No package, framework or model weights were installed.

## Commands

Historical metadata commands (already completed; **do not rerun for resume**):

```sh
python benchmark/pronunciation_v2/acquire.py inventory
services/api/.venv/bin/python benchmark/pronunciation_v2/pilot.py select
```

These commands cache successful API responses by URL SHA-256. The inventory exhausts continuation for six named direct categories, merges Commons page IDs, and obtains per-file imageinfo. `select` retrieves wikitext revisions for single-character candidates, reads current and legacy Lingua Libre speaker fields, resolves explicit license options, and writes `selected.jsonl`, `rejected.jsonl`, and `candidate-evidence.jsonl` to the cache. `--offline` requires complete cached metadata and performs no network access.

User-run resume, using only the existing approved metadata cache (no inventory/select step):

```sh
cd /home/jacob/benma
services/api/.venv/bin/python benchmark/pronunciation_v2/pilot.py download \
  --cache /tmp/benma-pronunciation-v2-pilot \
  --output docs/research/pronunciation-v2/2026-09-28-data-feasibility \
  --max-files 500 --max-bytes 1073741824 \
  --request-delay 60 --max-throttles 2
services/api/.venv/bin/python benchmark/pronunciation_v2/report.py \
  --cache /tmp/benma-pronunciation-v2-pilot \
  --output docs/research/pronunciation-v2/2026-09-28-data-feasibility
```

This command is for the user to run later/overnight, outside this agent pass. It preserves the 14 existing files and their budget usage. The caps cover the whole resumed acquisition, not 500 additional files. The final report command is offline.

The persistent `download-ledger.json` counts file transfers and received audio bytes across resumes, including incomplete transfers. Both limits apply; larger caps are rejected. Existing files are checked against the exact inventory SHA-1 and size, then SHA-256 hashed. Transfers use a `.part` file and atomic rename; truncated transfers are discarded. Do not run multiple downloaders against the same cache. Preserve the ledger with the audio directory; do not reset it to evade the cap.

Requests are serial and carry `BenmaPronunciationResearch/0.1 (bounded public corpus feasibility audit)`. The default/configured 60-second delay is deliberately conservative after repeated throttling even following a full 600-second cooldown; it offers **no rate guarantee**. Existing files are locally reverified and decoded without another network request or pacing sleep. HTTP 429/503 honors numeric or HTTP-date Retry-After in full, using exponential 60/120-second fallback when the header is absent. The second throttle event stops network acquisition across the **whole invocation**, even if different files triggered the events. A successful request does not reset that counter. No automatic restart loop is provided.

`network-cooldown.json` persists the server's earliest retry time, including when the throttle limit stops a run. A later invocation respects that cooldown. The manifest is rebuilt in deterministic selected order with atomic replacement; a network stop still includes later already-cached files. Ctrl-C during network acquisition preserves completed audio and reports partial progress. No alternate mirror, rotated identity or access-control workaround is used. Historical acquisition stopped after repeated HTTP 429s at 14 files; this final continuation used only offline regeneration. A null `acquisition_stopped_reason` in the regenerated summary means the **offline regeneration** completed, not that the historical network limitation disappeared. See [review.md](review.md).

Regenerate the downloaded manifest and count reports **without fetching more audio**:

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/pilot.py download --offline
services/api/.venv/bin/python benchmark/pronunciation_v2/report.py
```

`eligible-metadata.csv` records **all 516 metadata-eligible candidates** with `acquisition_status=metadata_eligible_not_a_local_audio_claim`. `pilot-manifest.jsonl` only contains successfully decoded, eligible files actually on disk (14 in this completed pass). Both manifests are written by atomic replacement. Selected-but-undownloaded candidates are not accepted pilot rows. Snapshot hashes in `inventory-summary.json` pin this run. A fresh live inventory can legitimately differ if Commons metadata/files change; the downloader refuses changed audio rather than silently substitute it.

`/tmp` is temporary. To preserve exact reproducibility, retain the cache, especially `api/`, `commons-metadata.jsonl`, `candidate-evidence.jsonl`, `selected.jsonl`, `rejected.jsonl`, `download-ledger.json`, `network-cooldown.json` if present, and `audio/`, outside Git. The curated manifest itself preserves asset URLs, source byte lengths/SHA-1s and local SHA-256s. For a lost cache, the exact downloaded pilot can be restored by copying `pilot-manifest.jsonl` to a new cache's `selected.jsonl`, then running `download --cache PATH`; source changes still fail checksum validation. This restores only those manifest rows, not the full historical discovery inventory.

## Labels and identity

- One Han character and one spoken citation syllable only. Explicit file pinyin must parse to T1–T4 and match a dictionary reading. That supplied pinyin may disambiguate a polyphone; dictionary membership alone never chooses a reading.
- Without explicit pinyin, pypinyin 0.55.0 `heteronym=True`, `neutral_tone_with_five=True` must return exactly one pronunciation. Even rare alternate readings cause rejection. No production dominant-reading override is used.
- Neutral, unmarked/uncertain tone, qualifier-dependent pronunciation and unresolved readings are excluded. Multi-character and connected-speech material stays in the inventory/rejection bucket; no forced alignment or surface-tone derivation is attempted.
- `label_confidence=high_lexical` does **not** assert independently observed surface tone. `observed_surface_tone` remains null. No v1 output, F0 contour, ASR confidence or expected-target feedback creates a label.
- Lingua Libre uses `speakerId` / legacy `locutorId`; recorder and uploader are separately preserved. Reviewed Shtooka source mappings distinguish speaker Wei Gao from recorder Nicolas Vion. Speaker evidence limitations remain explicit; metadata identity is not biometric verification.
- Native status remains NATIVE/NON_NATIVE/UNKNOWN, with UNKNOWN unless explicit Mandarin-specific evidence supports a change. Geographic descriptions and generic Chinese-language declarations do not establish native Mandarin.

## Audio and duplicates

Keep unchanged original bytes. Diagnostic decoding uses the original sample rate and channels, float32 PCM, with a 30-second decode safety bound. Report duration, sample rate, channel count, absolute peak, RMS, fraction of samples at `abs(x)>=0.999`, and fraction of 10-ms windows below RMS 0.001. The latter is a silence proxy, not a speech detector. Hard rejection is limited to decode/nonfinite errors, RMS below 0.00001 or peak below 0.0001, clipping proxy above 10%, or exact duplication. Do not call these checks a perceptual audit for singing, wrong language or overlapping speech. Metadata identifies the intended pronunciation material; no human listening certification is claimed.

Canonical identity is the Commons page ID, even for Lingua Libre-origin audio. Category overlaps are collapsed before counting. Inventory source SHA-1, downloaded SHA-256 and decoded PCM hash detect exact repeats. Normalized text plus speaker is retained for repetition review, not automatically discarded: different takes of the same syllable are not exact duplicates. No acoustic fingerprint model was used.

## Focused validation

```sh
services/api/.venv/bin/python -m unittest discover \
  -s benchmark/pronunciation_v2 -p 'test_*.py' -v
.venv/bin/ruff check benchmark/pronunciation_v2
```

Tests cover tone normalization, unmarked/neutral/ambiguous rejection, explicit polyphone disambiguation and conflicts, license allowlisting/dual-license handling, empty template values, uploader/speaker separation, no native inference from location, hard file/byte caps, partial-transfer accounting, resume caps, waveform diagnostics, exact deduplication, manifest schema, global throttle limits, persisted Retry-After cooldowns, preservation of cached files after network failure, and readiness gates. They use tiny synthetic temporary fixtures, never v1 truth or production state. The final run count is recorded in [review.md](review.md).
