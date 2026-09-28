"""Sample-level views of the three gaps; no inferred F0 or phonetic boundaries."""

import json

import numpy as np
from bakeoff import CORPUS, OUT
from benma_api.pronunciation.acoustics import _pcm16_mono

ma = next(r for r in json.loads((OUT / "forensics.json").read_text()) if r["target"] == "马")
rate, samples = _pcm16_mono(CORPUS / (ma["utterance_id"] + ".wav"))
values = np.array(samples)
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1250" height="810">',
    '<rect width="100%" height="100%" fill="white"/>',
    "<style>text{font:14px sans-serif;fill:#243347}</style>",
    '<text x="45" y="30">Fresh 马 — actual PCM samples around each pitch gap (pink)</text>',
    '<text x="45" y="54">Connected sample waveform; no pitch interpolation. Different vertical scales. Dashed = missing-frame centers.</text>',
]
for i, gap in enumerate(ma["gaps"]):
    lo, hi = gap["left_seconds"] - 0.025, gap["right_seconds"] + 0.025
    top, h, left, width = 115 + i * 230, 145, 90, 1090
    start, end = round(lo * rate), round(hi * rate)
    peak = float(np.max(abs(values[start:end])))

    def x(t):
        return left + (t - lo) / (hi - lo) * width

    def y(v):
        return top + h / 2 - v / peak * (h / 2 - 5)

    gs, ge = gap["first_missing_center"] - 0.005, gap["last_missing_center"] + 0.005
    parts.extend(
        [
            f'<text x="{left}" y="{top - 16}">Gap {i + 1}: {gap["missing_frames"]} missing frames; amplitude ±{peak:.4f}</text>',
            f'<rect x="{left}" y="{top}" width="{width}" height="{h}" fill="#fafcff" stroke="#ccd"/>',
            f'<rect x="{x(gs)}" y="{top}" width="{x(ge) - x(gs)}" height="{h}" fill="#fdd"/>',
        ]
    )
    coordinates = " ".join(f"{x(j / rate):.2f},{y(values[j]):.2f}" for j in range(start, end))
    parts.append(
        f'<polyline fill="none" stroke="#365570" stroke-width="1" points="{coordinates}"/>'
    )
    for t in np.arange(gap["first_missing_center"], gap["last_missing_center"] + 0.001, 0.01):
        parts.append(f'<path d="M{x(t)},{top}v{h}" stroke="#d66" stroke-dasharray="2 4"/>')
    for t in np.arange(np.ceil(lo * 100) / 100, hi, 0.01):
        parts.append(f'<text x="{x(t) - 15}" y="{top + h + 20}">{t:.2f}</text>')
parts.append("</svg>")
(OUT / "ma-waveform-zooms.svg").write_text("\n".join(parts) + "\n")
