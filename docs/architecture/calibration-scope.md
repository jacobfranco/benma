# Calibration maturity and scope

Calibration maturity and calibration scope are independent axes.

| Maturity | Meaning |
|---|---|
| `RAW_EVIDENCE` | a provider/acoustic/human observation exists; no calibrated decision |
| `EXPERIMENTAL` | a transparent rule or threshold is being evaluated |
| `CALIBRATED` | an explicitly selected rule passed its declared real-data and held-out gates |

| Scope | Meaning |
|---|---|
| `NONE` | no threshold is promoted |
| `PERSONAL` | evidence supports only the identified learner/speaker and compatible capture conditions |
| `PILOT_POPULATION` | evidence supports only the documented multi-speaker pilot strata |
| `GENERAL` | a broader representative evaluation explicitly supports transfer; never inferred from a small pilot |

A one-learner threshold can become `CALIBRATED/PERSONAL`; it can never become `GENERAL` merely
because its held-out fraction looks good. Personal policies must record the pseudonymous speaker
ID and must not be applied to other accounts. Population promotion needs varied learners, L1s,
proficiency, pitch ranges, microphones, and conditions. General promotion requires a later,
representative campaign and a new ADR.

Provider lifecycle is a third axis. `LIVE_VALIDATED` means a real request returned; it says nothing
about calibration. `PILOT_EVALUATED` requires qualifying real audio. `CALIBRATED` requires the
human-supported, split, and promotion gates. Fixture/parser success cannot advance any of these.

Current repository state is `RAW_EVIDENCE/NONE`: zero real recordings, zero native annotations,
zero live provider responses, no threshold selection, and no held-out promotion. The server rejects
`BENMA_ENABLE_CATEGORICAL_TONE_JUDGMENT=true` regardless of development enthusiasm.
