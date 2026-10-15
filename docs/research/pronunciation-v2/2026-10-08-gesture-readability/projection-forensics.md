# Projection forensics

## Identity and exact saved take

The complete local PostgreSQL read-only search returned one perception containing
我想买这个. The newest 45 perceptions and latest 32 analyses were inspected; local
private snapshots are in `services/api/var/gesture-readability/saved/`. No database
record was changed and no provider was called.

| Identity | Value |
| --- | --- |
| Perception | `a8250bd2-be9d-4637-9e61-116b18fc44df` — 我想买这个。 |
| Attempt | `2706b173-a023-43fe-a018-a8925a58a60f` |
| Utterance | `18160a37-f824-458f-ad80-22ae3e8776c7` |
| Analysis | `874ae05a-bd67-4836-a53c-f78df5d129b0` |
| AcousticRun | `62009479-e6a6-4513-8185-8de040144150` |
| Accepted timing evidence | `d6c0485b-2e51-429c-9d3e-071f1bcb8248` |
| Pitch evidence | `d9e0f4764f30341b01933a5d8f725828f4ecac26aacae09440df99aeb644bf97` |
| Canonical SHA-256 | `138433436566bd47b4e7731c43333d6dafa9f7e631b7b168ce954e8ca0f2ae4a` |

The source audio bytes match the asset, analysis, and immutable pitch track. This
is the unique matching saved take, not an independently observed phone session.

## Accepted span = selected playback span

All times are canonical seconds. Source indices are zero-based. Frame sets are
half-open in time even though index ranges below show inclusive first/last indices.

| Unit | Timing and playback | PCM samples [first,last) | Projected indices | Selected indices | First/last selected time | Count | Strict integrity / gesture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | 0.44–0.95 | 7040–15200 | 41–91 | 50–90 | 0.5304–0.9304 | 41 | sufficient / level |
| 想 | 0.96–1.55 | 15360–24800 | 93–151 | 109–151 | 1.1204–1.5404 | 43 | sufficient / unclear |
| 买 | 1.56–2.17 | 24960–34720 | 153–213 | 153–195 | 1.5604–1.9804 | 43 | unstable / unclear |
| 这 | 2.34–2.73 | 37440–43680 | 231–269 | 245–259; 263–267 | 2.4804–2.7004 | 20 | unstable / unclear |
| 个 | 2.74–3.04 | 43840–48640 | 271–300 | none | none | 0 | insufficient / unclear |

The selected timestamps in each continuous range increase by 0.01 s. Every timestamp,
index, F0 value, reason, and graph segment is also explicitly listed in
[projection-replay.json](projection-replay.json), including all 53 audit units.

我/想/买 each have one retained segment. 这 has 15 points at 2.4804–2.6204 and
five at 2.6604–2.7004: a 40 ms center-to-center break, containing three missing
10 ms measurements. Its raw pitch jumps from 98.441 to 157.018 Hz across this gap
(about 8.08 st). Both fragments fall; their upward reset prevents describing the
whole unit as one clean fall. We neither hide the second fragment nor relabel it 个.

买's reason is `raw_pitch_discontinuity`. 这 has that same reason. 个's reasons
are `too_little_sustained_evidence`, `voiced_boundary_lost`, and
`raw_to_selected_attrition`. Its eight raw points, source indices 291–298, occur
at 2.9404–3.0104 and were energy-excluded before gesture eligibility was calculated.
See [the energy audit](energy-gate.md).

## Production ownership contract

For an accepted individual interval `[start,end)`, a selected-unit graph may use
only retained immutable frame timestamps inside that interval. It must never own
a frame belonging only to a following interval. Exact shared boundaries belong to
the following interval. Accepted timing can tolerate at most 1 ms overlap; existing
mobile ownership resolves that overlap by later start, then perceived index. No
new tolerance was introduced. There are no overlapping retained assignments in
this replay. Untimed and synthetic/equal-split boundaries confer no ownership.

The backend `project_pitch` stores the original track ID, timing evidence ID, span,
and all frame indices, including unvoiced/rejected frames. The displayed subset
is precisely the selected points in that projection. `sentence_pitch_evidence`
serializes source indices and unsmoothed retained semitones; it splits at timing
boundaries before simplifying the separate Mine display. `unitPitch` filters the
actual points, preserves gaps, and uses a shared utterance pitch scale. It does
not merely hide out-of-domain points. `PitchPlot` receives this subset.

`PronunciationWorkspace` supplies the same selected unit's start/end to both
`PitchPlot` and `ExactPlaybackButton`. `exactRecording` crops canonical 16 kHz mono
PCM at nearest sample, with no padding; maximum sample rounding is 31.25 μs. The
replay executes these actual TypeScript functions and verifies resulting sample
counts. Repeated unit switches and new analysis selection reset are regression-tested.

The current backend classifier uses smoothed `display_contour`, while the selected
workspace uses unsmoothed retained `tone_graph.filtered`. This representation
difference is relevant to gesture calibration; it is not an ownership error.

## Frame semantics

The saved analyzer uses `sound.to_pitch_ac`, `pitch.xs()` frame centers, 10 ms steps,
a 50 Hz floor, and `very_accurate=False`. The physical Hanning support is 3/50 =
60 ms, approximately ±30 ms around each center. Energy is measured in a separate
40 ms centered window; the low-frequency quality diagnostic uses 100 ms. Centers
are rounded to four decimal places for storage, at most 50 μs. No window-start
conversion, arbitrary clipping, or temporal offset is appropriate.

These semantics follow the [Praat Pitch object documentation](https://www.fon.hum.uva.nl/praat/manual/Pitch.html)
and [raw autocorrelation settings](https://www.fon.hum.uva.nl/praat/manual/pitch_analysis_by_raw_autocorrelation.html),
checked against the repository's actual saved parameters. Windows centered near a
boundary can legitimately include samples from both sides; source ownership still
uses the center. Even the last center of 这's second fragment has pitch-window
support ending around 2.7304 s, before 个's accepted 2.74 s onset. The report cannot
be explained as an entire neighboring contour crossing this boundary.

## Closure

**PER-UNIT PITCH PROJECTION VERIFIED.** No production projection fix was justified.
The saved take establishes case A/C at the acoustic-selection stage: raw estimates
exist for 个, but no selected pitch survives. It is neither stolen evidence nor
the strict eligibility layer hiding correctly retained points. A deterministic
counterfactual regression supplies real numeric points inside 个's span and confirms
that selecting 个 displays them even with insufficient strict eligibility.

Grouped 雨伞 (`40357072`, 3.56–4.87 s) remains one unit/projection/playback action.
`d47274bc` has no accepted timing and therefore no selected-unit graph or bounded
playback. Target changes and the 广州/贵州 mismatch test leave perceived ownership
unchanged. Full utterance raw detail remains available separately.
