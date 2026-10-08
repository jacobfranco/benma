# Proposed research contract: ObservedSpeechUnit

Design only: no new production phone recognizer, endpoint or populated sound hypothesis in this pass. Unit boundaries need not be known, and a unit need not be a whole syllable. **No character or valid Chinese word is required.** Null means unresolved; empty candidates do not mean a sound was absent.

```typescript
type EvidenceRef = {
  evidence_id: string;
  producer: string;
  producer_version: string;
  configuration_sha256: string;
  audio_sha256: string;
  source: 'waveform' | 'model_output' | 'provider_payload' | 'manual_annotation';
  conditioning: 'audio_only' | 'lexical_reference' | 'intended_target';
};
type Confidence = {
  level: 'moderate' | 'low' | 'unresolved';
  probability: number | null;       // Only when calibrated; bounded [0,1]
  calibration_id: string | null;
};
type ObservedSpeechUnit = {
  id: string;
  index: number;                    // Stable audio-order identity, not a character index
  utterance_id: string;
  audio_sha256: string;
  granularity: 'acoustic_region' | 'phone_candidate' | 'syllable_candidate' | 'unresolved';
  timing: null | {
    start_seconds: number;
    end_seconds: number;
    provenance: EvidenceRef[];
    kind: 'independent_acoustic' | 'manual_acoustic' | 'lexical_alignment';
    confidence: Confidence;
  };
  pitch: {
    observed_gesture: 'level' | 'rising' | 'dipping' | 'falling' | 'unclear';
    confidence: Confidence;
    reason: string;
    quality: {
      retained_frames: number | null;
      total_frames: number | null;
      contamination_fraction: number | null;
      tracker_unstable: boolean | null;
    };
    measurement_refs: EvidenceRef[];
    classifier_ref: EvidenceRef | null;
  };
  segmental: {
    status: 'unresolved' | 'hypotheses';
    candidates: Array<{
      representation: 'ipa' | 'model_phone_symbols' | 'pinyin_like';
      inventory_id: string;          // A named phone inventory / spelling convention
      sequence: string[];            // Nonsense combinations remain legal
      confidence: Confidence;
      evidence_refs: EvidenceRef[];
      derivation: null | { from_candidate_id: string; mapping_version: string };
      candidate_id: string;
    }>;
    evidence_refs: EvidenceRef[];    // Can reference embeddings/posteriors without a label
  };
  lexical_links: Array<{
    interpretation_id: string;
    link_id: string;                 // Many-to-many alignment owned by interpretation layer
  }>;
  evidence_refs: EvidenceRef[];
  supersedes_unit_id: string | null; // Append revisions; never silently rewrite evidence
};

type LexicalInterpretation = {
  id: string;
  text: string;
  provenance: EvidenceRef[];
  links: Array<{
    id: string;
    observed_unit_ids: string[];
    character_start: number;
    character_end: number;
    confidence: Confidence;
  }>;
};
```

An independent path cannot carry segmental candidate evidence conditioned on lexical references or the target. Reference-conditioned alignments are allowed only with their explicit timing kind, so legacy evidence can coexist without being misrepresented as independent. Alternative boundary hypotheses receive their own unit-set/run IDs; this initial unit object does not force one hypothesis to overwrite another. Missing timing prohibits fabricated duration or pitch attribution. Measured F0 remains in evidence storage, with original seconds and immutable hashes, rather than giant arrays duplicated into every unit.

Reference pronunciation and intended target have their own records and comparison links. They are deliberately absent from the observed-unit evidence object. A pitch confidence is distinct from segmental confidence and timing confidence; a strong falling gesture cannot make a weak `zhou-ish` candidate certain. Pinyin-like spelling is an explicitly derived acoustic hypothesis, not dictionary pinyin copied from ASR.

## Illustrative future state, not a result from the latest recording

| Layer | First unit | Second unit |
|---|---|---|
| Audio-only segmental hypothesis | `gui-ish`, low, decoder provenance required | `zhou-ish`, low, decoder provenance required |
| Observed pitch | dipping, with its own evidence | falling, with its own evidence |
| Optional lexical interpretation | 贵 | 州 |
| Optional reference | guì / T4 | zhōu / T1 |
| Optional intended target | 广 | 州 |

This hypothetical state is valid even when no lexical interpretation is available. It does not describe the latest 贵/州 audit, which returned level-like/unclear. The current implementation must not emit these invented sound labels.

## Truth invariants

1. Observed units never require characters, pinyin, a dictionary entry or a valid word.
2. Lexical interpretation cannot mutate waveform, timing provenance, observed pitch or segmental evidence.
3. Intended target cannot enter extraction, segmentation or candidate generation in an independent observation path.
4. Multiple lexical interpretations may link to the same units, and links may be many-to-many.
5. Unresolved segmental identity and unresolved timing are valid first-class outcomes.
6. Pitch gesture is acoustic, not lexical-tone identification. A valley is not automatically correct T3.
7. `gui-ish`-style labels require an explicit acoustic producer, inventory/mapping and uncertainty. ASR pinyin is not sufficient provenance.
8. Nonsense syllable sequences are valid observations and cannot be rejected solely for lexical implausibility.
9. Reference-conditioned phones may be stored as reference evidence, never relabeled detected sounds.
10. No equal timing split or character boundary is introduced merely to fill the schema.
11. Confidence dimensions stay separate; no overall correct/wrong pronunciation grade follows from their presence.
12. Evidence revisions append immutable provenance. Product summaries may change without rewriting the source recording or prior interpretation.

## One bounded next step

**Implement a research-only, validation-tested ObservedSpeechUnit adapter for the already-cached waveform encoder's unpooled frame sequence.** Input is canonical audio and configuration only; output carries original-time frame-region evidence references, `granularity=acoustic_region`, null segmental hypotheses, and no lexical links. Include nonsense/unlinked, multiple-interpretation and target-independence fixtures. Do not call these frame regions syllables or phones.

This is the smallest credible next boundary toward independent segmental observation available with the installed capabilities. It makes independent temporal evidence attachable without inventing sound identities or obtaining a model. The deliverable is one offline interface/adapter, not a new recognizer or large research program. A future validated phone decoder can populate candidates through the same boundary.
