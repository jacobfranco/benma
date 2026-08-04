# Mandarin F0 and tone evidence

- Reviewed: 2026-08-03
- Product status: raw diagnostic evidence

F0 is the main acoustic correlate of Mandarin lexical tone, but context, speaker register, voicing, intonation, speech rate, and coarticulation all change observed contours. Listener normalization experiments show that Mandarin tone perception uses surrounding F0 context ([Huang and Holt experiment archive](https://pmc.ncbi.nlm.nih.gov/articles/PMC4187427/)). A single isolated syllable therefore cannot establish a speaker's full register.

The production baseline stores raw Hz, frame confidence, energy, and semitones relative to the median voiced F0 of that utterance. This is explicitly `utterance_local`; session- and speaker-history baselines remain future replacements. Unvoiced and low-confidence frames remain absent. The mobile series uses min/max bucket downsampling so extrema and gaps survive.

CREPE is a neural waveform-level pitch estimator with published noise/generalization evaluation ([Kim et al., 2018](https://arxiv.org/abs/1802.06182)). `torchcrepe` remains the preferred neural research contestant. It is not a required production dependency yet because the personal API deployment has not provisioned or measured its Torch footprint. Production currently uses the dependency-free normalized-autocorrelation v2 baseline, versioned with every parameter. This is a deployment compromise, not a claim that autocorrelation is robust Mandarin MDD.

Known failures include creaky/very-low voice, pitch doubling or halving, clipping, frication, silence, and breath noise. Recording-quality gates (`too_quiet`, `clipping`, `low_voiced_fraction`) suppress interpretation; they do not reject pronunciation.

Quantitative work on Standard Mandarin T3+T3 reports the first T3 as a rising surface tone while also examining non-neutralization in surface F0 ([study record](https://research.polyu.edu.hk/en/publications/a-quantitative-analysis-of-tone-sandhi-in-standard-mandarin-and-n/)). The engine changes the expected surface label for canonical two-syllable T3+T3 but does not demand equality with a TTS T2 curve.

Neutral tone is not “Tone 5 = one low line.” Production marks T0 and disables shape grading. Current work reports contextual/prosodic effects and no single canonical neutral contour ([Xu, 2024 manuscript](https://ora.ox.ac.uk/objects/uuid%3A49b00913-dc47-4bf4-912e-ec1764cab6e9/files/sxk81jn53w); [Lee, 2003](https://www.internationalphoneticassociation.org/icphs-proceedings/ICPhS2003/p15_1121.html)).

Promotion requires real learner and native audio, hand-checked boundaries, tracker disagreement analysis, three-listener labels, held-out false-accept/false-reject results, and a versioned decision record. Synthetic chirps test signal plumbing only.

