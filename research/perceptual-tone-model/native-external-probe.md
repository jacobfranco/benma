# External Benma probe — no selected learned model

**Learned probe status: not run.** Selection on corpus validation/test data never
occurred, so there is no model and no legitimate `P(T1)…P(NEUTRAL)` distribution
to report. Existing Benma recordings were not used for training or selection.

For a read-only reference inventory, `native_baseline.cjs` replays the frozen
shape/family functions on all **53 archived acoustic units**. Its predictions
match the existing replay in the focused adapter test. This is saved-evidence
replay, not new ASR/alignment/F0 extraction. Full results are in
[`reports/native-external-baseline.json`](reports/native-external-baseline.json).

For 我 in the archived **我想买这个。** recording `89cee47e…`, the current frozen
baseline returns **T3**. Its family supports are T1=0.04638, T2=0, T3=0.88494,
T4=0.20213. These values are **not probabilities**, do not sum to one, and must
not be relabeled as calibrated confidence. Neutral has no acoustic-family output.
Two other Stage-0 recordings of that phrase (`cad88597…`, `4f1ab9ed…`) have saved
baseline outcomes abstain and T3 respectively; the unchanged Stage-0 replay
verifies those archived records too.

The broader archive still contains T4 decisions for 我:

| Recording prefix | Transcript | Frozen family decision |
| --- | --- | --- |
| `8faf1a90` | 我要一个苹果。 | T4 |
| `a5acd04c` | 我有一个苹果。 | T4 |
| `b9067bec` | 我想买 | Abstain; T4 support exceeds T3 but decision is unclear |

These files do not independently establish native perceptual correctness or
intentional wrong tones. They are useful future external probes. The particular
archived 我想买这个 example is not currently T4, so this pass does not repeat an
older classification as if it were the frozen baseline's current output.

**Whether a learned model fixes natural 我 being heard as T4 remains unanswered.**
There are no learned probabilities, contrast-test results, or grading changes.
