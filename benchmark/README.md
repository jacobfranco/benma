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

Unknown-target requests cannot carry target/context. Known-target requests can. Experimental
context probes are a third, research-only type and cannot be sent through the production provider
contract. See the root README and `docs/benchmark/running.md` for commands.
