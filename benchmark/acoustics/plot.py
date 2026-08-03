"""Dependency-free static SVG waveform/F0 research plots."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from benchmark.acoustics.pitch import _pcm16_mono
from benchmark.models import AcousticAnalysisResult, AlignmentResult


def write_diagnostic_svg(
    audio_path: Path,
    analysis: AcousticAnalysisResult,
    output_path: Path,
    *,
    alignment: AlignmentResult | None = None,
    reference: AcousticAnalysisResult | None = None,
    title: str = "Benma acoustic diagnostic",
) -> None:
    rate, samples = _pcm16_mono(audio_path)
    duration = len(samples) / rate if rate else 1.0
    width, height = 1200, 620
    left, right = 70, 30
    plot_width = width - left - right

    def x(seconds: float) -> float:
        return left + min(1.0, max(0.0, seconds / duration)) * plot_width

    waveform: list[str] = []
    bins = min(1000, len(samples))
    for index in range(bins):
        start = index * len(samples) // bins
        end = max(start + 1, (index + 1) * len(samples) // bins)
        peak = max(abs(value) for value in samples[start:end])
        waveform.append(f"{x(start / rate):.2f},{170 - peak * 110:.2f}")
    voiced = [
        point.normalized_semitones
        for point in analysis.f0
        if point.normalized_semitones is not None
    ]
    maximum = max([abs(float(value)) for value in voiced] or [1.0])
    if maximum < 1e-9:
        maximum = 1.0

    def y(value: float) -> float:
        return 420 - (value / maximum) * 120

    f0_segments: list[str] = []
    current: list[str] = []
    for point in analysis.f0:
        if point.normalized_semitones is None:
            if current:
                f0_segments.append(" ".join(current))
                current = []
            continue
        current.append(f"{x(point.timestamp_seconds):.2f},{y(point.normalized_semitones):.2f}")
    if current:
        f0_segments.append(" ".join(current))
    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfbf8"/>',
        f'<text x="{left}" y="36" font-family="sans-serif" font-size="22">{escape(title)}</text>',
        '<text x="20" y="170" font-family="sans-serif" font-size="13">wave</text>',
        f'<polyline points="{" ".join(waveform)}" fill="none" stroke="#536878" stroke-width="1"/>',
        '<line x1="70" y1="170" x2="1170" y2="170" stroke="#ccd1d4"/>',
        '<text x="20" y="420" font-family="sans-serif" font-size="13">F0 ST</text>',
        '<line x1="70" y1="420" x2="1170" y2="420" stroke="#ccd1d4"/>',
    ]
    for segment in f0_segments:
        svg.append(
            f'<polyline points="{segment}" fill="none" stroke="#b8332a" stroke-width="2.5"/>'
        )
    if reference is not None:
        reference_points = [
            f"{x(point.timestamp_seconds):.2f},{y(point.normalized_semitones):.2f}"
            for point in reference.f0
            if point.normalized_semitones is not None
        ]
        svg.append(
            f'<polyline points="{" ".join(reference_points)}" fill="none" '
            'stroke="#2b6f9f" stroke-dasharray="5 4" stroke-width="2"/>'
        )
    if alignment is not None:
        for unit in alignment.words:
            boundary_x = x(unit.span.start_seconds)
            svg.append(
                f'<line x1="{boundary_x:.2f}" y1="280" x2="{boundary_x:.2f}" y2="540" '
                'stroke="#777" stroke-dasharray="2 3"/>'
            )
            svg.append(
                f'<text x="{boundary_x + 3:.2f}" y="565" font-family="sans-serif" '
                f'font-size="13">{escape(unit.label)}</text>'
            )
    voiced_fraction = analysis.contour_features.get("voiced_fraction")
    voiced_label = f"{voiced_fraction:.1%}" if isinstance(voiced_fraction, float) else "n/a"
    svg.append(
        f'<text x="{left}" y="600" font-family="monospace" font-size="12">'
        f"{escape(analysis.pitch_algorithm)} · voiced {voiced_label}</text>"
    )
    svg.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg) + "\n", encoding="utf-8")
