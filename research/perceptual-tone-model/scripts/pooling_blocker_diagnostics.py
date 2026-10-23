"""Cheap waveform/spectrum inspection of the fixed cases; no F0 or model calls."""

import html
import wave

import numpy as np
from perceptual_tone.common import file_hash, read_json
from perceptual_tone.pooling_blocker_audit import OUT, PRIOR, save_table


def run():
    selection = read_json(OUT / "selection.json")
    ids = set(selection["native_cases"]) | {r["control"] for r in selection["native_controls"]}
    items = {r["id"]: r for r in read_json(PRIOR / "preregistration.json")["items"]}
    details = {
        r["id"]: r
        for r in read_json(OUT / "right-edge-contributions.json")
        if r["head"] == "expanded"
    }
    folder = OUT / "acoustic-diagnostics"
    folder.mkdir(exist_ok=True)
    frozen = read_json(OUT / "freeze-before.json")["files"]
    cache, rows = {}, []
    for i in sorted(ids):
        r = details[i]
        contract = items[i]["contract"]
        path = PRIOR / "cache/canonical" / (contract["audio_sha256"] + ".wav")
        if path not in cache:
            from perceptual_tone.common import ROOT

            assert file_hash(path) == frozen[str(path.relative_to(ROOT))]
            with wave.open(str(path)) as audio:
                rate = audio.getframerate()
                assert rate == 16000 and audio.getnchannels() == 1
                y = np.frombuffer(audio.readframes(audio.getnframes()), dtype="<i2") / 32768
            cache[path] = y
        y = cache[path]
        center = round(r["mapped_timestamp"] * rate)
        x = y[center - 160 : center + 160]
        power = abs(np.fft.rfft((x - x.mean()) * np.hanning(320))) ** 2
        freq = np.fft.rfftfreq(320, 1 / rate)
        total = max(float(power.sum()), 1e-24)
        rms = float(np.sqrt(np.mean(x * x)))
        high = float(power[freq >= 3400].sum() / total)
        np.testing.assert_allclose(
            [rms, high], [r["removed_rms"], r["removed_high_band_fraction"]], atol=1e-14
        )
        rows.append(
            {
                "id": i,
                "role": r["role"],
                "audio_path": str(path),
                "window_seconds": [(center - 160) / rate, (center + 160) / rate],
                "window_outside_owner_ms": 1000 * max(0, (center + 160) / rate - r["owner_end"]),
                "rms": rms,
                "high_band_fraction": high,
                "hann_power_sum": total,
                "spectral_centroid_hz": float(freq @ power / total),
                "spectral_flatness": float(
                    np.exp(np.log(power + 1e-24).mean()) / max(power.mean(), 1e-24)
                ),
                "below_1khz_fraction": float(power[freq < 1000].sum() / total),
                "frequencies_hz": freq.tolist(),
                "power_fraction": (power / total).tolist(),
                "f0": "unavailable in consumed native artifacts; not extracted",
                "autocorrelation": "unavailable in consumed native artifacts; not recomputed",
            }
        )
        lo, hi = max(0, r["owner_start"] - 0.04), r["owner_end"] + 0.04
        a, b = round(lo * rate), min(len(y), round(hi * rate))
        samples = y[a:b]
        # Max/min per display pixel preserves peaks without plotting every PCM sample.
        parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620">',
            '<rect width="1000" height="620" fill="white"/>',
            f'<text x="60" y="25">{html.escape(i)} — frozen PCM and RIGHT window</text>',
        ]
        def xp(t, lo=lo, hi=hi):
            return 60 + 900 * (t - lo) / (hi - lo)
        peak = max(float(abs(samples).max()), 1e-6)
        parts.append(
            f'<text x="60" y="52">Waveform (PCM amplitude ±{peak:.4f}); owner boundaries dashed</text>'  # noqa: E501 -- literal SVG markup
        )
        for j, block in enumerate(np.array_split(samples, min(900, len(samples)))):
            xx = 60 + j
            parts.append(
                f'<path d="M {xx} {160 - 90 * block.max() / peak:.2f} V {160 - 90 * block.min() / peak:.2f}" stroke="#25628c"/>'  # noqa: E501 -- literal SVG markup
            )
        for t in (r["owner_start"], r["owner_end"]):
            parts.append(f'<path d="M {xp(t):.2f} 65 V 255" stroke="#555" stroke-dasharray="4 4"/>')
        parts.append(f'<path d="M {xp(r["timestamp"]):.2f} 65 V 255" stroke="#b33"/>')
        parts.append(f'<text x="60" y="278">{lo:.3f}s</text><text x="900" y="278">{hi:.3f}s</text>')
        parts.append(
            '<text x="60" y="315">Final-frame Hann spectrum (dB relative to peak; 0 to -80 dB)</text>'  # noqa: E501 -- literal SVG markup
        )
        db = np.maximum(-80, 10 * np.log10(np.maximum(power, 1e-24) / max(power.max(), 1e-24)))
        points = " ".join(
            f"{60 + 900 * f / 8000:.2f},{345 - 2 * v:.2f}" for f, v in zip(freq, db, strict=True)
        )
        parts.append(f'<polyline points="{points}" fill="none" stroke="#25628c"/>')
        parts.append('<text x="60" y="535">0 Hz</text><text x="880" y="535">8000 Hz</text>')
        parts.append(
            f'<text x="60" y="565">RMS {rms:.5f}; ≥3.4kHz fraction {high:.6f}; removed weight {r["removed_weight_share"]:.4f}</text>'  # noqa: E501 -- literal SVG markup
        )
        parts.append(
            '<text x="60" y="595">Spectral shape is descriptive; no native F0 or phonetic/coda label inferred.</text></svg>'  # noqa: E501 -- literal SVG markup
        )
        with (folder / (i.replace(":", "_") + ".svg")).open("x") as f:
            f.write("\n".join(parts) + "\n")
    save_table("native-acoustic-diagnostics", rows)
    print(
        f"Inspected {len(rows)} fixed native waveforms/windows; no inference or pitch extraction."
    )


if __name__ == "__main__":
    run()
