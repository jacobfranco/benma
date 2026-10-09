"""Canonical playback is the same private utterance resource, never a path API."""

from __future__ import annotations

import hashlib
import io
import uuid
import wave

import pytest
from conftest import ApiClient, wav_bytes


def test_canonical_selector_preserves_original_and_returns_exact_owned_asset(
    client: ApiClient, auth_header: dict[str, str]
) -> None:
    original = wav_bytes(sample_rate=24000)
    uploaded = client.post(
        "/v1/utterances", headers=auth_header,
        files={"file": ("speech.wav", original, "audio/wav")},
    ).json()
    path = uploaded["audio_url"]
    for suffix in ("", "?canonical=false"):
        response = client.get(path + suffix, headers=auth_header)
        assert response.status_code == 200
        assert response.content == original
    response = client.get(path + "?canonical=true", headers=auth_header)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["cache-control"] == "private, no-store"
    assert hashlib.sha256(response.content).hexdigest() == uploaded["canonical_audio"]["sha256"]
    with wave.open(io.BytesIO(response.content)) as audio:
        assert (audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) == (16000, 1, 2)
    assert response.content != original


@pytest.mark.parametrize("canonical", ["false", "true"])
def test_audio_selectors_enforce_auth_and_ownership(
    client: ApiClient, auth_header: dict[str, str], uploaded_utterance: dict[str, object],
    canonical: str,
) -> None:
    path = f"{uploaded_utterance['audio_url']}?canonical={canonical}"
    assert client.get(path).status_code == 401
    other = client.post("/v1/dev/auth", json={"phone_number": "+12025550124"}).json()
    response = client.get(path, headers={"Authorization": f"Bearer {other['token']}"})
    assert response.status_code == 404
    assert "RIFF" not in response.text
    assert client.get(f"/v1/utterances/{uuid.uuid4()}/audio?canonical={canonical}",
                      headers=auth_header).status_code == 404


@pytest.mark.parametrize("path", [
    "/v1/utterances/not-a-uuid/audio?canonical=true",
    "/v1/utterances/%2e%2e%2fsecret/audio?canonical=true",
    "/v1/utterances/00000000-0000-0000-0000-000000000000/audio?canonical=/etc/passwd",
])
def test_selector_cannot_address_files(
    client: ApiClient, auth_header: dict[str, str], path: str
) -> None:
    assert client.get(path, headers=auth_header).status_code in (404, 422)
