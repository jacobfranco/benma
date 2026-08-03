"""Small stdlib HTTP helpers so live adapters do not require an SDK."""

from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from benchmark.providers.base import ProviderAdapterError


def json_request(
    url: str,
    *,
    payload: dict[str, object] | None,
    headers: dict[str, str],
    timeout: float,
    method: str = "POST",
) -> object:
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    request = Request(url, data=data, method=method)
    for name, value in {"Content-Type": "application/json", **headers}.items():
        request.add_header(name, value)
    return _read_json(request, timeout)


def binary_request(url: str, *, payload: bytes, headers: dict[str, str], timeout: float) -> object:
    request = Request(url, data=payload, method="POST")
    for name, value in headers.items():
        request.add_header(name, value)
    return _read_json(request, timeout)


def multipart_request(
    url: str,
    *,
    fields: dict[str, str],
    file_field: str,
    file_path: Path,
    headers: dict[str, str],
    timeout: float,
) -> object:
    boundary = f"benma-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            ]
        )
    media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode(),
            f"Content-Type: {media_type}\r\n\r\n".encode(),
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    request = Request(url, data=b"".join(chunks), method="POST")
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    for name, value in headers.items():
        request.add_header(name, value)
    return _read_json(request, timeout)


def _read_json(request: Request, timeout: float) -> object:
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise ProviderAdapterError(
            f"provider HTTP {exc.code}: {body[:500]}",
            retryable=exc.code in {408, 409, 429} or exc.code >= 500,
            code=str(exc.code),
        ) from exc
    except (TimeoutError, URLError) as exc:
        raise ProviderAdapterError(str(exc), retryable=True) from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderAdapterError("provider returned non-JSON data") from exc
