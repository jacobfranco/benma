"""Developer-only measured waveform/candidate plots and gap evidence tables."""

import html
import json
import math
from collections import Counter

import numpy as np
import parselmouth
from bakeoff import CORPUS, OUT, PARAMETERS, gap_records, write
from benma_api.pronunciation.acoustics import _pcm16_mono
from benma_api.pronunciation.contours import display_contour, syllable_contour


def stage(point, retained):
    if not point.get("tracker_f0_hz"):
        return "praat_selected_unvoiced"
    if point.get("energy_gated"):
        return "below_energy_gate"
    if not point.get("quality_usable", True):
        return point.get("selection_reason", "quality_rejected")
    if point.get("voicing_probability", 0) < 0.45:
        return "below_reliable_strength_gate"
    if point["timestamp_seconds"] not in retained:
        return "hampel_or_short_octave_island_rejected"
    return "retained"


def plot(fresh, tracks, unit, gaps):
    path = CORPUS / (fresh["utterance_id"] + ".wav")
    rate, samples = _pcm16_mono(path)
    values = np.array(samples)
    a, b = unit["start_seconds"], unit["end_seconds"]
    lo, hi = max(0, a - 0.05), b + 0.05
    width, height = 1300, 1190
    left, right = 100, 1240
    x = lambda t: left + (t - lo) / (hi - lo) * (right - left)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        "<style>text{font:14px sans-serif;fill:#243347}.small{font-size:12px}</style>",
        f'<text x="35" y="25" style="font-size:20px">{html.escape(fresh["target"])} — measured F0 investigation</text>',
        f'<text x="35" y="48" class="small">Attempt {fresh["attempt_id"]}; time axis = seconds from start of canonical recording</text>',
    ]
    panels = [
        (85, 130, "Waveform (PCM amplitude) and 40-ms RMS envelope"),
        (270, 120, "Original Praat selected F0 (gray); high-pass AC witness (green); dots only"),
        (
            450,
            160,
            "All original AC candidates (opacity = periodicity); no candidate is an automatic F0",
        ),
        (
            675,
            120,
            "Reliable filtered F0 (blue); rejected voiced frames (red x); pink = internal missing support",
        ),
        (
            865,
            105,
            "Actual alternate selections: balanced DP (purple), continuity DP (orange), CC (green), legacy (gray)",
        ),
        (
            1040,
            95,
            "Frozen classifier five-bin medians (semitones): diagnostic even when the result is unclear",
        ),
    ]

    def txt(px, py, s, cls=""):
        parts.append(f'<text x="{px:.2f}" y="{py:.2f}" class="{cls}">{html.escape(str(s))}</text>')

    def line(coords, color, stroke=1):
        points = " ".join(f"{xx:.2f},{yy:.2f}" for xx, yy in coords)
        parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="{stroke}" points="{points}"/>'
        )

    def dot(xx, yy, color, r=2, opacity=1):
        parts.append(
            f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="{r}" fill="{color}" opacity="{opacity:.3f}"/>'
        )

    for top, h, title in panels:
        txt(left, top - 12, title)
        parts.append(
            f'<rect x="{left}" y="{top}" width="{right - left}" height="{h}" fill="#fbfcfe" stroke="#cbd5e1"/>'
        )
        for g in gaps:
            gs, ge = g["first_missing_center"] - 0.005, g["last_missing_center"] + 0.005
            parts.append(
                f'<rect x="{x(gs):.2f}" y="{top}" width="{x(ge) - x(gs):.2f}" height="{h}" fill="#fdd" opacity=".6"/>'
            )
        for bound in [a, b]:
            parts.append(
                f'<path d="M{x(bound):.2f},{top}v{h}" stroke="#4169e1" stroke-dasharray="5 3"/>'
            )
        region = unit["methods"]["production"]["region"]
        if region and (region["start"] != a or region["end"] != b):
            for bound in [region["start"], region["end"]]:
                parts.append(
                    f'<path d="M{x(bound):.2f},{top}v{h}" stroke="#d97706" stroke-dasharray="2 2"/>'
                )
        for t in np.arange(math.ceil(lo * 10) / 10, hi, 0.1):
            txt(x(t) - 13, top + h + 16, f"{t:.1f}", "small")
    raw = tracks["production"]["f0"]
    gate = tracks["production"]["energy_gate"]["threshold_rms"]
    view = values[round(lo * rate) : round(hi * rate)]
    peak = max(abs(view))
    top, h, _ = panels[0]
    y = lambda v: top + h / 2 - v / peak * (h / 2 - 5)
    # Min/max at each horizontal bucket preserve amplitude spikes without huge SVGs.
    n0, n1 = round(lo * rate), round(hi * rate)
    step = max(1, (n1 - n0) // 1100)
    for i in range(n0, n1, step):
        chunk = values[i : i + step]
        line(
            [(x(i / rate), y(float(chunk.min()))), (x(i / rate), y(float(chunk.max())))], "#8294a8"
        )
    line(
        [
            (x(p["timestamp_seconds"]), y(p["energy_rms"]))
            for p in raw
            if lo <= p["timestamp_seconds"] <= hi
        ],
        "#dd6b20",
        2,
    )
    line([(x(lo), y(gate)), (x(hi), y(gate))], "#e53e3e")
    txt(12, top + 14, f"+{peak:.3f}")
    txt(30, top + h / 2, "0")
    txt(12, top + h, f"−{peak:.3f}")
    retained = {p.timestamp_seconds for seg in display_contour(raw).segments for p in seg}
    for k in [1, 2, 3, 4]:
        top, h, _ = panels[k]
        yhz = lambda hz: top + h * (1 - math.log(hz / 45) / math.log(550 / 45))
        for hz in [50, 75, 100, 150, 250, 550]:
            txt(45, yhz(hz) + 4, str(hz), "small")
            parts.append(f'<path d="M{left},{yhz(hz):.2f}H{right}" stroke="#e2e8f0"/>')
        if k == 4:
            for name, color in [
                ("dp_balanced", "#805ad5"),
                ("dp_continuity", "#ed8936"),
                ("cc", "#25855a"),
                ("legacy_nac", "#637080"),
            ]:
                for p in tracks[name]["f0"]:
                    if lo <= p["timestamp_seconds"] <= hi and p.get("f0_hz"):
                        dot(x(p["timestamp_seconds"]), yhz(p["f0_hz"]), color, 2, 0.8)
            continue
        for p in raw:
            t = p["timestamp_seconds"]
            if not lo <= t <= hi:
                continue
            if k == 1:
                for key, color in [("tracker_f0_hz", "#728096"), ("comparison_f0_hz", "#24855a")]:
                    if p.get(key):
                        dot(x(t), yhz(p[key]), color, 2)
            if k == 2:
                for c in p["pitch_candidates"]:
                    dot(x(t), yhz(c["frequency_hz"]), "#713f99", 2.7, max(0.12, c["strength"]))
            if k == 3 and p.get("f0_hz"):
                reliable = display_contour(raw)
                matched = next(
                    (q for seg in reliable.segments for q in seg if q.timestamp_seconds == t), None
                )
                hz = (
                    reliable.baseline_hz * 2 ** (matched.normalized_semitones / 12)
                    if matched
                    else p["f0_hz"]
                )
                yy = yhz(hz)
                if t in retained:
                    dot(x(t), yy, "#167ab5", 2.7)
                else:
                    parts.append(f'<path d="M{x(t) - 3},{yy - 3}l6,6m-6,0l6,-6" stroke="#d22"/>')
    top, h, _ = panels[5]
    obs = unit["methods"]["production"]["observed"]
    f = obs["features"]
    bins = [(f.get(f"bin_{i}_seconds"), f.get(f"bin_{i}_st")) for i in range(1, 6)]
    ymin = min(-4, min((v for _, v in bins if v is not None), default=0) - 1)
    ymax = max(4, max((v for _, v in bins if v is not None), default=0) + 1)
    for val in np.linspace(ymin, ymax, 5):
        txt(38, top + h * (ymax - val) / (ymax - ymin), f"{val:.1f}", "small")
    for t, v in bins:
        if t is not None:
            dot(x(t), top + h * (ymax - v) / (ymax - ymin), "#167ab5", 4)
    txt(
        left,
        1170,
        f"{obs['classification']} / {obs['confidence']} / {obs['reason']}. Blue dashed: alignment; orange dotted: selected evidence (if different).",
    )
    parts.append("</svg>")
    (OUT / f"fresh-{fresh['target']}-evidence.svg").write_text("\n".join(parts))


def main():
    fresh = json.loads((OUT / "fresh-diagnostics.json").read_text())
    comparisons = json.loads((OUT / "comparison.json").read_text())
    traces = json.loads((OUT / "fresh-traces.json").read_text())
    reports = []
    for take in fresh:
        uid = take["utterance_id"]
        tracks = traces[uid]["tracks"]
        raw = tracks["production"]["f0"]
        unit = next(r for r in comparisons if r["utterance_id"] == uid)["spans"][0]
        a, b = unit["start_seconds"], unit["end_seconds"]
        region = unit["methods"]["production"]["region"]
        contour = syllable_contour(display_contour(raw), a, b)
        retained = {p.timestamp_seconds for seg in contour.segments for p in seg}
        gaps = gap_records(raw, a, b, retained)
        rate, samples = _pcm16_mono(CORPUS / (uid + ".wav"))
        values = np.array(samples)
        pitch = parselmouth.Sound(str(CORPUS / (uid + ".wav"))).to_pitch_ac(**PARAMETERS)
        frames = []
        for p, praat in zip(raw, pitch, strict=True):
            t = p["timestamp_seconds"]
            if not a <= t < b:
                continue
            center = round(t * rate)
            short = values[center - round(0.005 * rate) : center + round(0.005 * rate)]
            candidates = []
            for c in p["pitch_candidates"]:
                hz = c["frequency_hz"]
                near = [
                    q
                    for q in raw
                    if q["timestamp_seconds"] in retained
                    and abs(q["timestamp_seconds"] - t) <= 0.08
                ]
                distances = [abs(12 * math.log2(hz / q["f0_hz"])) for q in near]
                tags = []
                if c["strength"] < 0.45:
                    tags.append("below_frozen_strength_gate")
                if distances and min(distances) < 1.5:
                    tags.append("near_neighbor_branch")
                if any(10 <= d <= 14 for d in distances):
                    tags.append("octave_competition")
                if not tags:
                    tags.append("different_or_unsupported_branch")
                candidates.append({**c, "diagnostic_tags": tags})
            alternatives = {}
            for method, track in tracks.items():
                q = min(track["f0"], key=lambda q: abs(q["timestamp_seconds"] - t))
                alternatives[method] = {
                    k: q.get(k)
                    for k in [
                        "timestamp_seconds",
                        "tracker_f0_hz",
                        "f0_hz",
                        "voicing_probability",
                        "quality_usable",
                    ]
                }
            frames.append(
                {
                    **p,
                    "stage_decision": stage(p, retained),
                    "candidates_annotated": candidates,
                    "praat_frame_intensity": float(praat.intensity),
                    "rms_10ms": float(np.sqrt(np.mean(short**2))),
                    "peak_10ms": float(np.max(abs(short))),
                    "alternates": alternatives,
                }
            )
        gate = tracks["production"]["energy_gate"]["threshold_rms"]
        for gap in gaps:
            missing = [
                f
                for f in frames
                if gap["first_missing_center"]
                <= f["timestamp_seconds"]
                <= gap["last_missing_center"]
            ]
            lo, hi = gap["first_missing_center"] - 0.005, gap["last_missing_center"] + 0.005
            audio = values[round(lo * rate) : round(hi * rate)]
            gap.update(
                rms_40ms_min=min(p["energy_rms"] for p in missing),
                rms_40ms_max=max(p["energy_rms"] for p in missing),
                rms_10ms_min=min(p["rms_10ms"] for p in missing),
                rms_10ms_max=max(p["rms_10ms"] for p in missing),
                actual_gap_interval_rms=float(np.sqrt(np.mean(audio**2))),
                actual_gap_interval_peak=float(max(abs(audio))),
                all_frames_above_energy_gate=all(p["energy_rms"] >= gate for p in missing),
                frames_with_strength_at_least_045=sum(
                    any(c["strength"] >= 0.45 for c in p["pitch_candidates"]) for p in missing
                ),
                reasons=dict(Counter(p["stage_decision"] for p in missing)),
            )
        report = {
            "utterance_id": uid,
            "attempt_id": take["attempt_id"],
            "target": take["target"],
            "duration_seconds": len(values) / rate,
            "sample_rate": rate,
            "aligned": [a, b],
            "region": region,
            "energy_gate": gate,
            "aligned_waveform_rms": float(
                np.sqrt(np.mean(values[round(a * rate) : round(b * rate)] ** 2))
            ),
            "aligned_waveform_peak": float(np.max(abs(values[round(a * rate) : round(b * rate)]))),
            "segments": [
                (s[0].timestamp_seconds, s[-1].timestamp_seconds, len(s)) for s in contour.segments
            ],
            "gaps": gaps,
            "stage_counts": dict(Counter(p["stage_decision"] for p in frames)),
            "frames": frames,
        }
        reports.append(report)
        plot(take, tracks, unit, gaps)
    write("forensics.json", reports)
    # Exact per-frame candidate inventory: includes all problematic frames and onset/offset.
    lines = [
        "# Fresh 马 candidate audit",
        "",
        "All times are recording-relative seconds. Frequencies in Hz; parentheses contain measured Praat strength. The .45 downstream gate is frozen. No frequencies are inferred between frames.",
        "",
        "| Time | Raw selected | RMS40 | Stage | All AC candidates |",
        "|---|---|---|---|---|",
    ]
    ma = next(r for r in reports if r["target"] == "马")
    for p in ma["frames"]:
        candidates = (
            ", ".join(
                f"{c['frequency_hz']:.3f} ({c['strength']:.4f})" for c in p["pitch_candidates"]
            )
            or "none"
        )
        lines.append(
            f"| {p['timestamp_seconds']:.4f} | {p['tracker_f0_hz'] or 'UV'} | {p['energy_rms']:.6f} | {p['stage_decision']} | {candidates} |"
        )
    (OUT / "ma-candidates.md").write_text("\n".join(lines) + "\n")
    print([(r["target"], r["segments"], r["gaps"]) for r in reports])


if __name__ == "__main__":
    main()
