# Immutable utterance evidence contract

**AUDIO EVIDENCE != SPEECH PRESENCE != PERCEIVED TEXT != REFERENCE PRONUNCIATION != INTENDED TARGET.**

`pronunciation/pitch_types.py` defines frozen Pydantic objects with extra fields forbidden. Frames and candidate collections are tuples of frozen objects; tracker parameters are canonical JSON text, not a mutable dictionary. No linguistic identity is a field or argument to extraction/building. This is application-level immutability plus the existing append-only evidence convention, not a new database trigger.

| Field | Exact meaning |
|---|---|
| `evidence_id` | SHA-256 of canonical sorted JSON containing schema version, canonical audio hash, algorithm/version/parameters, selection version, cadence/duration/baseline and the complete frame snapshot. Includes measurements; no account ID, run UUID, creation time, transcript, alignment, reference or target. |
| `audio_sha256` | Existing canonical `AudioAsset.sha256`, distinct from original-upload hash. Loading a saved typed track with a different supplied canonical hash fails. |
| `tracker_source`, `tracker_version`, `tracker_configuration_json` | Existing analyzer identity and complete parameter snapshot. Production Praat remains provisional; no tracker settings changed. |
| `selection_version` | Existing display-selection algorithm version. New typed snapshots preserve the selection actually used, rather than silently reapplying a later filter during replay. |
| `raw_provenance` | `native_tracker` when native `tracker_f0_hz` history exists; otherwise explicitly `legacy_energy_gated`. A legacy energy-gated value is never presented as recovered native truth. |
| cadence/duration | Median stored frame spacing; analyzer waveform duration (canonical asset duration fallback when omitted). Frame times remain original seconds, ordered, unique, nonnegative and within duration. |
| `raw_f0_hz` | Native Praat selected path **before Benma energy/quality/display exclusions**; not every candidate, and not ground-truth F0. Missing stays null. |
| `energy_gated_f0_hz` | Existing `f0_hz`, after the existing energy gate. |
| `analyzer_selected_f0_hz` | Existing analyzer quality/terminal selection, before display selection. |
| `selected_f0_hz` | Unsmoothed Hz at timestamps retained by the existing utterance display filter; null if excluded. No octave repair, interpolation, expected-tone adjustment or value replacement. |
| `periodicity`, candidates | Existing Praat strength and candidate frequency/strength; no invented calibrated confidence. |
| high-pass diagnostics | Existing `comparison_f0_hz` and `filter_disagreement_st` per frame; `energy_rms` also retained. The existing high-pass computation remains part of one analyzer call, not a new tracker or independently chosen learner contour. Other original diagnostics remain unchanged in `normalized_result.f0`. |
| `exclusion_reasons` | Existing display diagnostics including energy/quality/weak-periodicity/island/Hampel reasons. Raw Hz is retained alongside rejection. |
| `display_semitones`, baseline | Snapshot of existing within-run median smoothing and sentence normalization for presentation only. Selected Hz remains unsmoothed; classification never changes the raw frame. |

## Persistence and reuse

Fresh successful `AcousticRun.normalized_result` retains its original fields unchanged and adds `utterance_pitch_track`. The acoustic endpoint exposes a typed `utterance_pitch_track` as well as the legacy JSON. No migration, new service, model dependency, queue or network call was introduced.

Reuse is **account + utterance + algorithm + algorithm version + parameters**, under the existing utterance `NO KEY UPDATE` lock until persistence. This is not cross-account/global audio-hash deduplication. The evidence digest may agree for identical waveform/configuration/content in distinct runs, but their database run IDs remain distinct. Normal warmup, perceived analysis, target analysis and acoustic endpoint calls reuse one run. Existing explicit administrative `rerun_acoustics`/`reuse=False` controls can append a new run; “extract once” does not erase that deliberate provenance-preserving operation. Failed-run reuse behavior is unchanged.

Existing untyped runs are wrapped purely from their saved JSON and the canonical asset hash, without tracker execution or mutation of old records. That compatibility wrapper is derived at read time; it is not written over historical JSON. Its selection version/digest identifies the newly derived view. New typed runs deserialize their saved selection directly. Perceived analysis stores the track ID and projections; it does not duplicate the full track per character. Failed acoustics expose no successful track ID/projections.

## Invariants checked

Real production Praat service calls with 贵州, 鬼粥, arbitrary other text, changed/no target and empty metadata have identical complete typed snapshots and one extractor call. Distinct persisted perception records reuse the same `AcousticRun` and digest. Existing target-revision tests compare full typed tracks as well as raw JSON, references and displays. JSON round-trip, deep frozen fields, forbidden linguistic fields, deterministic digest, hash mismatch, source-index ownership and unchanged source arrays are tested. PostgreSQL integration exercises separate worker sessions and cross-route reuse.
