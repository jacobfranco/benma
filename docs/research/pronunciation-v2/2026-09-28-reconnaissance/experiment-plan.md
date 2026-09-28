# First empirical experiment: frozen acoustic tone probe

**Decision:** a syllable-only frozen wav2vec2 Base encoder, mean pooling, a linear T1–T4 head and temperature scaling. Test whether a small native-trained classifier generalizes to unseen speakers and a separate learner source without requiring continuous F0. This is a protocol, not implemented code or measured results.

The clean fallback is a directly licensed native micro-corpus. Common Voice can replace that acquisition step only after its specific usage questions are resolved; AISHELL-3 is another conditional option. Do not silently proceed with YELLOW data or an unaudited aligner. No sufficiently complete public native-data/automatic-aligner chain was verified GREEN under this pass's strict policy. Data acquisition and human annotation remain external prerequisites, not tasks a coding pass can fabricate.

## 1. Data and locked splits

Propose 48 native adult speakers, each with **96 accepted center syllables: 24 per realized class**, comprising 64 isolated instances and 32 centers in short phrases. Use roughly 16–24 base syllables covering vowel/sonorant, stop, aspirate, fricative and affricate onsets and several vowel/nasal finals. Use natural attested words, balance base syllable across tones where possible, and reserve some bases/carrier templates from training for a lexical-shortcut diagnostic. Do not let one syllable, script, device or speaker uniquely predict a class. Phrase selections must be authored and audited by Mandarin specialists, not generated labels accepted on trust.

Record 12–20-minute sessions, randomizing tone order and preserving original files. Target at least 12 low-, 12 middle- and 12 high-pitch speakers with the remainder filling demographic/recording gaps; report gender separately from measured pitch range. Use multiple phone/laptop models, rooms and ordinary rates. Each split must cover every tone and both speech styles. Pitch range is descriptive metadata, not an F0-availability gate.

| Role | Speakers / intended accepted instances | Use |
|---|---|---|
| TRAIN | 24 / 2,304 | Fit feature scaler and head; 576 instances per class if all targets are met |
| VALIDATION-TUNE | 4 / 384 | Select layer/regularization; never update encoder |
| VALIDATION-CALIBRATE | 4 / 384 | Fit one temperature; no architecture selection |
| VALIDATION-OPERATING-POINT | 4 / 384 | Lock probability thresholds for approximately 80% and 60% coverage |
| IN-DOMAIN TEST | 12 / up to 1,152 | Never used for fitting; 240 instances form the double-audited primary gold panel |
| OUT-OF-DOMAIN | Entire OMPAL source held out; FLEURS after its listed provenance question is closed | Initially 60 native OMPAL centers (3 speakers), 120 learner centers (at least 12 learners); optional 120 FLEURS centers. Report these panels separately |
| BENMA LEARNER CHALLENGE | All existing eligible recordings/spans, count re-inventoried later | No training, tuning, calibration, threshold choice or error-driven model selection |
| ROBUSTNESS | Copies of the 240 native gold originals | Share original's split and statistical cluster; never count variants as independent speakers |

Counts are targets, not permission to relabel rejected audio. Recruit replacements or reduce all balanced cells and disclose shortfall. If fewer than 24 train or 12 test speakers are available, call the result a smoke study and make no GO-for-product claim. This is an operational scope rule, not a power theorem.

Assign stable pseudonymous speaker IDs before processing, group all sessions/devices/utterances from the same person, then create stratified deterministic speaker splits with seed 20260928. Audio hash/near-duplicate and prompt-template audits must run before feature extraction. Keep all syllables from an utterance together. Pseudonymous IDs are grouping keys; do not investigate Common Voice identities. Separate-data-source does not mathematically guarantee different people; provider attestation and compatible pseudonymous IDs are preferable to claiming certainty from voice similarity.

**Public-data substitution:** after clearance, target the same speaker/instance counts from CV's validated pool. Rebuild splits by contributor, exclude unknown speaker IDs and uncertain native status, and manually audit every retained label/boundary. Do not use CV's default split as proof of this protocol. FLEURS' published splitting promises cannot supply absent per-speaker identities for the requested fine-grained audit; reserve it as an external panel instead of reconstructing arbitrary speaker groups. Its paper distinguishes train/dev versus test; do not overstate that as proof of all our calibration partitions. [FLEURS collection](https://arxiv.org/html/2205.12446).

## 2. Label contract and inclusion policy

Maintain separate fields for `lexical_tone`, `expected_surface_tone`, `observed_surface_tone`, `correctness`, `surface_rule`, `realization_subtype`, `label_confidence`, rater decisions and adjudication. The classifier consumes **waveform only** in experiment 1. Character, pinyin, lexical/expected tone, requested production, correctness, provider scores, speaker identity and v1 category never enter its feature vector. In a later timing-aware experiment, only numeric center bounds accompany the waveform.

“Observed tone” here means an expert-supported Mandarin surface category, not an immutable contour template. Some realizations are genuinely between categories; annotate ambiguous rather than manufacturing one of four labels. A learner attempting 马 but producing a convincing rising T2 gets observed T2 and expected T3; an ambiguous rise/valley gets no hard class. Tone correctness is a later comparison and cannot certify segmental correctness.

| Bucket | Inclusion rule |
|---|---|
| SAFE ISOLATED / READ SYLLABLE | Both native raters agree on realized T1–T4 with high confidence, boundary and syllable identity are clear; prompt alone is insufficient |
| SAFE CONNECTED | Both agree on category in context; transcript matches; no unresolved heteronym, reduction or phrase boundary; ordinary coarticulation permitted |
| SURFACE TRANSFORM REQUIRED | Record lexical and transformed expectation separately; include only after listening confirms realized class and relevant prosodic grouping |
| AMBIGUOUS / EXCLUDE | Disagreement, categorical indeterminacy, unclear syllable identity/timing, overlap, truncation, code-switching, singing, severe distortion, uncertain native reading; retain in a research manifest |
| NEUTRAL / DEFER | Never relabel as T1 or “weak T3”; outside the four-tone metric; retain explicit unsupported status |

This five-bucket framework is sufficient **only with independent dimensions for boundary quality, label confidence, licensing and source/speaker identity**. A clear tone with untrustworthy boundaries is not a safe training example. Conversely, fragmented Praat F0 is not an exclusion if listeners can identify the realization.

Two Mandarin-native annotators with phonetics or pronunciation-teaching experience independently listen first without target tone, v1/v2 output or ASR guesses. They may replay the original phrase after an initial center judgment. Then reveal transcript to audit syllable identity, lexical reading and sandhi; retain both judgments. A third adjudicator handles disagreements. Primary gold requires agreement after review with high confidence; unresolved cases become an ambiguity panel. Preserve disagreement rate, excluded counts by tone/source and raw rater labels, because easy-case filtering can otherwise inflate apparent accuracy. Report raw agreement and Cohen's kappa with sample counts; kappa is descriptive, not a truth certificate.

For native training, both raters verify every retained instance under the strict high-confidence rule; corpus pinyin/rules are suggestions that reduce lookup labor. For the 240-item gold, audit timing too and conceal all model output until labels are locked. Human listening remains fallible: confidence tiers make that limitation visible. Do not use TTS, v1, ASR text equality or an LLM to certify gold.

### Sandhi and connected speech

- **Third-tone pair:** a clearly grouped lexical T3+T3 often yields a T2-like first surface syllable. Label that first syllable observed T2 only if heard as such, recording `sandhi_T3` provenance. Do not assume acoustic identity with every lexical T2. Exclude long T3 chains or uncertain grouping initially.
- **一:** quantity uses commonly change to T2 before T4 and T4 before T1/T2/T3; isolated/ordinal/numeral uses can remain T1. Reduplication, names, emphatic citation and ambiguous grammar require audit or exclusion.
- **不:** ordinary pre-T4 change suggests T2; otherwise commonly T4. Reduplicated/reduced/emphatic uses are not automatic labels.
- **Partial T3:** a low or low-falling contextual T3 need not rise. Keep it T3 when the contextual category is confidently heard, tag the subtype, and evaluate separately. Never force it into T4 just because the slope falls.
- **Heteronyms/erhua:** resolve reading and character-to-syllable mapping in context; 儿 is not always a second syllable. Unresolved mapping is excluded.
- **Prosody:** declination, focus, phrase-final lengthening and question intonation alter realization. Keep ordinary variation; defer examples whose category is not identifiable. Neutralization is unsupported, not a fifth hidden training class.

These are conservative policy choices informed by [experimental T3-sandhi work](https://pmc.ncbi.nlm.nih.gov/articles/PMC4066894/), [coarticulated-tone research](https://pubmed.ncbi.nlm.nih.gov/8201120/) and [MIT Mandarin tone analysis](https://sls.csail.mit.edu/archives/root/publications/2001/Wang_phd_thesis.pdf). Existing `surface.py` supplies limited expectations, not observed labels or a comprehensive phonology engine.

## 3. Alignment and extraction

**First experiment: manual boundaries on a deliberately small corpus**, using waveform/spectrogram/listening and isolated prompt files. This removes a commercially ambiguous alignment-model dependency. Preserve syllable onset/end plus optional initial/rhyme/nucleus times, boundary uncertainty and annotator provenance. Manual labeling is slower but feasible at this scale; estimate 20–60 seconds per center boundary after familiarization, in addition to label listening. Measure actual annotation throughput on the first 100 examples.

| Method | Mandarin / resolution | License and suitability | Accuracy, setup and speed assessment |
|---|---|---|---|
| Corpus-provided boundaries | Best where available; inspect whether word, character, phone or syllable | Inherits corpus/annotation rights | Validate a stratified sample; no general accuracy claim; cheapest to ingest |
| Manual TextGrid/CSV | Any Mandarin; explicit syllable and phone tiers | No pretrained-weight lineage; corpus and annotation rights still required | Low setup, highest human time; two-rater boundary audit on gold |
| MFA Mandarin | GMM-HMM; phone/word TextGrid, syllables derived with dictionary mapping | MFA code MIT; Mandarin v3 weights CC BY-4.0, but includes AI-DataTang NC-ND and other corpora: **YELLOW lineage, not first** | Mature CPU/batch tool; conda/Kaldi/dictionary setup medium-high; read-speech performance does not establish learner boundary precision |
| CTC segmentation | Mandarin only with appropriate ASR checkpoint/token inventory; character timing possible, not automatically phone timing | Package Apache-2.0; checkpoint separately audited | Moderate setup, encoder dominates cost; blank spans/coarticulation produce approximate boundaries |
| MMS model family | Many languages; alignment/timestamp workflows possible | Inspected MMS-1b-all checkpoint CC BY-NC-4.0: **RED**. Verify each FA checkpoint separately; do not infer permission from library license | Large model and romanization/CTC mappings; no reason to add it to this first path |
| Existing Benma Azure/replay timings | Some recorded “phone” intervals are entire pinyin syllables | Saved authorized evidence only, no new paid calls | Useful challenge provenance; not a general offline corpus-preparation solution |

[MFA code license](https://raw.githubusercontent.com/MontrealCorpusTools/Montreal-Forced-Aligner/main/LICENSE), [Mandarin model/data inventory](https://mfa-models.readthedocs.io/en/latest/acoustic/Mandarin/Mandarin%20MFA%20acoustic%20model%20v3_0_0.html), [CTC license](https://raw.githubusercontent.com/lumaku/ctc-segmentation/master/LICENSE), [MMS card](https://huggingface.co/facebook/mms-1b-all).

For later automatic alignment: normalize transcript with original character offsets preserved; resolve word/heteronym/erhua readings; map each syllable to the actual dictionary phone sequence; align the **known transcript**; reconstruct character → pinyin → phone group → start/end. Reject omissions, repeats, unknown phones and transcript mismatch. Never infer syllable boundaries by splitting duration evenly or by taking every TextGrid tier as the same unit. The current benchmark parser flattens intervals and is not a ready phone-to-syllable gold extractor.

Audit absolute boundary error against manual gold, reporting median/p90 and fractions within 20/40 ms, stratified by initial. Those are measurement bins, not established MFA performance. Record onset definition (including stop closure where audible) and uncertain boundaries. Later test ±20/40-ms boundary jitter on validation; never tune crop edges by target tone or by agreement with v1.

Keep the full syllable, including unvoiced /t/, /q/, /x/, /s/, /sh/, /ch/ and aspiration. These intervals may legitimately have no F0. Do not trim to a Praat-voiced region, fill gaps or train “voiced at every frame.” A future rhyme-pooling ablation requires genuine phone boundaries; v1's evidence region is not a phonetic nucleus annotation.

## 4. Exact first model recipe

1. Confirm rights/consent manifests, accepted labels and locked speaker splits. Pin baseline commit, dataset revision, encoder revision/hash and preprocessing configuration. Refuse unknown lineage or missing required metadata.
2. Decode original audio; preserve originals and checksums; resample once to mono 16-kHz PCM. Use variable-length syllable `[start,end)` samples with **zero acoustic padding** as the starting hypothesis. Initial supported duration band 0.15–1.5 s is a processing scope choice; report out-of-band items separately, never silently drop difficult test items.
3. Apply the exact checkpoint feature extractor's waveform normalization; no pitch normalization, denoising, F0 trimming, time warping or augmentation. Log low RMS/clipping before normalization. Near-silence/corrupt-input checks are signal checks, not continuous-pitch requirements. Use **one unpadded crop per encoder call initially**: group-normalized feature extractors can change representations when padding changes, even if pooling excludes padding. Later batching must measure that effect and retain masks/length provenance; do not assume numerical equivalence.
4. Frozen `facebook/wav2vec2-base`, evaluation mode, no gradients and no stochastic masking/dropout. Extract Transformer layers **4, 6, 8** (explicit layer indexing documented). Mean pool valid syllable frames. First preregistered default is layer 6; select among the three on VALIDATION-TUNE only.
5. Standardize each pooled feature dimension using TRAIN means/stds only, with a fixed small denominator floor. Fit multinomial logistic regression (linear 768→4 softmax) with unweighted cross-entropy on balanced examples and L2 regularization. Use deterministic LBFGS, max 1,000 iterations and a convergence check; test `C ∈ {0.1, 1, 10}` on VALIDATION-TUNE. Report convergence failures rather than selecting a failed fit. No accuracy-based example removal.
6. Training diagnostic: loss and train macro F1; selection: tune macro F1, then lower NLL to break ties. Check T2/T3 and held-out bases, but do not repeatedly redesign the model around them. Majority/chance and within-speaker shuffled-label controls check pipeline leakage.
7. Fit one positive scalar temperature by minimizing NLL on VALIDATION-CALIBRATE. Keep head/layer/scaler fixed. Fit operating thresholds separately as below.
8. Freeze artifacts, run tests once: ID/native gold, connected strata, OOD, learner, Benma challenge and degradations. Compare to the fixed v1 operating points. Report all abstentions/failures, not just scored successes.

This is one bounded experiment: at most nine primary small head fits plus calibration; not an architecture search. If validation is negative, the only preregistered diagnosis is three-bin temporal pooling using the same frozen selected layer, and then the single HuBERT backup with the same protocol. Choose whether to run these diagnostics, and select the final configuration, **on validation before opening any test or Benma challenge results**. Evaluate the locked primary and any preregistered diagnostic variants together, reporting all rather than selecting a test winner. A negative finding is about this bounded formulation, not all learned tone classifiers; any redesign after test inspection requires a new holdout.

**Context follow-up**, after the first readout: compare exact crop against ±100 ms and ±250 ms of available acoustic context using **center-only pooling**. Clamp at recording boundaries, mask center frames using true feature receptive-field positions, and log available context; never stretch audio or invent neighbors. Whole-window pooling is a control, not the preferred phrase extension. Padding values are hypotheses, not established optimal amounts. Context Transformer states can still encode neighbors even when pooling only center frames; inspect neighbor-only and held-out lexical/carrier controls before attributing improvements to tone.

## 5. Native gold and learner challenges

The primary native gold is **240 centers, 60 per tone, 12 speakers × 20**; for each speaker choose 5 per tone. Cross-class quotas: 120 isolated / 120 connected, each class split 30/30; 120 clean / 120 naturally consumer-quality, balanced within class/style as far as recording availability permits. Device and speaker must not be confounded. All 12 test speakers should contribute both recording conditions. Include several initials/finals and rate bands. Among T3 examples, tag full and partial realizations; among surface T2, tag sandhi-derived and lexical cases. Small subtype cells are descriptive, not standalone validated benchmarks.

150–300 instances is enough to expose large errors and compare a few architectures, **not certify production safety**. At 240 independent items, a nominal 90% accuracy would have a Wilson interval roughly 85.5–93.2%; at 60 per tone it is roughly 80–95%. These are illustrative calculations, not results. Speaker dependence makes uncertainty wider. Report paired bootstrap intervals by speaker (e.g. 10,000 resamples), individual speaker results and leave-one-speaker-out sensitivity. With 12 clusters, acknowledge unstable interval tails. Bootstrap originals with all degradation copies together; never count frames or variants as independent samples.

OMPAL learner pilot: choose 120 centers from at least 12 speakers and both proficiency groups, stratify original tone-correct/incorrect judgments before inspecting model output, then obtain realized-tone annotations. Balance classes if available but preserve/report natural correctness prevalence separately. Correctness agreement is a separate analysis: a model can correctly identify T2 in an attempted T3 and should not receive a classification penalty for it.

Benma: prior F0 inventory reports 67 recordings, 116 syllable rows, 101 numeric spans, 95 timing-authorized spans and six timing-rejected. These are historical local reports, not a fresh DB inventory. Some current temp WAVs are absent. Inventory existing authorized exports/storage later; do not fabricate boundaries or call paid providers. Include frozen v1 failure cases, but manually label before scoring and disclose that v1 was already tuned on this convenience set. This is a product regression/challenge, not an unbiased population comparison. If insufficient independent labels exist, return case-level blinded observations without an accuracy claim.

## 6. Robustness benchmark, not training augmentation

Use the same 240 gold originals with deterministic variants; preserve clean references. First test one factor at a time, then two modest combinations after the individual results. Verify transforms preserve sample alignment or record encoder delay/trim offsets.

| Condition | Initial test levels / interpretation |
|---|---|
| Codec | Opus 24 and 12 kb/s; AAC 64 kb/s; decode to 16 kHz; record implementation/version, bitrate and delay |
| Resampling | 48→16 kHz; 44.1→16 kHz; 16→8→16 kHz telephone-band stress; use proper antialiasing |
| Additive noise | 20, 10 and 5 dB SNR against active-speech RMS; seeded synthetic noise first, licensed real room noise later |
| Reverb | Simulated room response RT60 about 0.2 and 0.4 s, report direct/reverb balance; distinguish realistic mild from stress |
| Gain | −6, −18, −30 dB; preserve quantization floor and track actual clipping/RMS. Waveform normalization may remove much pure-gain effect |
| Clipping | Adjust gain/limit for approximately 0.1%, 1%, 3% clipped active samples; report actual rate, not guessed “mild” labels |
| Combination | One moderate codec+noise and one gain+noise condition, defined before opening final results |

Some low-SNR/clipped variants may become unidentifiable; raters review an example from each severity and any disputed gold transfer. Such examples belong in an uncertainty/stress panel, not automatic wrong-tone ground truth. Do not use pitch shifts or time stretching in phase 1: they can change the tonal cue being labeled. Frozen clean training stays unchanged for this first measurement. Any later augmentation decision uses validation/development failures and a new locked test version, not repeated tuning on the gold results.

## 7. Metrics, calibration and abstention

Report T1–T4 confusion with an additional abstain column; macro F1; balanced accuracy (=mean per-tone recall, define “macro accuracy” this way); per-tone precision/recall/support; directional T2→T3 and T3→T2 errors; correct/wrong/abstain fractions on **all** eligible items. Also report forced-choice V2 accuracy as a diagnostic, clearly separate from selective results. Stratify by speaker, pitch range, microphone/condition, native/L2, isolated/connected, T3 subtype, sandhi, duration and boundary quality.

Compute NLL, multiclass Brier score and small-bin reliability plots before/after calibration. ECE is descriptive with five equal-count bins and counts/intervals, not a small-sample optimization target. A scalar temperature is the first choice because it is simple and preserves argmax; it does not guarantee calibration after domain shift. [Temperature-scaling study](https://proceedings.mlr.press/v70/guo17a.html).

Choose **max calibrated probability** as the initial acceptance score. Use VALIDATION-OPERATING-POINT quantiles to define 80% and 60% nominal coverage thresholds (handle ties deterministically); report actual test coverage, never retune thresholds to test labels. Also plot test risk/coverage curves by ranking score, clearly labeling those as diagnostic curves rather than deployed thresholds. Report margin and entropy for analysis, but do not fit three simultaneous gates. Acceptance is not OOD detection: a four-class softmax can be confident on neutral tone, silence or a wrong syllable. Keep unsupported-input/neutral controls as a separate abstention challenge. [Selective classification research](https://arxiv.org/abs/1705.08500).

“Good” requires accepted observed tone agreeing with an independently established expected surface category. Estimate both `P(observed correct | accepted)` and the precision of the tone-match verdict; also report false-Good rate among independently labeled wrong-tone attempts. These denominators are different. Native-correct data alone cannot validate false-Good behavior. Do not label tone match as overall pronunciation correctness.

## 8. Fair v1 comparison and preregistered decisions

Run frozen v1 from `68057aa57cdfccbba01c986be827a402fcb59a67`: current whole-recording Praat extraction, original parameters, then the **same audited center bounds** and timing eligibility. V1 may use its existing acoustic evidence selector; do not replace it with learned-model crops or trim it to voiced frames. Preserve whole recording for v1 because its gates include recording-wide information. V2's initial crop has less context; disclose this asymmetry and compare context variants later, rather than change v1 to manufacture equal inputs.

Give both systems identical gold labels and count every supported center, including when v1 rejects pitch. Show v1 categorical output at (a) all emitted T1–T4 categories and (b) its moderate-confidence operating point. Low/moderate are ordinal states, **not probabilities**; no invented v1 softmax or temperature fit. Show the actual learner-verdict mapping separately. V1 cannot be forced to any arbitrary 60/80% coverage: show its attainable points against V2's curve, interpolate V2 only with explicit tie handling, and include comparisons on the shared accepted subset plus the all-item outcome table. V1 abstention is neither a confident error nor a free correct answer.

The following are **proposed decision tolerances chosen before seeing outcomes**, not literature accuracy requirements. A 5-point gain is 12 extra correct outcomes on a 240-item panel; a 2-point regression margin is about five items. The small gold panel may not resolve these margins, so INCONCLUSIVE is a valid outcome. More tuning is not a substitute for more independent speakers.

| Category | Criterion for advancing this prototype to a larger evaluation |
|---|---|
| MUST IMPROVE | All-item macro F1 improves by at least 0.05 absolute over v1, counting abstentions as missed true classes; paired speaker-bootstrap lower bound for the difference exceeds zero. Additionally gain at least 0.05 coverage at v1's error rate **or** reduce selective error by at least 0.02 at a common attainable coverage, with uncertainty reported. Both conditions prevent a win based only on guessing former abstentions. |
| MUST IMPROVE | T2/T3 pair macro F1 improves; both directional confusions reported. Require no increase in pair selective error at matched coverage. If sample support is insufficient, classify this criterion inconclusive. |
| MUST NOT REGRESS | Native clean and moderate degradations: no >0.02 loss in selective accuracy at common coverage, assessed with paired intervals; no hidden loss from lower coverage. Require the lower bound on accuracy difference above −0.02 for a positive noninferiority claim. |
| MUST NOT REGRESS | Learner false-Good risk: no newly systematic confident error pattern and no >0.02 increase where adequate wrong-tone support exists. Small Benma panel is descriptive; cannot prove this bound. Abstain more as information degrades, rather than turn missed F0 into confident errors. |
| MUST NOT REGRESS | Calibration: temperature scaling must not materially worsen held-out NLL/Brier; uncertainty bands and domain-specific plots required. Accuracy at 60% coverage should be at least that at 80%, within sampling error; failure triggers uncertainty investigation. |
| Operational gate | For later interactive candidacy, warm CPU p95 ≤1 s for one ≤1.5-s center and RSS ≤4 GiB on the inspected machine, with cold start separately measured. These are provisional product budgets, not measured guarantees. Missing this gate can still justify offline research, not deployment. |
| NICE TO HAVE | Better OOD connected speech, meaningful confident coverage on v1-fragmented-F0 cases, stable across low/high pitch and unseen bases, sub-300-ms CPU p95. |

**GO** means advance to a larger independently labeled evaluation, never replace v1 from this small study. **NO-GO for this formulation** means no useful validation/test improvement after the bounded temporal/backup diagnosis or unacceptable confident learner errors. **INCONCLUSIVE** means uncertainty, labels, rights, speaker coverage or compute measurements cannot settle a criterion. Report the conclusion honestly; the strict noninferiority gates will often be underpowered with 240 items.

## 9. Artifacts, later ablations and implementation scope

The later harness can live under `benchmark/pronunciation_v2/` with its own optional environment; data/cache outputs outside tracked documentation. Expected small reviewable artifacts: rights/source manifest; split manifest and leakage report; syllable/annotation manifest; frozen config and environment lock; tiny trained head and scaler/temperature; per-instance predictions with provenance; confusion and metric CSVs; calibration/risk-coverage plots; v1 paired-outcome table; degradation manifest; error audit; CPU timing/RSS report. Avoid audio/embedding dumps in Git.

Manifest should include source release, license evidence, consent scope, original/canonical audio hashes, speaker/session/device, utterance and character offset, syllable boundaries, optional rhyme bounds, lexical/expected/observed labels, subtype, rater confidence, exclusion reason and split. Prediction output adds encoder revision/layer, preprocessing and head hashes, logits/probabilities, acceptance/reason and v1 comparison tuple. Keep expected tone in the evaluation table, not the model input manifest.

Future hybrid: same frozen encoder/head budget, same splits, add explicit F0/periodicity statistics **and missingness flags**; compare embedding-only, F0-only and combined using validation. Include fragmented-F0 strata, and never impute absent F0 as zero Hz. No training target from v1. A hybrid must improve held-out risk/coverage, not merely agreement with v1.

Phrase extension: retain aligned syllable centers, classify each within bounded acoustic context using timing-aware pooling; maintain per-syllable uncertainty. Handle shortening, coarticulation, declination and partial T3 through diverse observed labels, not contour templates. Reusing an entire phrase's encoded states is a separately tested efficiency variant, since it changes context. Expected sandhi logic remains downstream and independent.

Estimate **3–5 engineering days after usable data exists**, plus roughly 35–70 annotator-hours for paired labels/boundaries and gold review, 48 recording sessions and recruitment/rights turnaround. Estimate retained audio 1–3 h and local compute 1–6 h initially; benchmark to revise. No paid inference provider is needed. Monetary planning example only: participant honoraria `48 × $10–25` plus annotation `35–70 h × $25–60/h` gives about **$1.4k–$5.4k**, excluding legal/recruiting fees; these are budget assumptions, not researched vendor quotes or authorized purchases. Public-data clearance may reduce recruitment cost but not eliminate alignment/audit labor.

Next coding pass: **HIGH**, because leakage controls, boundaries, v1 parity and uncertainty evaluation need careful implementation. MEDIUM fits a later isolated cache/head task once manifests are accepted. EXTRA HIGH is not justified before data and labels exist. No full fine-tuning, new F0 tracker, production service/schema/UI changes, live provider calls, deployment, large dataset collection/download or model training occurs in this reconnaissance.
