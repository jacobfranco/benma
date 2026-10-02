# Interpretation and architectural assessment

**Measured observation is not sound identity, and sound identity is not correctness.**
The [region tables](region-results.md) contain the measurements. This document interprets
what those measurements can support. No learner-facing correctness judgment is made.

## What the evidence supports today

| Dimension | Measurement exists? | Sound identification supported? | Learner-facing correctness supported? |
| --- | --- | --- | --- |
| A. Voicing | Yes, partial: saved raw/selected pitch and candidate strength, contiguous support, gaps; waveform/spectrum are inspectable | Supported frames are evidence of periodicity; no reliable complete voiced/unvoiced segmentation. Missing tracker output is not proof of absent voicing | No |
| B. Vowels/finals | Generic resonance estimates exist in six regions; none passes the fixed summary guards. Spectra and raw Burg trajectories remain inspectable | No vowel, diphthong, nasal-final or coda identity established. Even a passing Burg track would not label a vowel | No |
| C. Initials/consonants | Whole-region spectra in 12/12; prefix spectra in 5/12 | No independently isolated consonants or Mandarin initial labels. Prefixes can contain earlier voicing and boundary contamination | No |
| D. Tone/prosody | Duration/energy in 12/12; some usable saved F0 in 9/12, at least five frames in 7/12; descriptive runs/slopes | No lexical/surface tone classification. Fragmentation, broad ranges and unknown boundaries limit trajectory interpretation | No |
| E. Correctness overall | Measurements exist with explicit abstentions | No gold phonetic labels or validated mapping from features to production categories | **No in every dimension** |

The independence is conditional on the supplied perceived-text/provider span. It does
not turn provider alignment into independent timing truth. Target expectation, reading
resolution and reference-conditioned phone evidence remain separate and unchanged.

## Formants: feasibility result, not a failed-vowel result

Seven regions have a five-frame contiguous saved-pitch nucleus candidate. One is too
short for any fully supported Burg analysis center on the fixed grid. Six have finite
F1/F2/F3 candidates: **68 attempted centers, 25 jointly passing centers**. Five regions
fall below the fixed 70% joint-sanity fraction; the sixth has only two frames. No
region passes all summary guards. Zero adjacent jumps were recorded *among passing
adjacent frames*; rejected/missing stretches are not bridged. Thus instability is not
the demonstrated universal failure mode: sparse support and broad/outlying estimates
are the immediate blockers under this parameterization.

The 5500 Hz ceiling, five-formant Burg model, frequency/bandwidth bounds and 50 ms full
support are general preregistered choices, not speaker-calibrated truth. Failed tracks
include the evidence-rich controls. A nonpassing result cannot show a mispronounced
vowel, nor does it prove that no useful resonance exists in the recording. Individual
F1 values may be more plausible than F2/F3, but this audit deliberately does not promote
selected components after seeing target identities. All raw estimates/bandwidths are
retained locally for future blind inspection; accepted formant summaries stay null.

Nucleus detection depends on saved F0. Therefore this pass cannot assess formants in a
truly voiced portion that the existing tracker missed. It does not fix pitch coverage,
use expected vowel locations, or infer absence of a vowel from a missing candidate.

## Onset/noise: measurable mixtures, unresolved consonants

Five prefix windows contain at least three complete FFT frames. Their centroid medians
range from 806 to 3870 Hz, with IQRs from 184 to 2518 Hz. High-frequency fractions differ,
and the traces show where energy/spectral content changes. This provides material for
human inspection. It does not establish a stable isolated consonant segment.

The prefix of control S02 我 even includes two raw voiced frames before the selected
longest run; the prefix of control S03 你 includes one and is too short for the spectral
summary. Calling those prefixes “aperiodic initial duration” would be false. Prefixes
with no saved pitch also cannot be assumed aperiodic. No confirmed aperiodic duration,
VOT, phone onset, coda or Mandarin initial class is produced. Where the saved voiced
candidate is absent, this implementation retains whole-span spectra and abstains from
onset segmentation instead of cutting an arbitrary first third.

## S02 饭: independent evidence present

After unblinding, this is **R08**, source `u10`, **4820–5250 ms (430 ms)**. It has:

- Digital RMS **0.0526**, nonzero waveform/spectrum, and no near-full-scale samples.
- **11/43** usable selected-F0 frames; raw missingness **69.8%**, selected missingness
  **74.4%**. The existing saved evidence has **five tracker-instability frames**.
  Those flags are retained, not newly diagnosed. Usable median is **108.9 Hz**, range
  **103.0–109.6 Hz**, with a **110 ms** contiguous support candidate.
- Candidate at **159.7–269.7 ms relative to the crop**. Burg has six finite F1/F2/F3
  centers, but only one passes joint sanity; no accepted formant summary.
- A **159.7 ms** prefix with 14 complete spectral frames. Centroid median/IQR
  **2316/2518 Hz**, median ≥4 kHz fraction **0.3004**. This is variable generic
  prefix spectral content; the window is not independently established as an initial.
- A frozen 768-dimensional acoustic embedding, with no phone interpretation.

**Interpretation:** there is real periodic and spectral evidence, with substantial
missingness and constrained segmental interpretability. These measurements do not tell
whether any onset, vowel/final, tone or timing was incorrect. The learner's “I don't
think I said 饭 right” remains **user-reported possible pronunciation issue**, not gold.
Neither recognition as 饭 nor a provider reference phone/score establishes correctness.
The control formant failures prevent treating R08's formant abstention as a distinctive
error signature. No problem was sought or parameter changed after unblinding.

## S13 贵 / 州: lexical substitution, no phonetic gold

The separate identity layer retains intended **我要去广州。** and perceived/deliberately
spoken **我要去贵州。**. That establishes a lexical substitution, not perfect phonetics.

- **贵 / R01:** **2550–2900 ms**, 350 ms, **14/35** usable F0, median **126.9 Hz**,
  140 ms candidate, measurable spectrum and prefix. Six of nine Burg centers pass
  joint sanity, below the fixed passing-fraction requirement; accepted summary absent.
- **州 / R12:** **2910–3370 ms**, 460 ms, **15/46** usable F0, but longest run only
  70 ms. The selected values span **130.7–504.6 Hz**, median **475.0 Hz**, with **no
  existing tracker-instability flag**. This broad/fragmented evidence deserves human
  review; it is neither corrected nor interpreted as a tone. Two Burg centers pass
  sanity, too few for a summary. Prefix spectrum is present.

Both spans are analyzable for waveform/spectral inspection, with partial saved-pitch
support and no accepted formant summary. No reference-phone label entered this conclusion.

## Six recovered regions: did timing recovery provide useful regions?

| Region | ms | Saved usable F0 | Window/formant/onset outcome | Analyzable? |
| --- | --- | --- | --- | --- |
| S01 气 / R06 | 250 | 0/25 | No saved-voicing candidate; formants/onset unresolved | Yes for waveform/spectrum; high-frequency fraction median 0.2024, no sound label |
| S01 first 说 / R07 | 90 | 5/9 | 50 ms candidate; insufficient full formant support; only two prefix FFT frames | Yes, limited; short span may omit transitions/context |
| S01 second 说 / R04 | 90 | 2/9 | No sustained candidate; formants/onset unresolved | Yes for waveform/spectrum and two saved pitch observations |
| S02 上 / R09 | 350 | 3/35 | Longest run only two frames; formants/onset unresolved | Yes for waveform/spectrum; pitch highly sparse |
| S02 吃 / R10 | 380 | 0/38 | No candidate; formants/onset unresolved | Yes for waveform/spectrum; high-frequency fraction median 0.1377, no sound label |
| S03 果 / R02 | 460 | 0/46 | No candidate; formants/onset unresolved | Yes for waveform/spectrum; missing F0 does not establish unvoiced sound |

All six now expose real audio crops and nonzero measurements, so the recovered timing
has diagnostic value. All six still abstain from formant and isolated-onset evidence.
The result does not independently validate boundaries or solve the reading ambiguities.

## Largest blocker and one next bounded step

The largest blocker is **unvalidated phonetic interpretation and boundary/voicing
support**, not lack of additional scalar features. A fixed formant pipeline fails even
the stronger controls; the retained pitch includes gaps and broad branches; and prefix
spectra mix unknown material. The audit cannot determine whether those failures arise
from boundaries, actual phonation, acoustic contamination, model assumptions or tracking.

**One next step: obtain a blinded phonetic annotation of these same twelve regions.**
Give one Mandarin-trained phonetician the sealed packet, with no identity key, target,
reading, scores or self-report. Record boundary plausibility, audible periodic support,
resonance/noise observability and uncertainty; allow an explicit “insufficient crop”
outcome before consulting existing neighboring audio where needed. Lock observations
before unblinding and compare them with the saved missingness and formant failures.
The deliverable is a twelve-row evidence/uncertainty annotation, not an accuracy score
or training set claimed as definitive gold. This bounded annotation would identify
which measurement failure to address next without automatically recording S11/S12 or
starting a model/training program. No annotation was commissioned in this pass.
