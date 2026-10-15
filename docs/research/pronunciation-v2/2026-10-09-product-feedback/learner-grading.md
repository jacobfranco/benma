# Learner tone-family grading — October 10 focused pass

The primary grade compares an independently observed tone family with an acceptable
expected family. Context cannot change acoustic classification. Intended target,
reference TTS, characters, lexical tones and expected tones never enter the acoustic
shape or tone-likeness functions.

`pitchExpectation` reads the perceived syllable and returns an explicit basis:

1. Resolved reading and numbered `expected_surface_tone`: `resolved_surface` wins.
   This preserves 一, 不 and resolved T3→T2 sandhi, even when lexical tone differs.
2. Resolved surface 0: `neutral`, evaluated through the bounded dependent path.
3. Surface null, resolved reading/pinyin and lexical tone 1–4: `lexical_family`.
   Details say “Tone N family” and “Connected-speech realization may vary here.”
4. Unresolved reading or missing valid expectation: `unresolved`, unavailable.

The fallback never mutates `expected_surface_tone`, backend evidence or readings.
Prosodic/sandhi uncertainty remains secondary coaching, not an automatic veto.
Optional quantity 个 can use its lexical T4 family, but cannot acquire a neutral
exemption without an explicit neutral surface expectation.

| Grade / color | Meaning |
| --- | --- |
| STRONG_MATCH / green | Stable matching family, full acoustic realization |
| PARTIAL_OR_WEAK / amber | Matching family with weak excursion or reduced variant |
| CLEAR_DIFFERENCE / red | Stable different family |
| UNAVAILABLE / gray | Acoustic or linguistic judgment unavailable |

There is no grading-layer half-third or low-register exception. Observed T4/T1
against expected T3 is red. A reduced T3 remains an acoustic T3 with weak strength,
and can be amber when expected T3. Acoustic ambiguity stays gray.

## Inspected frozen-corpus changes

The same 53 units retain the same shape and tone labels (29 classified, 24 unclear).
Grades move from **4 green / 2 amber / 7 differences / 40 gray** to
**15 green / 4 amber / 10 red / 24 gray**. The 16 formerly context-only gray cases
become 11 green, 3 amber and 2 red. One existing amber T4-against-T3 becomes red.
The [pass report](dominant-gesture-pass.md) lists the individual changed cases.
The tone-feedback JSON/CSV use the production grading and presentation functions.
Historical research comparison artifacts remain explicitly historical.

Fresh 我 is green through lexical T3 fallback. Fresh 想 is amber through the same
basis: its 1.033 st descent is genuinely weak under the existing strength rule.
Fresh 买 remains unavailable because support is fragmented; lexical fallback cannot
repair the acoustics. No physical evidence was edited.
