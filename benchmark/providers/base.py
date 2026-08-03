"""Separate provider contracts for separate evidence types."""

from __future__ import annotations

from abc import ABC, abstractmethod

from benchmark.models import (
    AcousticAnalysisResult,
    AlignmentResult,
    KnownTargetAssessmentRequest,
    KnownTargetAssessmentResult,
    UnknownTargetPerceptionRequest,
    UnknownTargetPerceptionResult,
)


class ProviderAdapterError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False, code: str | None = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.code = code


class MissingCredentialsError(ProviderAdapterError):
    pass


class MalformedProviderResponseError(ProviderAdapterError):
    pass


class UnsupportedConfigurationError(ProviderAdapterError):
    pass


class UnknownTargetPerceptionProvider(ABC):
    provider_name: str
    product_name: str
    adapter_version: str = "1.0.0"

    @abstractmethod
    def perceive(
        self, request: UnknownTargetPerceptionRequest
    ) -> tuple[UnknownTargetPerceptionResult, object]:
        """Return normalized evidence and untouched JSON-compatible provider response."""


class KnownTargetPronunciationProvider(ABC):
    provider_name: str
    product_name: str
    adapter_version: str = "1.0.0"

    @abstractmethod
    def assess(
        self, request: KnownTargetAssessmentRequest
    ) -> tuple[KnownTargetAssessmentResult, object]:
        """Assess speech with explicit target knowledge."""


class PitchAnalyzer(ABC):
    algorithm_name: str
    algorithm_version: str

    @abstractmethod
    def analyze(self, audio_path: str) -> AcousticAnalysisResult:
        """Extract acoustic evidence without assigning lexical tones."""


class ForcedAligner(ABC):
    algorithm_name: str
    algorithm_version: str

    @abstractmethod
    def align(self, audio_path: str, transcript: str) -> AlignmentResult:
        """Align known text to audio while exposing uncertainty/warnings."""
