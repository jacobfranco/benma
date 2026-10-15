"""Research-only acceptance proposal. No production imports or transcript heuristics."""

from __future__ import annotations

from typing import Any


def candidate_acceptance(
    *, no_speech: bool, response: dict[str, Any] | None, request_ok: bool = True
) -> tuple[str, str]:
    if no_speech:
        return "RETRY", "acoustic_absence"
    if not request_ok or response is None:
        return "UNKNOWN", "preflight_failed"
    languages = response.get("languages")
    if not isinstance(languages, list) or not languages:
        return "UNKNOWN", "no_reliable_language"
    if any(
        not isinstance(item, dict) or not isinstance(item.get("code"), str) for item in languages
    ):
        return "UNKNOWN", "malformed_language_metadata"
    codes = {item["code"].lower() for item in languages}
    if codes <= {"zh", "cmn"}:
        return "ACCEPT", "mandarin_detected_not_acoustically_absent"
    if len(codes) == 1:
        return "RETRY", "non_mandarin_detected"
    return "UNKNOWN", "multiple_detected_languages"
