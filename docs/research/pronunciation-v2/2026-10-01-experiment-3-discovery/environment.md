# Environment and reproducibility

- Python executable: services/api/.venv/bin/python
- Python: 3.12.13
- Platform: Linux-7.2.6-arch2-1-x86_64-with-glibc2.44
- pypinyin: 0.55.0; built-in dictionary only, no added dictionaries
- pytest: 9.1.1
- Ruff: ruff 0.16.1
- Decoder: ffmpeg version n9.0.1 Copyright (c) 2000-2026 the FFmpeg developers
- No dependencies installed or production environments changed.
- Raw audio and full downloaded documentation/indexes: ignored cache at
  benchmark/corpus/recordings/original/experiment-3-discovery/.
- Models/encoder/head modules are not imported by the data path. Fitted NPZ files
  are read as opaque bytes for SHA-256 verification only. No arrays are loaded.

The research data script is benchmark/pronunciation_v2/public_panel.py. Its
stages are index, prepare, acquire, history, history-mono16k, seal and verify.
Initial metadata responses and their exact URLs/hashes are recorded in
retrieval-receipts.jsonl. The 18 cached ZIP indexes bind published archive IDs,
sizes/checksums, exact member paths and HTTP Range receipts. All selected IDs and
input hashes are frozen in selection.json, created before any selected WAV fetch.

Completed acquisition was retained on continuation: 720 existing source hashes
were checked, with no selected WAV redownloads. The cached native-PCM historical
index was retained, checked, and extended with mono-16k hashes for the same 700
files. This extension implements the explicit normalized-PCM comparison requested
in the continuation. No source search was restarted.

No archive member is segmented: each selected distributed WAV remains unchanged.
Native PCM SHA-256 uses the established pilot convention (rate/channels prefix +
f32le PCM). evaluation_pcm_sha256 is the whole waveform decoded with exactly the
features.py load_waveform FFmpeg options: first audio stream, mono, 16 kHz,
f32le. That function/module is not imported; no encoder or checkpoint waveform
normalizer runs. Duration, original sample rate and channels are retained too.

Reproduce metadata and test invariants offline using:

```sh
PYTHONPATH=benchmark/pronunciation_v2 services/api/.venv/bin/python -m pytest benchmark/pronunciation_v2/test_public_panel.py benchmark/pronunciation_v2/test_pilot.py benchmark/pronunciation_v2/test_preflight.py benchmark/pronunciation_v2/test_evaluation_preflight.py -q
.venv/bin/ruff check benchmark/pronunciation_v2/public_panel.py benchmark/pronunciation_v2/test_public_panel.py
.venv/bin/ruff format --check benchmark/pronunciation_v2/public_panel.py benchmark/pronunciation_v2/test_public_panel.py
services/api/.venv/bin/python benchmark/pronunciation_v2/public_panel.py verify
```

The final verify command is read-only and available after sealing. It checks
bound artifact and code hashes, exact deterministic manifest bytes, composition,
frozen heads/protocol and local source hashes. It does not evaluate models.
To recreate an audit on another machine, retrieve the pinned public metadata,
verify receipt hashes, and use a separate output location; do not overwrite an
existing seal. The full original ZIP MD5 cannot be checked from partial ranges;
member CRC/size and locally computed WAV hashes are explicitly distinguished.

The source deposit publishes record ID 17506802 (DOI
10.5281/zenodo.17506802; concept ID 17506801), with publication date 2025-11-02 and
API modification time 2025-12-13T05:14:51.679245+00:00. No semantic version string
is supplied; revision_id=17506802 and the exact metadata hash bind the release.
The source paper carries a later 2026 publication date; it is independent
corroborating documentation, not silently treated as a new audio revision.
