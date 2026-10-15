# Contextual neutral acceptance and chunk aggregation

Neutral has no canonical T1–T4 pitch target. A recognized, separately timed dependent
can be positively accepted on structural pitch support even when the numbered-tone
classifier returns UNCLEAR. This is a plausible contextual realization, not proof
of stress, segmental articulation or overall pronunciation.

The production path requires recorded accepted evidence, the exact-playback
utterance/span contract, a chunks-v1 recognized construction, distinct nonoverlapping
single-syllable timing inside the chunk, a resolved neutral reading with surface 0,
and at least one non-neutral grade-bearing head. No character identity is tested.
Playback availability uses the same contract as ExactPlaybackButton; no audio is
downloaded by grading. Transport errors remain player errors.

| Role | Constituent result | Aggregate behavior |
| --- | --- | --- |
| `grade_bearing` | Normal numbered-family grade or unavailable | Carries or vetoes the chunk |
| `neutral_unmeasured_nonveto` | Unavailable; no retained pitch | Does not veto a supported head |
| `neutral_unreliable_nonveto` | Unavailable; measured but structurally untrustworthy | Does not veto a supported head; earns no positive credit |
| `neutral_measured_accepted` | Green: neutral plausibly realized in this chunk | Does not hide a bad, absent or weak head |

Measured neutral evidence must pass the shared full-track sample, duration, timing,
gap, coverage, discontinuity and fragment checks, plus deletion support checks.
Raw tracker branch flags and perturbation-sensitive numbered geometry prevent
positive acceptance. Ambiguous but structurally supported geometry does not need
to win a numbered-tone competition. Rise, fall, level, valley and noncanonical arch
controls are accepted. Sparse, discontinuous and corrupted controls are unavailable
as individual neutrals, but eligible dependents use `neutral_unreliable_nonveto`
instead of becoming numbered-tone grade-bearing vetoes. See the
[October 12 physical classification pass](../2026-10-12-learner-classification/README.md).

Aggregation remains categorical: missing timing/playback or no head is unavailable;
a stable grade-bearing mismatch is red; otherwise any unavailable head makes gray,
any weak head makes amber, and all strong heads make green. Neutral never provides
replacement credit for missing head evidence.

Bounds remain: standalone 吧 is unavailable, quantity 个 does not become neutral,
unresolved readings stay unavailable, and grouped timing cannot create independent
syllables. 那个 follows the same semantic rule as 这个. No recognized chunk or exact
playback means no positive contextual neutral claim.

The frozen fresh 这个 has supported T4 这 and zero retained pitch on 个: the chunk
remains green, and 个 remains independently unavailable/non-vetoing. Constructed
measured-neutral controls are separate from that immutable recording.
