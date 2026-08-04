"""Generate an explicit local Azure Mandarin voice-listening bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from benma_api.config import get_settings
from benma_api.pronunciation.reference import (
    AzureReferenceSpeechProvider,
    ReferenceSpeechRequest,
)

TARGETS = (
    "妈",
    "麻",
    "马",
    "骂",
    "买",
    "卖",
    "水",
    "睡",
    "生活",
    "后面",
    "睡觉",
    "你好",
    "很好",
    "可以",
    "不知道",
    "一个",
    "不是",
)
DEFAULT_VOICES = (
    "zh-CN-Xiaochen:DragonHDLatestNeural",
    "zh-CN-Yunfan:DragonHDLatestNeural",
    "zh-CN-XiaoxiaoNeural",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--voice", action="append", dest="voices")
    args = parser.parse_args()
    settings = get_settings()
    if settings.azure_speech_key is None or settings.azure_speech_region is None:
        raise SystemExit(
            "Azure Speech credentials are required; no fixture audio will be generated"
        )
    provider = AzureReferenceSpeechProvider(
        settings.azure_speech_key.get_secret_value(), settings.azure_speech_region
    )
    voices = tuple(args.voices or DEFAULT_VOICES)
    args.output.mkdir(parents=True, exist_ok=True)
    rows: list[str] = []
    for voice_index, voice in enumerate(voices):
        for target_index, target in enumerate(TARGETS):
            name = f"v{voice_index + 1:02}-t{target_index + 1:02}.wav"
            result = provider.synthesize(
                ReferenceSpeechRequest(
                    text=target,
                    locale="zh-CN",
                    voice=voice,
                    model_version="listening-candidate",
                    rate="0%",
                    timeout_seconds=30,
                )
            )
            (args.output / name).write_bytes(result.audio)
            rows.append(
                f"<tr><td>{target}</td><td>{voice}</td>"
                f'<td><audio controls preload="none" src="{name}"></audio></td>'
                "<td contenteditable></td></tr>"
            )
    html = (
        "<!doctype html><meta charset='utf-8'><title>Benma reference listening</title>"
        "<h1>Benma reference listening</h1>"
        "<p>Listen for Standard Mandarin naturalness, tones, sandhi, neutral tone, and pacing. "
        "This is not a statistical provider ranking.</p>"
        "<table border='1' cellpadding='8'><tr><th>Target</th><th>Voice</th>"
        f"<th>Audio</th><th>Notes</th></tr>{''.join(rows)}</table>"
    )
    (args.output / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote {len(rows)} listening samples to {args.output / 'index.html'}")


if __name__ == "__main__":
    main()
