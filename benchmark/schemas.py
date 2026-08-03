"""Export JSON Schema snapshots for non-Python tooling and corpus review."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from benchmark.models import (
    AcousticAnalysisResult,
    BenchmarkSample,
    CorpusManifest,
    HumanListenerAnnotation,
    KnownTargetAssessmentRequest,
    KnownTargetAssessmentResult,
    ProviderRun,
    UnknownTargetPerceptionRequest,
    UnknownTargetPerceptionResult,
)
from benchmark.storage import write_json

EXPORTED_MODELS: dict[str, type[BaseModel]] = {
    "benchmark-sample.schema.json": BenchmarkSample,
    "corpus-manifest.schema.json": CorpusManifest,
    "unknown-target-request.schema.json": UnknownTargetPerceptionRequest,
    "unknown-target-result.schema.json": UnknownTargetPerceptionResult,
    "known-target-request.schema.json": KnownTargetAssessmentRequest,
    "known-target-result.schema.json": KnownTargetAssessmentResult,
    "acoustic-analysis.schema.json": AcousticAnalysisResult,
    "human-listener-annotation.schema.json": HumanListenerAnnotation,
    "provider-run.schema.json": ProviderRun,
}


def export_json_schemas(output_dir: Path) -> int:
    for filename, model in EXPORTED_MODELS.items():
        write_json(output_dir / filename, model.model_json_schema(mode="serialization"))
    return len(EXPORTED_MODELS)
