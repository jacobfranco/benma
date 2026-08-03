# Mandarin tone evaluation notes

Benma cannot compare speech against four rigid pitch drawings and call the result “tone
correctness.” Lexical tone is one constraint on a surface realization shaped by segmental,
prosodic, physiological, and discourse context.

## Lexical label is not surface contour

- Third tone commonly surfaces as a low/“half-third” contour before T1/T2/T4 and as a rising T2-
  like contour before another T3. A full dip-rise is not the universal target.
- 一 is T1 in isolation/ordinal uses, commonly T4 before T1/T2/T3, and T2 before T4. 不 is commonly
  T2 before T4 and otherwise T4.
- Neutral-tone height depends partly on the preceding tone; its short duration and weak stress are
  part of the evidence.
- Phrase-final position, focus/emphasis, question intonation, and boundary tones can expand,
  compress, or tilt the lexical contour.
- Coarticulation carries preceding/following F0 into a syllable. Initial consonant voicing,
  aspiration, and vowel properties affect reliable tracking and onset.

The corpus stores lexical tones and expected contextual/surface descriptions separately. Surface
descriptions such as `half-T3` remain hypotheses for human review, not universal templates.

## Speaker and tracker effects

Absolute Hertz is not comparable across speakers. The initial diagnostic representation uses
semitones relative to the utterance's median voiced F0 and z-normalized log-F0. This is suitable
for contour shape research but has limitations: a one-syllable utterance supplies a weak baseline,
utterance medians move with tone composition, and range compression can itself be learner error.
Pass 2 should estimate a speaker baseline from multiple neutral/carrier utterances.

Creaky voice, octave errors, voiceless initials, clipping, low energy, and background speech can
make F0 missing or wrong. Missing pitch must stay missing; interpolated display points must never
be mistaken for measured evidence. torchcrepe periodicity and Praat voicing decisions should be
recorded and compared rather than collapsed.

## Evidence roles

F0 initially serves **visualization and diagnostic evidence**, not an autonomous grade. It can
show whether a commercial assessment missed a conspicuous contour or whether the tracker itself
failed. Promotion to grading evidence requires:

1. native and learner speaker-relative baselines;
2. hand-checked syllable boundaries;
3. tone/sandhi-specific human labels;
4. tracker disagreement analysis;
5. false-accept and native false-reject thresholds selected on held-out data.

## L2 English-speaker priorities

The corpus includes the required z/zh, c/ch, s/sh, j/zh, q/ch, x/sh, x/s, u/ü, -n/-ng,
aspiration, retroflexion, Mandarin r, and compound-final contrasts. Primary research supports
testing the eight-way palatal/retroflex/dental-affricate set and shows that English learners'
tone perception/production accuracy changes with phonological context; T2/T3 is repeatedly
identified as difficult. These findings justify strata, not assumptions about an individual.

Sources:

- Wang & Chen, [The Acquisition of Mandarin Consonants by English Learners](https://doi.org/10.3390/languages5020020).
- Hao, [Second language acquisition of Mandarin Chinese tones](https://doi.org/10.1016/j.wocn.2011.11.001).
- Ding et al., [Contextual effect in L2 Mandarin tone perception and production](https://doi.org/10.1016/j.specom.2017.12.015).
- Gu & Chen, [Segmental and Tonal Errors in L2 Mandarin Speech](https://assta.org/proceedings/sst/SST-14/2.A.%20L2%20ACQUISITION/1.%20GU.pdf).

## Open questions

- How should the benchmark encode acceptable regional/native variation without letting learner
  errors pass? Collect geographically and demographically varied Standard Mandarin controls.
- Should neutral tone be evaluated categorically or via duration/relative-height likelihood?
- Do evaluator tone scores respond to lexical labels, produced contour, or both under sandhi?
- When commercial scores and blind listeners disagree, which acoustic evidence explains it?

These do not block corpus collection; they block production grading thresholds.
