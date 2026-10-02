"""Blind packet writer: accepts only a strict acoustic manifest; cannot load an unblinding key."""

import argparse
import wave
from pathlib import Path

import numpy as np

from benchmark.pronunciation_v2.forensics_plots import SVG
from benchmark.pronunciation_v2.phonetic_evidence import (
    FRAME,
    HOP,
    RATE,
    SavedFrame,
    Span,
    decode,
    dump,
    extract_observed,
    load_manifest,
    sha,
)


def plots(destination, rid, crop, evidence):
    duration = len(crop) / RATE
    # Same physical scales for all regions; x includes whitespace after shorter crops.
    svg = SVG(1100, 270)
    svg.text(30, 28, f"{rid} | waveform | digital amplitude | analysis windows are not phones")
    xy = svg.panel(65, "Seconds relative to crop; shared 0-0.65 s axis", 0.65, -1, 1)
    for offset in range(0, len(crop), 16):
        chunk = crop[offset : offset + 16]
        t = offset / RATE
        svg.line([xy(t, float(chunk.min())), xy(t, float(chunk.max()))], "#28568c", width=0.8)
    for w in evidence["analysis_windows"]:
        svg.spans([{"start": w["start_ms"] / 1000, "end": w["end_ms"] / 1000}], xy, -1, 1)
        svg.text(*xy(w["start_ms"] / 1000, 0.8), w["kind"])
    svg.line([xy(duration, -1), xy(duration, 1)], "#555", dashed=True)
    svg.save(destination / "waveform.svg")

    svg = SVG(1100, 580)
    svg.text(30, 28, f"{rid} | saved pitch, strength and measured energy | no gap interpolation")
    pitch = evidence["pitch"]["frames"]
    xy = svg.panel(80, "Saved raw F0 (gray), usable selected F0 (blue), Hz", 0.65, 0, 600, 110)
    for p in pitch:
        t = p["timestamp_seconds"]
        if p["f0_hz"] is not None:
            svg.line([xy(t, p["f0_hz"])], "#aaa")
        if p["selected_f0_hz"] is not None and p["quality_usable"]:
            svg.line([xy(t, p["selected_f0_hz"])], "#2374b8")
    xy = svg.panel(
        270,
        "Saved candidate strength (not probability); missing F0 is not unvoiced",
        0.65,
        0,
        1,
        80,
    )
    for p in pitch:
        if p["voicing_probability"] is not None:
            svg.line([xy(p["timestamp_seconds"], p["voicing_probability"])], "#8b5b91")
    xy = svg.panel(435, "25 ms RMS, digital amplitude (fixed scale)", 0.65, 0, 1, 80)
    svg.line([xy(r["time_ms"] / 1000, r["rms"]) for r in evidence["spectral_frames"]], "#207945")
    svg.save(destination / "pitch-energy.svg")

    svg = SVG(1100, 500)
    svg.text(30, 28, f"{rid} | spectrogram | 25 ms Hann / 10 ms hop / 512 FFT")
    svg.text(
        30, 48, "Fixed grayscale: -100 dB white to -20 dB black; bin power / squared window sum"
    )
    xy = svg.panel(
        90,
        "Hz; dots: Burg estimates (green passes frame sanity, orange rejected)",
        0.65,
        0,
        8000,
        300,
    )
    window = np.hanning(FRAME)
    for offset in range(0, len(crop) - FRAME + 1, HOP):
        frame = crop[offset : offset + FRAME].astype(float)
        power = abs(np.fft.rfft((frame - frame.mean()) * window, n=512)) ** 2 / window.sum() ** 2
        db = 10 * np.log10(np.maximum(power, 1e-12))
        for k, value in enumerate(db):
            shade = round(255 * (1 - np.clip((value + 100) / 80, 0, 1)))
            t = (offset + FRAME / 2) / RATE
            x, y = xy(t - 0.005, min(8000, (k + 0.5) * RATE / 512))
            x2, y2 = xy(t + 0.005, max(0, (k - 0.5) * RATE / 512))
            svg.parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{x2 - x:.2f}" '
                f'height="{y2 - y:.2f}" fill="rgb({shade},{shade},{shade})"/>'
            )
    for row in evidence["formants"]["frames"]:
        for f in row["hz"]:
            if f is not None:
                svg.line(
                    [xy(row["time_ms"] / 1000, f)], "#148543" if row["sanity_pass"] else "#ce6500"
                )
    for w in evidence["analysis_windows"]:
        for t in (w["start_ms"], w["end_ms"]):
            svg.line([xy(t / 1000, 0), xy(t / 1000, 8000)], "#426bd0", dashed=True)
    svg.text(
        40, 470, "Window edges are analysis heuristics. No independent consonant or vowel label."
    )
    svg.save(destination / "spectrogram.svg")


def crop_wav(path, crop):
    # Float source is preserved in the original. The listening artifact is ordinary PCM16.
    samples = np.clip(np.rint(crop * 32768), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(RATE)
        stream.writeframes(samples.tobytes())


def build_packet(manifest_path, output):
    manifest = load_manifest(manifest_path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    decoded = {}
    for r in manifest["regions"]:
        path = r["audio_path"]
        if sha(path) != r["audio_sha256"]:
            raise ValueError("Audio hash mismatch")
        if path not in decoded:
            decoded[path] = decode(path)
        span = Span(**r["span"])
        evidence = extract_observed(
            decoded[path], span, tuple(SavedFrame(**p) for p in r["saved_frames"])
        )
        evidence["id"] = r["id"]
        dest = output / r["id"]
        dest.mkdir()
        dump(dest / "evidence.json", evidence)
        if evidence["status"] == "measured":
            start, end = (round(v / 1000 * RATE) for v in (span.start_ms, span.end_ms))
            crop = decoded[path][start:end]
            crop_wav(dest / "crop.wav", crop)
            plots(dest, r["id"], crop, evidence)
        rows.append({k: v for k, v in evidence.items() if k not in {"spectral_frames"}})
    dump(output / "summary.json", rows)
    lines = [
        "# Blind acoustic observations",
        "",
        "No correctness judgments. Missing pitch is not proof of absent voicing.",
        "",
        "| Region | ms | RMS | Saved F0 usable/total | Longest run frames | "
        "Formants | Prefix spectrum |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        p = r["pitch"]
        if p is None:
            lines.append(
                f"| {r['id']} | {r['duration_ms']} | unavailable | unavailable | "
                "0 | unavailable | unavailable |"
            )
            continue
        lines.append(
            f"| {r['id']} | {r['duration_ms']:g} | {r['energy']['rms']:.4f} | "
            f"{p['usable_frame_count']}/{p['frame_count']} | {p['longest_run_frames']} | "
            f"{r['formants']['status']} | {r['onset']['status']} |"
        )
    (output / "observations.md").write_text("\n".join(lines) + "\n")
    html = [
        "<!doctype html><meta charset='utf-8'><title>Blind acoustic review</title>",
        "<style>body{font:16px sans-serif;max-width:1150px;margin:2em auto}"
        "img{width:100%}section{margin:3em 0}</style>",
        "<h1>Blind acoustic review</h1><p>Analysis windows are not phones. No correctness labels. "
        "Listen before inspecting any unblinding key. Crops preserve source gain.</p>",
        "<p>Review prompts: boundary truncation? audible periodicity? stable resonance/noise? "
        "What is uncertain? Record observations before proposing segment identity.</p>",
    ]
    for r in rows:
        rid = r["id"]
        html.append(f"<section><h2>{rid}</h2>")
        if r["status"] == "measured":
            html.append(f"<audio controls src='{rid}/crop.wav'></audio>")
            html.extend(
                f"<img alt='{rid} {name}' src='{rid}/{name}.svg'>"
                for name in ("waveform", "spectrogram", "pitch-energy")
            )
        html.append(
            f"<p><a href='{rid}/evidence.json'>Measurements and reason flags</a></p></section>"
        )
    (output / "index.html").write_text("\n".join(html) + "\n")
    # A receipt is written before any unblinding process. It covers all current packet files.
    dump(
        output / "seal.json",
        {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*")) if p.is_file()},
    )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = build_packet(args.manifest, args.output)
    print(f"Sealed {len(rows)} regions at {args.output}")


if __name__ == "__main__":
    main()
