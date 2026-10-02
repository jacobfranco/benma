# Connected-speech diagnostic schema

This document describes the original v1 contract. See [the v2 architecture and compatibility notes](../2026-10-01-connected-speech-mapping/architecture-update.md) for current replay output; the [archived v1 machine schema](../../../../benchmark/pronunciation_v2/connected-speech-schema-v1.json) preserves the original definition.

Canonical executable definition: [connected_schema.py](../../../../benchmark/pronunciation_v2/connected_schema.py). Published machine contract: [connected-speech-schema.json](../../../../benchmark/pronunciation_v2/connected-speech-schema.json), generated using Pydantic `Record.model_json_schema()`; tests require exact equality and validate record round trips. Unknown structured fields are rejected; provider payloads/acoustic frame dictionaries deliberately allow their native fields. Null means unavailable, not zero, incorrect, or unvoiced.

## Fields

| Field | Meaning |
| --- | --- |
| `schema_version`, `analysis_version` | `connected-speech-v1`, `connected-probe-v1` |
| `recording_id`, `mode`, `provider`, `language` | run/fixture identity, free/practice metadata, perception product, zh-CN |
| `audio` | original path/hash, canonical hash, duration in ms, recorded/synthetic provenance; fixture hashes/paths absent |
| `perception` | exact raw and identity-normalized transcript, transcript digest, normalized provider evidence/uncertainty, complete raw response, fixed request configuration, evidence status |
| `intended_text` | optional exact target; never input to recognition, alignment, acoustic measurement |
| `alignment` | exact perceived reference, source, provenance, raw provider response, issue reasons, whole-word regions |
| `alignment.words[]` | exact perceived text/character offsets, nullable interval, source, mapped/unresolved syllable status, raw normalized provider-word evidence |
| `acoustics` | full production result: raw/selected F0, candidates, RMS, voicing/quality, normalization, recording quality, display contour and analyzer version/parameters |
| `units[]` | one candidate syllable per supported Han character, even when untimed; not a claim every written character is one acoustic syllable |
| `text_comparison[]` | full match/substitution/insertion/deletion trace, including deletions with no perceived unit; exact text offsets, uniqueness and optional intended expectations |
| `target_relative_assessment` | null in v1; intended-target provider assessment deliberately not invoked |
| `configuration` | context widths, reading/surface/mapping versions, text edit and transparent quality policies |
| `limitations` | evidence and validation scope |

Each unit has `unit_id`, `perceived_text`, exact character offsets, `granularity`, nullable `timing` (`start_ms`, `end_ms`, `duration_ms`), `timing_source` and optional actual provider `timing_confidence`. Intervals must be positive, ordered, nonoverlapping, and within audio. Start/end values are never filled by equal partition. Whole-word timing does not populate unit timing.

`reading` preserves pinyin, lexical tone, resolution source/status, alternatives and unresolved ambiguity. Neutral tone is **0**, never T1–T4; production numeric-pinyin convention 5 is converted by the existing reader. Resolved phrase readings may still retain dictionary alternatives; `ambiguous` means unresolved selection, not merely multiple historical options.

`pitch` contains full in-region frame dictionaries and a selected-F0 contour (explicit nulls retained), frame counts, raw voiced proportion, active voiced proportion when an energy gate exists, raw F0 missing proportion, and source. Slices use `[start, end)` to avoid duplicating a boundary frame. The full-utterance `acoustics.display_contour` separately retains the existing production filtered graph. Neither contour uses expected tone. Praat's `voicing_probability` is a periodicity/strength proxy, not a calibrated probability of pronunciation correctness.

`phones[]` can contain mapped SAPI reference labels, their intervals, source, nullable score and mandatory reference-label semantics. This version keeps scores in `alignment.raw_response`; it does not promote them to independent segmental observations. `observed_tone_model` is explicitly null. Future model integration requires a schema version that preserves checkpoint/configuration, all four probabilities and a mandatory experimental/out-of-domain connected-crop flag; v1 cannot silently accept an unlabeled model output.

`context` links previous/next candidate units and provides an audio window. Default pre/post context is **150 ms**, clipped to audio. It is configurable, not tuned. Untimed units have no invented window. Frames anywhere in the context window can be retrieved from full-utterance `acoustics.f0`; no context crop files are generated.

`target_comparison` refers to the deterministic edit at the perceived offset. `expectation` contains intended lexical reading, contextual tone, rule and version only for a unique minimum-edit path. Punctuation/whitespace are ignored **only** for text comparison; original transcripts/targets and source offsets stay exact. Other alphanumeric characters participate in comparison but have no Mandarin pronunciation unit. Repeated-text ties retain a deterministic path (diagonal, deletion, insertion precedence) labeled ambiguous; per-unit expected correspondence is withheld. This is text correspondence, not acoustic alignment.

## Quality and abstention

No aggregate correctness/confidence scalar is introduced. Sorted deterministic flags preserve reasons:

- timing available / syllable timing unresolved;
- reference phone available / phone evidence unavailable;
- ASR uncertainty available / unavailable (logprobs are not an utterance confidence);
- at least five usable frames / insufficient voiced frames;
- heavy F0 missingness when more than half the region's raw gated-F0 frames are null;
- tracker instability when production marks any region frame unusable;
- optional evidence issue codes; synthetic provenance; model not integrated.

Five frames and 50% missingness are disclosed **descriptive research flags**, not calibrated correctness gates. Counts and fractions are stored so future evaluation need not reverse-engineer a score. Source agreement/disagreement is not claimed: this pass has no second independent tone/segment detector to compare against F0.

All units abstain from pronunciation diagnosis (`judgment = INSUFFICIENT EVIDENCE`) because connected-speech diagnosis is unvalidated. Specific reasons additionally include missing syllable boundaries, fewer than five usable voiced frames, unresolved reading, tracker instability, timing/text/boundary conflicts, optional provider failures, synthetic evidence, ambiguous target edit correspondence, and unresolved surface expectation. Lexical substitution is still reported factually. Missing data is never a pronunciation error; a matching transcript is never proof of correct tones.

## Output and reproducibility

`markdown(record)` renders the same validated record that is serialized to JSON. It includes intended text when present, exact heard text, timing table, retained word spans, readings, available phone/pitch data, edit relationships, contextual expectations and abstention reasons. Missing phone/model evidence does not create empty report sections. No plotting/classifier output is fabricated. Canonical audio lives only in a temporary directory; original audio stays at its supplied path.

Raw responses remain opaque for future audits. Text and audio digests establish identity checks, not provider truth. Repeated analyses must use a new output directory. The harness does not mutate production DB records, user-facing grading, existing research models or historical experiments.
