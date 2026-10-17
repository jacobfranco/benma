# Offline baseline comparisons

| Model | Inputs |
| --- | --- |
| 0 | Frozen Benma learner grade: STRONG_MATCH→acceptable; PARTIAL_OR_WEAK→borderline; CLEAR_DIFFERENCE→incorrect; UNAVAILABLE→abstain |
| 1 | Benma numeric acoustics/prosody/reliability |
| 2 | Frozen speech embeddings |
| 3 | Speech embeddings + Benma numeric features |
| 4 | Speech embeddings + Benma features + linguistic context |

Models 1–4 each support multinomial logistic regression and a one-hidden-layer
32-unit MLP. The reference MLP uses scikit-learn's L-BFGS optimizer with L2
regularization and a fixed iteration cap. It does not create an internal random
syllable validation split. Convergence warnings are recorded. Numerical fitting
uses one BLAS thread; model seeds and all hyperparameters are recorded. The
always-acceptable sanity baseline detects apparent safety gains from never warning.

The target is acceptable/borderline/incorrect. Disputed, insufficiently annotated
and ungradable samples remain in the dataset but never train the classifier.
Training fails if its speakers lack any of the three classes, or a held-out
partition has no gradable consensus examples. Report per-class counts before
interpreting missing/rare classes in validation or test.

The first recipe uses argmax class predictions, optional confidence-based abstention
(disabled by default), and a predeclared 0.8 threshold for **reporting** confident
incorrect predictions. This does not change the frozen grader or any app threshold.
Probability calibration is measured, not fitted. Future operating-point selection
must use validation speakers only and be frozen before inspecting test results.
No automatic model/threshold search or test-set winner selection happens here.

Each run saves immutable config, split, dataset, feature matrices/schema, embedding
index, fitted pipelines, predictions, leakage checks, dependency versions, code
hashes and metrics. Artifacts live under ignored run directories. Joblib files are
local fitted artifacts; only load ones created by this research workflow.
