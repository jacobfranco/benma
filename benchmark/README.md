# Benchmark package

`benchmark` is the executable research subsystem. Its dependency direction is deliberate:

```text
corpus + immutable schemas
        ↓
separate provider contracts → raw + normalized ProviderRun
        ↓
evaluation metrics + dated cost assumptions
        ↓
machine-readable and Markdown reports
```

The calibration layer adds explicit evidence origin, rater profiles, human consensus classes,
immutable stratified splits, count/interval FAR and FRR, exploratory thresholds, transparent
fusion rules, provider lifecycle/scope, and acoustic/alignment comparison tools. The browser
annotator hides descriptive sample IDs behind opaque audio tokens. None of this converts fixtures
into real evidence.

Unknown-target requests cannot carry target/context. Known-target requests can. Experimental
context probes are a third, research-only type and cannot be sent through the production provider
contract. See the root README and `docs/benchmark/running.md` for commands.
