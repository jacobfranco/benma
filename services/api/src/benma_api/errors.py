"""Stable public error taxonomy."""

from __future__ import annotations


class BenmaError(Exception):
    code = "internal_failure"
    status_code = 500

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable


class AuthenticationError(BenmaError):
    code = "authentication_error"
    status_code = 401


class AuthorizationError(BenmaError):
    code = "authorization_error"
    status_code = 404


class InvalidAudioError(BenmaError):
    code = "invalid_audio"
    status_code = 422


class NoSpeechError(BenmaError):
    code = "no_speech"
    status_code = 422


class InvalidTargetError(BenmaError):
    code = "invalid_pronunciation_target"
    status_code = 422


class InvalidConversationTurnError(BenmaError):
    code = "invalid_conversation_turn"
    status_code = 422


class ProviderUnavailableError(BenmaError):
    code = "provider_unavailable"
    status_code = 503


class ProviderTimeoutError(BenmaError):
    code = "provider_timeout"
    status_code = 504


class ProviderRejectedError(BenmaError):
    code = "provider_rejected_request"
    status_code = 502


class ProviderMalformedResponseError(BenmaError):
    code = "provider_malformed_response"
    status_code = 502


class AnalysisUnsupportedError(BenmaError):
    code = "analysis_unsupported"
    status_code = 422
