"""Dependency-free offline SVG artifacts; every display-only line is dashed.

No plotting package is installed in the local environments. SVG keeps this pass
offline and portable, with text labels and no rasterization/font dependency.
"""

import html
import math
import statistics


def esc(value):
    return html.escape(str(value), quote=True)


class SVG:
    def __init__(self, width, height):
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/>'
            "<style>text{font-family:sans-serif;font-size:12px} "
            ".title{font-size:18px;font-weight:bold}</style>"
        ]

    def text(self, x, y, value, color="#253447", cls=""):
        self.parts.append(f'<text x="{x}" y="{y}" fill="{color}" class="{cls}">{esc(value)}</text>')

    def line(self, points, color, dashed=False, width=1.8, dots=False):
        if not points:
            return
        if len(points) > 1:
            coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
            dash = ' stroke-dasharray="5 4"' if dashed else ""
            self.parts.append(
                f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
                f'stroke-width="{width}"{dash}/>'
            )
        if dots or len(points) == 1:
            for x, y in points:
                self.parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2" fill="{color}"/>')

    def panel(self, top, label, duration, low, high, height=132):
        left, right = 80, 1050
        self.text(left, top - 10, label)
        for fraction in (0, 0.25, 0.5, 0.75, 1):
            y = top + height * (1 - fraction)
            value = low + (high - low) * fraction
            self.line([(left, y), (right, y)], "#e1e6eb", width=0.7)
            self.text(10, y + 4, f"{value:.3g}")
            x = left + (right - left) * fraction
            self.text(x - 10, top + height + 18, f"{duration * fraction:.2f}")
        return lambda t, v: (
            left + (right - left) * t / duration,
            top + height * (1 - (v - low) / max(high - low, 1e-9)),
        )

    def spans(self, spans, xy, low, high):
        for span in spans:
            x, y = xy(span["start"], high)
            x2, y2 = xy(span["end"], low)
            self.parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{x2 - x:.2f}" '
                f'height="{y2 - y:.2f}" fill="#e8acac" opacity="0.19"/>'
            )

    def save(self, path):
        path.write_text("\n".join([*self.parts, "</svg>"]))


def measured_lines(svg, points, key, xy, color, dots=False):
    segment = []
    for p in points:
        value = p.get(key)
        if value is None:
            svg.line(segment, color, dots=dots)
            segment = []
        else:
            segment.append(xy(p["timestamp_seconds"], value))
    svg.line(segment, color, dots=dots)


def plot_clip(path, clip, row):
    svg = SVG(1100, 1080)
    pred = clip["wav2vec"]
    probability = pred[f"p_T{pred['prediction']}"]
    svg.text(
        35,
        28,
        f"{row['text']} {row['pinyin']} | lexical T{row['tone']} | "
        f"wav2vec T{pred['prediction']} p={probability:.3f}",
        cls="title",
    )
    svg.text(
        35,
        50,
        f"{row['source_asset_id']} | Benma: {row['v1_category']}, "
        f"{row['v1_confidence']}, {row['v1_reason']} | research whole-clip timing",
    )
    svg.text(
        35,
        70,
        "Gray dots: pre-energy-gate tracker; blue: raw gated F0; "
        "green: retained original F0; pink: missing raw F0.",
    )
    raw = clip["acoustics"]["f0"]
    duration = clip["duration_seconds"]
    filtered = clip["filtered_measured_frames"]
    region = clip["evidence_region"]
    high = max(350, max(p.get("tracker_f0_hz") or 0 for p in raw) * 1.1)
    xy = svg.panel(
        110,
        "F0 (Hz). Vertical dotted bounds: selected evidence region; no octave correction.",
        duration,
        40,
        high,
    )
    svg.spans(clip["missing_spans"]["raw"], xy, 40, high)
    for p in raw:
        if p["tracker_f0_hz"]:
            svg.line([xy(p["timestamp_seconds"], p["tracker_f0_hz"])], "#aaa")
    measured_lines(svg, raw, "f0_hz", xy, "#2473b8", True)
    measured_lines(svg, filtered, "f0_hz", xy, "#178453", True)
    for bound in (region["start"], region["end"]):
        svg.line([xy(bound, 40), xy(bound, high)], "#555", True)
    baseline = clip["full_display_contour"]["baseline_hz"]
    same_baseline = [
        {
            "timestamp_seconds": p["timestamp_seconds"],
            "st": 12 * math.log2(p["f0_hz"] / baseline) if p["f0_hz"] and baseline else None,
        }
        for p in raw
    ]
    vals = [p["st"] for p in same_baseline if p["st"] is not None]
    low, high_st = min(-6, min(vals, default=0) - 1), max(6, max(vals, default=0) + 1)
    xy = svg.panel(
        310,
        "Semitones: blue raw on retained median baseline; "
        "green production median-smoothed evidence.",
        duration,
        low,
        high_st,
    )
    svg.spans(clip["missing_spans"]["filtered"], xy, low, high_st)
    measured_lines(svg, same_baseline, "st", xy, "#2473b8", True)
    measured_lines(svg, filtered, "smoothed_semitones", xy, "#178453", True)
    ui = clip["drawer_projection"]
    display = ui["normalized_primary_contour"]
    extent = display["maximum_semitones"]
    xy = svg.panel(
        510,
        "Drawer Mine: purple DASHED = display geometry only (recentered). "
        "Orange = canonical reference ONLY.",
        duration,
        -extent,
        extent,
    )
    svg.spans(clip["missing_spans"]["raw"], xy, -extent, extent)
    for segment in display["segments"]:
        svg.line(
            [xy(p["timestamp_seconds"], p["normalized_semitones"]) for p in segment],
            "#8a42b0",
            True,
            dots=True,
        )
    points = [p for s in display["segments"] for p in s]
    if points:
        first, last = points[0]["timestamp_seconds"], points[-1]["timestamp_seconds"]
        heights = ui["canonical_heights_reference_only"]
        center = statistics.median(heights)
        svg.line(
            [
                xy(first + (last - first) * i / (len(heights) - 1), (v - center) * 6)
                for i, v in enumerate(heights)
            ],
            "#ca7a1b",
            True,
        )
    svg.text(
        80,
        682,
        "Canonical reference uses arbitrary teaching amplitude; never fitted to audio. "
        "Mobile fits Mine horizontally to voiced span.",
    )
    peak_rms = max(p["energy_rms"] for p in raw)
    xy = svg.panel(
        730,
        "Energy envelope: 40-ms RMS (black); dashed red = existing energy gate; "
        "gray = diagnostic active threshold.",
        duration,
        0,
        peak_rms * 1.1,
        100,
    )
    measured_lines(svg, raw, "energy_rms", xy, "#333")
    for gate, color in (
        (clip["acoustics"]["energy_gate"]["threshold_rms"], "#b04141"),
        (row["active_gate_rms"], "#999"),
    ):
        svg.line([xy(0, gate), xy(duration, gate)], color, True)
    xy = svg.panel(
        900,
        "Praat selected-candidate autocorrelation strength "
        "(NOT calibrated voice probability or a creak measure).",
        duration,
        0,
        1,
        100,
    )
    measured_lines(svg, raw, "voicing_probability", xy, "#856016", True)
    svg.line([xy(0, 0.45), xy(duration, 0.45)], "#999", True)
    svg.text(940, 1045, "time (seconds) →")
    svg.save(path)


def comparison_plot(output, rows):
    metrics = [
        ("voiced_fraction", "F0 coverage (all tracker frames)"),
        ("active_missing_fraction", "Missing F0 in energy-active frames"),
        ("f0_median_hz", "Median tracked F0 (Hz)"),
        ("classifier_maximum_tracker_jump_st", "Max tracker jump (st, production definition)"),
        ("raw_st_middle_to_final", "Middle → final third F0 (st)"),
        ("active_periodicity_mean", "Mean active-frame periodicity"),
        ("classifier_voiced_duration_seconds", "Retained voiced duration (s)"),
        ("energy_end_start_ratio", "Ending / onset active-span RMS"),
    ]
    svg = SVG(1100, 1220)
    svg.text(
        35, 28, "All 13 T3 versus all 21 T4: descriptive distributions, one speaker", cls="title"
    )
    svg.text(
        35,
        50,
        "Blue = T3 wav2vec miss; green = T3 wav2vec correct; orange = T4. "
        "Black ticks = group medians.",
    )
    for i, (metric, label) in enumerate(metrics):
        top = 100 + i * 138
        values = [r[metric] for r in rows if r.get(metric) is not None]
        low, high = min(values), max(values)
        span = max(high - low, 0.01)
        low, high = low - 0.1 * span, high + 0.1 * span
        if metric != "raw_st_middle_to_final":
            low = max(0, low)
        if metric in {"voiced_fraction", "active_missing_fraction", "active_periodicity_mean"}:
            high = min(1, high)
        svg.text(30, top, label)
        for tone, y in (("3", top + 32), ("4", top + 66)):
            group = [r for r in rows if r["tone"] == tone and r.get(metric) is not None]
            svg.text(30, y + 4, f"T{tone} (n={len(group)})")
            svg.line([(165, y), (1050, y)], "#ddd", width=0.7)
            for j, row in enumerate(group):
                x = 165 + 885 * (row[metric] - low) / (high - low)
                color = "#ce8130" if tone == "4" else "#178453" if row["correct"] else "#2473b8"
                svg.parts.append(
                    f'<circle cx="{x:.2f}" cy="{y + (j % 5 - 2) * 3}" r="3.5" fill="{color}">'
                    f"<title>{esc(row['text'])} {esc(row['pinyin'])}: "
                    f"{row[metric]:.4g}</title></circle>"
                )
            med = statistics.median(r[metric] for r in group)
            x = 165 + 885 * (med - low) / (high - low)
            svg.line([(x, y - 11), (x, y + 11)], "#111", width=2)
        for fraction in (0, 0.25, 0.5, 0.75, 1):
            svg.text(155 + 885 * fraction, top + 96, f"{low + fraction * (high - low):.3g}")
    svg.save(output / "plots/comparison.svg")


def make_artifacts(output, clips, rows):
    comparison_plot(output, rows)
    index = [
        "# Human audit index",
        "",
        "All 13 T3 and all 21 T4. No new listening was performed. "
        "Labels are retained. Audio links address the existing local cache; no audio is copied.",
        "",
        "[Visual gallery](index.html) · [Group comparison](plots/comparison.svg)",
        "",
        "| Clip | wav2vec | V1 / reason | Drawer | Audio | Plot |",
        "|---|---|---|---|---|---|",
    ]
    cards = []
    for clip, row in zip(clips, rows, strict=True):
        stem = row["source_asset_id"].replace(":", "-")
        plot_clip(output / "plots" / f"{stem}.svg", clip, row)
        name = f"{row['text']} {row['pinyin']}"
        probability = row[f"p_T{row['prediction']}"]
        index.append(
            f"| {name} | T{row['prediction']} ({probability:.3f}) | "
            f"{row['v1_category']} / {row['v1_reason']} | {row['drawer_verdict']} | "
            f"[{stem}]({row['local_path']}) | [plot](plots/{stem}.svg) |"
        )
        cards.append(
            f'<section data-tone="{row["tone"]}"><h2>{esc(name)} — T{row["tone"]}; '
            f"wav2vec T{row['prediction']} ({probability:.3f})</h2>"
            f"<p>{esc(row['v1_category'])} / {esc(row['v1_reason'])}</p>"
            f'<audio controls preload="none" src="file://{esc(row["local_path"])}"></audio>'
            f'<a href="plots/{stem}.svg"><img loading="lazy" src="plots/{stem}.svg" '
            f'alt="{esc(name)} acoustic plot"/></a></section>'
        )
    (output / "human-audit-index.md").write_text("\n".join(index) + "\n")
    (output / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>Luilui T3 acoustic forensics</title><style>body{font-family:system-ui;"
        "max-width:1120px;margin:30px auto;padding:12px;background:#f3f5f7;color:#243344}"
        "section{background:white;margin:24px 0;padding:14px}img{width:100%}"
        "button{padding:9px;margin:4px}</style>"
        "<h1>Luilui T3 acoustic forensics</h1><p>34 clips, unchanged labels. "
        "Research whole-clip timing; no cloud alignment. Dashed purple contours are display-only. "
        "Pink spans remain missing in measured data. "
        "Audio playback uses the existing cache and may require opening the file locally.</p>"
        '<p><a href="review.md">Research report</a> · '
        '<a href="human-audit-index.md">Audit index</a> · '
        '<a href="per-clip.csv">Per-clip CSV</a></p>'
        '<img src="plots/comparison.svg" alt="T3 versus T4 distributions">'
        '<nav><button onclick="show(0)">All 34</button><button onclick="show(3)">13 T3</button>'
        '<button onclick="show(4)">21 T4</button></nav>'
        + "\n".join(cards)
        + '<script>function show(t){document.querySelectorAll("section")'
        ".forEach(s=>s.hidden=t&&Number(s.dataset.tone)!==t)}</script></html>"
    )
