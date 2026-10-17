# Phase A exclusion and coverage analysis

**These are data-pipeline errors/exclusions, not learned-model errors.** No model
was trained and no test predictions exist. Source: the immutable local
`data/generated/native-tone-phase-a-v3/` artifacts and
[`reports/native-feasibility-summary.json`](reports/native-feasibility-summary.json).

From 68 utterances / 640.6195 seconds, 2,210 Han syllables were considered.
Only **229 (10.36%)** are structural candidates. All remain quarantined pending QA.
**1,981 (89.64%)** were excluded; reasons overlap:

| Reason | Syllables |
| --- | ---: |
| Multi-Han word without verified syllable boundary | 1,615 |
| Unresolved lexical reading | 690 |
| Repeated prompt owned by another partition | 163 |
| Word interval duration/bounds rejected | 110 |
| T3 followed by unresolved reading | 60 |
| Unresolved T3 prosodic grouping | 57 |
| Ambiguous 一 grammatical context | 16 |
| Reduplication may reduce second tone | 11 |
| Cardinal 一 surface uncertain | 6 |
| Erhua / 儿 ownership uncertain | 5 |
| Quantity 个 reduction optional | 3 |

Duration screening is applied to original word spans even for multi-Han words;
the 110 count is not evidence that 110 genuine syllable alignments were wrong.
Likewise “candidate” means structurally plausible, not that the timing or label
has been confirmed by listening.

| Derived class | Train candidates | Validation candidates | Test candidates | Total |
| --- | ---: | ---: | ---: | ---: |
| T1 | 32 | 8 | 4 | 44 |
| T2 | 25 | 17 | 13 | 55 |
| T3 | 16 | 7 | 3 | 26 |
| T4 | 61 | 25 | 15 | 101 |
| NEUTRAL | 3 | 0 | 0 | 3 |
| Total | 137 | 57 | 35 | 229 |

The nominal split uses 21 conservative identifier groups; retained candidates
span 19 (12 train, 4 validation, 3 test). These are **not verified speaker counts**.
No cross-partition group, utterance, source PCM, prompt ID, or normalized duplicate
transcript occurs among the retained candidates. This does not establish that
all real speaker aliases were resolved.

| T3 subset | Retained candidates | Interpretation |
| --- | ---: | --- |
| Non-sandhi lexical/surface T3 | 26 | Weak labels only |
| Before T1 | 9 | Available |
| Before T2 | 11 | Available |
| Before T3 | 0 | Not covered; excluded contexts remain in manifest |
| Before T4 | 6 | Available |
| Before neutral | 0 | Not covered |
| Utterance-medial proxy | 26 | Not a verified prosodic phrase category |
| Utterance-final proxy | 0 | Not covered |
| Isolated T3 / verified phrase-final / verified phrase-medial | Unknown | No trustworthy category annotation |

This retention policy cannot answer the motivating connected-T3 question:
73.1% of all source syllables lack the required word-to-syllable mapping, only
three candidate test T3s survive, and neutral is entirely absent from both
held-out partitions. Fitting a five-class head or reporting a five-class score
would give a misleading picture. Fetching more of the same filtered material
would increase volume without demonstrating that the missing hard contexts are
handled correctly.

The linguistic audit also shows why reusing grader expectations without a
research filter would be unsafe: 看看 can reduce its second syllable, and a
cardinal-number 一 fallback need not match the realized tone. The research-only
wrapper now excludes those cases. It does not silently retune production.

The next technical repair is an auditable character/pinyin-to-phone ownership
mapping or a pinned local syllable aligner, matched to original corpus transcripts
and a trustworthy speaker registry. Then build a new 500–1,000-candidate Phase A
covering neutral and the missing T3 contexts, and complete its small audio QA
packet. A change to corpus, labels, alignment or split requires a new manifest
and run identity. Do not treat this quarantined split as a final benchmark.
