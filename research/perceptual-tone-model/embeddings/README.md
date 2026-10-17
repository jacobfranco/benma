# Frozen pretrained encoder abstraction

Both checkpoints are pinned in [`configs/encoders.json`](../configs/encoders.json):

| Encoder | Immutable revision | Input / output |
| --- | --- | --- |
| [Tencent Chinese HuBERT base](https://huggingface.co/TencentGameMate/chinese-hubert-base/tree/fce0375452b1dd6c080ac3248d423d4d037bc831) | `fce0375452b1dd6c080ac3248d423d4d037bc831` | 16 kHz, normalized waveform, 768 dimensions |
| [Microsoft WavLM Base+](https://huggingface.co/microsoft/wavlm-base-plus/tree/4c66d4806a428f2e922ccfa1a962776e232d487b) | `4c66d4806a428f2e922ccfa1a962776e232d487b` | 16 kHz, model's unnormalized waveform recipe, 768 dimensions |

Revisions were resolved from the publishers' Hugging Face API on 2026-10-15;
preprocessing is checked against each pinned `preprocessor_config.json` at load.
Exact downloaded file hashes are retained in every embedding metadata record.
These are representation candidates, not trained acceptability graders.

`FrozenEncoder` loads only the local pinned snapshot, sets eval/inference mode,
disables all gradients and uses float32. Default layer is transformer layer 9
(`hidden_states[9]`, with projection at index 0). This is a starting configuration,
not a claim that layer 9 is best; change the registry in a recorded experiment to
test another layer. Device and thread count are configured and recorded. CPU is
the validated reference runtime; CUDA is available but not validated in this pass.

Choose either `local` or `wide` input view and `target_mean`, `context_mean`, or
`target_context_concat` pooling. The last concatenates target and whole-context
means (1536 dimensions). Target pooling uses convolutional receptive-field centers
in original sample coordinates, not evenly spaced approximations. A target with
no encoder frame center fails and needs segmentation review. Contextual hidden
states still contain surrounding speech information when target pooling is used.

Cache keys include decoded window content, exact model/revision and model-file
hashes, sample rate/preprocessing, layer, pooling/view, target-relative samples,
implementation hash, dependency/runtime versions and device. Entries store NPY
vectors plus JSON metadata and a vector checksum. Identical requests reuse the
vector without loading/inferencing the model. Incomplete/corrupt entries fail;
remove just that ignored cache entry and recompute. Model downloads occur only
through the explicit setup script; experiments use `local_files_only=True`.

`.cache/huggingface/` holds weights and `embeddings/generated/` holds vectors.
Both are ignored. WavLM currently emits a PyTorch mask-type deprecation warning
with this pinned dependency combination; real extraction passed. No fine-tuning,
remote inference, model publishing or production integration is performed.
