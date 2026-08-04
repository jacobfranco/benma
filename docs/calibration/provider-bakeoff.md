# Same-audio provider bakeoff

Run all implemented known-target configurations on one immutable canonical 16 kHz mono PCM16 WAV:

```bash
cd services/api
uv run python scripts/provider_bakeoff.py \
  --sample /absolute/path/to/canonical.wav \
  --sample-id attempt-004 \
  --target 生活 --pinyin sheng1 huo2 \
  --surface-tones T1 T2 \
  --acoustic-json /absolute/path/to/acoustic.json \
  --alignment-json /absolute/path/to/alignment.json \
  --output ../../benchmark/corpus/provider-captures/attempt-004
```

The runner invokes Azure, Tencent sentence, Tencent pinyin, and iFlytek with the same bytes and
audio SHA-256 and sample ID. The optional immutable acoustic/alignment inputs produce the combined
developer inspection artifact while retaining their provenance. Missing credentials produce
`BLOCKED_EXTERNAL`; there is no replay fallback. A
successful row writes a sanitized `LIVE_CAPTURED_SANITIZED` capture with timestamp, Git commit,
provider/product, adapter/version, target, audio format/hash, request configuration, transport
timing, dated billing estimate when defensible, raw hash, and normalized evidence.

Import each successful capture only after mapping that exact audio to a recorded benchmark sample:

```bash
uv run python -m benchmark import-provider-capture \
  benchmark/corpus/provider-captures/attempt-004/tencent_sentence.live-sanitized.json \
  SAMPLE_ID
```

The importer rejects fixtures, target mismatches, and audio-hash mismatches. Provider mode remains
part of identity; Tencent sentence and pinyin distributions are never pooled. The resulting report
shows raw dimensions, score distributions, confusion matrices, abstentions, latency and cost—not a
single weighted winner.

The 2026-08-03 credential-free smoke produced four `BLOCKED_EXTERNAL` rows and no captures. This is
transport readiness evidence only; the input was a labeled synthetic audio-format fixture and does
not count as a live or calibration run.
