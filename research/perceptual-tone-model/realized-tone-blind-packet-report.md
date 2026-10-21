# Blinded realized-tone perceptual packet — 2026-10-19

The 52-presentation packet is ready for developer listening review. No perceptual
answers have been collected, ingested, or scored. The frozen learner-domain transfer
conclusion remains **MIXED**; legitimate nucleus/coda pooling remains **NO GENERAL
IMPROVEMENT DEMONSTRATED**. The 16-unit natural release and all earlier QA decisions,
quarantines, spans, labels and saved predictions remain unchanged.

| Composition | Unique units | Additional presentations |
| --- | ---: | ---: |
| Accepted documented-natural learner units | 16 | 3 repeats |
| Hidden native controls | 28 | 5 repeats |
| Total | 44 | 8 repeats; 52 presentations |

All 16 accepted natural units from `benma-learner-natural-v1-20261019` are included.
Excluded: all 16 quarantined natural units, all 12 diagnostic candidates (11 accepted,
one quarantined), and all 79 unknown-provenance candidates (75 accepted, four
quarantined). No diagnostic or unknown-provenance speech enters this packet.

The learner release manifest SHA-256 is unchanged:
`8024a51df91e60b9e336189cd9b04dfbf2d5d8c530fd0656778c731e1306f4ae`.

Controls contain **6 T1, 6 T2, 6 T3, 6 T4, and 4 NEUTRAL** items, covering **12
speakers**, 28 distinct utterances/source PCM recordings, and 26 phonetic identities.
Eight speakers contribute two controls each; four contribute three. Each tone class
spans at least four speakers. These speakers are disjoint from the learner speaker.
All controls use the frozen experiment's **test** speaker partition; the archive
member name `train` is corpus provenance, not the experiment partition.

**Control QA distinction approved by the user:** use release-approved controls with
mechanical checks instead of requiring an individual listening PASS on every item.
None of the 28 selected controls has an individual listening PASS record. Their
eligibility derives from the existing release's corpus-wide automatic and human
spot-check acceptance, with explicit quarantines preserved. Do not describe them as
28 newly or individually listened-to controls. No listening or perceptual cherry
picking was performed in this pass.

The frozen native manifest contains 947 accepted test items. A label-independent
quality screen excluded 53 flagged/atypical candidates and left 894 eligible
controls. Every eligible control was mechanically checked against its exact source
WAV hash and PCM hash, speaker registry, corpus transcript line/read-unit label,
frozen owned-phone sequence and spans. Each selected item has nonzero periodic
material and no whole-target digital saturation. Quarantined items are never
eligible. Unique source/PCM ownership prevents accidental independent duplicate
counts. Corpus read-tone labels are used only for control balancing and the hidden
reference key; learner expected tones never guide selection, repeats or ordering.

Mechanical checks reproduce the frozen nucleus/coda projection without changing
timing or running alignment. Periodicity presence uses fixed 40 ms windows, 10 ms
hops, 60–500 Hz autocorrelation lag bounds, normalized peak at least 0.35, and
mean-square energy at least 1e-6. Whole-target PCM16 peaks must stay below 32760.
These are integrity/presence checks, not tone estimates or calibrated classifiers.
They cannot independently prove absence of perceptual boundary clipping. Existing
release QA remains the boundary-quality evidence.

| Group / view | Count | Min | Q1 | Median | Q3 | Max | Mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Learner tone-bearing | 16 | 20 ms | 60 ms | 95 ms | 112.5 ms | 230 ms | 96.875 ms |
| Control tone-bearing | 28 | 70 ms | 100 ms | 120 ms | 182.5 ms | 280 ms | 142.857 ms |
| Learner whole target | 16 | 60 ms | 152.5 ms | 215 ms | 267.5 ms | 370 ms | 212.5 ms |
| Control whole target | 28 | 110 ms | 170 ms | 210 ms | 250 ms | 320 ms | 212.857 ms |

These summaries exclude repeat presentations. Controls cover 10 short (at most
100 ms), nine medium (over 100 through 160 ms) and nine long (over 160 ms)
tone-bearing spans. The distributions are reasonably close but not identical;
learner spans include much shorter material. No span was extended to force a
match. Two controls are at utterance edges and 26 are utterance-medial. Internal
prosodic phrase boundaries are unavailable, so utterance position is explicitly
only a proxy; phrase-edge balance is not claimed.

**Randomization and seals.** Seed: **20261019**. Control selection balances frozen
read-tone classes, speakers, coarse durations, position proxies and phonetic
diversity. Repeat selection uses one random learner item per accepted take and one
random control from each tone class. Learner expected tones and model results are
not inputs. Ordering prohibits consecutive presentations from the same source and
runs of three from the same speaker. Repeats have distinct random 80-bit opaque
IDs and occur 15–38 positions apart. Presentation order, seed and repeat relations
are stored only in the private selection artifact and key.

Packet SHA-256:
`f5c041a22f03ddf41337472fd494397a055adfee9fd16ba234c75d3ea2ead6a4`.

This hashes the canonical public manifest (version, ordered opaque IDs, both actual
embedded WAV byte strings). The private selection seal also records the physical
manifest file hash, including its trailing newline. The completed annotation
export carries the canonical packet hash. The artifact seal additionally hashes
the HTML, private key, selection, construction code and preregistered plan.

Selection, repeat/order decisions and the public audio were sealed **before** the
separate `blind_key` module semantically read saved model results. That module only
joins existing frozen primary expanded/pilot/deterministic results into the private
key. It cannot select items or render the page. No model was deserialized or run.
Control result fields are null with an explicit availability reason; no new control
inference was performed. Native lexical/expected labels remain null where the
corpus did not independently provide them. Learner realized-tone fields remain null.

**Exact review artifact and export paths.**

- QA HTML: `/home/jacob/benma/research/perceptual-tone-model/data/generated/realized-tone-blind-v1-20261019/qa/index.html`
- Completed human export: `/home/jacob/Downloads/benma-realized-tone-blind-review.json`
- Hidden key, for use only after review: `/home/jacob/benma/research/perceptual-tone-model/data/generated/realized-tone-blind-v1-20261019/private/answer-key.json`
- Presentation order/eligibility audit: `/home/jacob/benma/research/perceptual-tone-model/data/generated/realized-tone-blind-v1-20261019/private/selection.json`
- Manifest: `/home/jacob/benma/research/perceptual-tone-model/data/generated/realized-tone-blind-v1-20261019/private/packet-manifest.json`
- Validation: `/home/jacob/benma/research/perceptual-tone-model/data/generated/realized-tone-blind-v1-20261019/private/validation.json`

Open the HTML directly in a browser; it is self-contained and needs no server.
The `qa/` directory contains only that HTML, while all analyst artifacts live in
the separate `private/` directory. Share only the HTML for first-pass review. If
serving locally, expose only `qa/`, never the repository or its parent directory.
No human review JSON has been fabricated or written in Downloads. The browser
proposes the exact filename; the reviewer selects the Downloads location when saving.

**Reviewer instructions.** Enter your name. On every item, first finish playing
**TONE-BEARING TARGET**. Use **WHOLE TARGET** if needed; it unlocks after primary
playback. Answer **WHAT TONE FAMILY DOES THIS AUDIO MOST SOUND LIKE?** Choose
T1 — high / level; T2 — rising; T3 — low / dipping / low-rising; T4 — falling;
NEUTRAL / WEAK; or UNCLEAR / CANNOT TELL. Choose confidence 1–5. Optionally record
CLEAR, BORDERLINE or UNUSABLE acoustic usability. Judge what was actually heard.
The page explicitly says: **“If it sounds like T2 even if you think the speaker
probably meant T3, choose T2.”** Do not infer intended Mandarin or mentally correct
pronunciation. Save a draft to pause; resume via JSON or browser storage. After all
52 items, export the completed review to the exact path above.

Exports contain only schema, packet version/hash, reviewer, opaque annotation IDs,
perceived tone, confidence, usability, both heard flags, and per-item timestamps.
Tone-bearing playback, tone choice, confidence and reviewer name are required;
whole-target playback and usability are optional. Unchanged repeated exports and
JSON import/export round trips are byte-identical. Timestamps change only when an
item's review content changes. Wrong packet hashes, item IDs, extra fields, invalid
labels/confidence/timestamps and incomplete completed exports are rejected. The
Python validator performs schema checks only and never reads the hidden key.

**Visible leakage audit.** PASS. HTML payload fields are allowlisted. There are no
Hanzi, pinyin, phrase, lexical/surface labels, model results, historical results,
learner/control/repeat roles, source/take IDs, original filenames, repository paths,
seed, hidden-key references, or source-navigation links in the page. WAVs contain
only format and PCM data chunks. Both sources use the same delivery format: mono
PCM16 at 16 kHz, fixed polyphase resampling where needed, with no normalization,
denoising, sentence context, pitch or duration manipulation. The source spans are
unchanged. Content Security Policy blocks network connections; browser inspection
recorded zero external requests. Audio itself may reveal voice/syllable identity or
repeat familiarity; metadata blinding cannot prevent recognition or independent
filesystem access by a person who already owns the repository.

**Validation and production freeze.** Twelve focused Python tests pass: exact
learner inclusion and quarantine exclusion; control eligibility/class/speaker/source
balance; ownership/voicing/clipping rejection; opaque IDs and repeat spacing;
deterministic randomization; identical repeated audio; poisoned expected/model
metadata yielding identical selection/order; hidden-key separation; visible-page
leakage injection rejection; export schema/round trip and neutral preservation;
byte-identical full packet regeneration/hash stability; and production preservation.
Disposable Chromium tests decode all 104 audio views, exercise real playback and
listening order, exclusive playback, completion gates, optional fields, neutral and
unclear answers, deterministic downloads, Python validation of browser exports,
invalid import rejection, browser resume and 390/1280 px layouts. Synthetic test
responses were confined to a disposable browser/profile and temporary files.
The initial browser launch needed a sandbox exception for its local test socket.
Ruff, Node syntax checks, tracked/untracked whitespace checks and `git diff --check`
pass. No expensive training or native model evaluations were rerun.

All **413 deterministic baseline hashes** and **19,012 preexisting files** from the
starting snapshot remain unchanged. Production pronunciation inference, grading,
app UI, APIs and deployment are unchanged. No training, retraining, adaptation,
calibration, learner evaluation, commit, push or deployment occurred.

New research source/doc files in this continuation (existing untracked work retained):

- `perceptual_tone/blind_packet.py`
- `perceptual_tone/blind_key.py`
- `scripts/blind_packet.py`
- `scripts/blind_key.py`
- `scripts/blind_review.html`
- `scripts/blind_review.js`
- `scripts/blind_review_smoke.cjs`
- `scripts/blind_verify.py`
- `tests/test_blind_packet.py`
- `realized-tone-blind-analysis-plan.md`
- `realized-tone-blind-packet-report.md`

Generated research files are confined to
`data/generated/realized-tone-blind-v1-20261019/`: the HTML, starting-state snapshot,
selection and selection seal, manifest, private key, leakage audit, test logs,
browser preview, artifact seal and validation record. No prior artifact was edited.

**Exact next step after human review.** In the next continuation, validate the
completed Downloads export against this packet version/hash and all 52 IDs; preserve
and hash its original bytes; then join with the hidden key. First evaluate native
control reliability and repeat consistency using the preregistered
[interpretation plan](realized-tone-blind-analysis-plan.md). If credibility is
insufficient, report solo labels as insufficient and seek independent review. Only
after that gate may the next continuation describe the 16 learner percepts and
compare frozen expanded/pilot results, preserving human-neutral items separately.
Do not perform those analyses in this pass.
