"""Small structured logging configuration with no payload/token logging."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in (
            "request_id",
            "account_id",
            "utterance_id",
            "run_id",
            "provider",
            "status",
            "status_code",
            "reading_ms",
            "pitch_ms",
            "alignment_ms",
            "contour_ms",
            "persistence_commit_ms",
            "total_ms",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = str(value)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
