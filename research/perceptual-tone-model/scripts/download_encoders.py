#!/usr/bin/env python3
"""Explicit one-time network setup; experiment commands remain local-only."""

import json
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from huggingface_hub import snapshot_download

root = Path(__file__).resolve().parents[1]
for config in json.loads((root / "configs/encoders.json").read_text()).values():
    print(
        snapshot_download(
            config["model_id"],
            revision=config["revision"],
            cache_dir=root / ".cache/huggingface",
            allow_patterns=["config.json", "preprocessor_config.json", "pytorch_model.bin"],
        )
    )
