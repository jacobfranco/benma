# Projections and the truth boundary

**CHARACTER/WORD GRAPHS ARE PROJECTIONS OF ONE IMMUTABLE UTTERANCE ACOUSTIC TRACK.**

`project_pitch(track, start, end, timing_source, timing_evidence_id)` returns a frozen `PitchRegionProjection` containing the source track digest, interval, timing provenance and tuple of source frame indices. Ownership is exactly **[start,end)**. A frame on a shared boundary belongs only to the next region; the last available frame before the final end remains owned. No new timestamp or acoustic value is created. Index + digest resolves every projected sample to the immutable source frame.

The projection itself does not carry spelling, pinyin or tone. Its enclosing perceived syllable or word group supplies linguistic identity separately. Missing, invalid, out-of-waveform or synthetic timing yields an empty untimed projection. Production integration supplies intervals only after existing alignment validation; the low-level operation does not claim that an arbitrary string is proof of trusted timing. Punctuation supplies source-text offsets but no Han pitch cell.

Perceived analysis and the target laboratory derive displays from the saved track; the existing classifier can consume its saved full-resolution selected display rather than refilter the waveform per character. It still receives original saved raw diagnostics for existing acoustic core checks. There is no new F0 extraction in either projection or classification.

For 雨伞 with only Azure word timing, one `PerceivedTimingGroup` owns one whole-word projection. Both characters remain visible; their individual start/end and projections remain absent. Anonymous syllable intervals are not assigned by order or divided equally. The group receives completeness diagnostics but no per-character observation or comparison. Old responses can still recover grouped timing from saved timing payloads, without claiming a projection they never stored.

`SentencePitchEvidence.track_evidence_id` links the graph to this source. Raw frames now include `source_frame_index` and exclusion reasons; selected Hz uses final selection semantics. Mine still uses existing smoothing/simplification with real interval boundaries; More Detail retains unsmoothed selected measurements over elapsed time. Raw retains native Hz, rejected timestamps and the original source index. Gating changes an observation, never these fragments.

Tests cover shared boundaries, exact character spans, repeated deterministic projection, final-frame ownership, punctuation, untimed cells, source mismatch, grouped whole-word spans and no invented internal boundaries. The saved replay also records each projection's digest and full source-index tuple in `replay.json`.
