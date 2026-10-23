"""Additive acoustic diagnostics. No provider, pitch extraction or inference calls."""

import csv
import html
import subprocess
import wave
from pathlib import Path

import numpy as np

from .common import PACKAGE, ROOT, file_hash, read_json, write_json
from .f0_independent_replay import FAST, GOOGLE, SAVED, sources
from .f0_independent_replay import OUT as PRIOR
from .ownership_selector import energy_runs

OUT = PACKAGE / "data/generated/ownership-selector-v1"


def audio(path):
    with wave.open(str(path)) as stream:
        assert stream.getnchannels() == 1 and stream.getsampwidth() == 2
        rate = stream.getframerate()
        values = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
    return values.astype(float) / 32768, rate


def freeze():
    paths = set(PRIOR.rglob("*"))
    paths.update(PACKAGE.glob("perceptual_tone/*.py"))
    paths.update(PACKAGE.glob("tests/*.py"))
    paths.add(PACKAGE / "f0-independent-representation-report.md")
    paths.update(ROOT / p for p in read_json(PACKAGE / "configs/dev-learned-lock.json")["files"])
    paths.add(PACKAGE / "configs/dev-learned-lock.json")
    paths.update(GOOGLE.glob("*.json"))
    paths.add(FAST / "final-results.json")
    for source in sources():
        paths.add(Path(source["audio"]))
        if source["name"] != "google":
            paths.add(SAVED / source["take_id"] / "acoustics.json")
    tracked = subprocess.check_output(["git", "ls-files", "services/api", "apps"], cwd=ROOT)
    paths.update(ROOT / p for p in tracked.decode().splitlines())
    # Existing experiment code itself is new; freeze it at policy seal, not here.
    paths = [p for p in paths if p.is_file() and not p.name.startswith("ownership_")]
    write_json(
        OUT / "freeze-before.json",
        {
            "scope": (
                "All prior experiment artifacts, consumed inputs, frozen lock files, "
                "research Python, tracked API/app files; no corpus rescan"
            ),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(),
            "files": {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(paths)},
        },
    )


def features(values, rate):
    """20 ms Hann FFT / 5 ms hop; autocorrelation magnitude, never a pitch estimate."""
    size, hop = round(0.020 * rate), round(0.005 * rate)
    frequencies = np.fft.rfftfreq(size, 1 / rate)
    rows, last = [], None
    for center in range(size // 2, len(values) - size // 2 + 1, hop):
        x = values[center - size // 2 : center + size // 2]
        centered = x - x.mean()
        power = abs(np.fft.rfft(centered * np.hanning(size))) ** 2
        total = max(float(power.sum()), 1e-24)
        spectrum = np.sqrt(power / total)
        ac = np.correlate(centered, centered, mode="full")[size - 1 :]
        periodicity = float(
            max(ac[round(0.002 * rate) : round(0.015 * rate) + 1]) / max(ac[0], 1e-24)
        )
        rms = float(np.sqrt(np.mean(x * x)))
        rows.append(
            {
                "time": center / rate,
                "rms_20ms": rms,
                "dbfs": float(20 * np.log10(max(rms, 1e-12))),
                "zcr": float(np.mean(x[1:] * x[:-1] < 0)),
                "speech_band_fraction": float(
                    power[(frequencies >= 300) & (frequencies <= 3400)].sum() / total
                ),
                "high_band_fraction": float(power[frequencies >= 3400].sum() / total),
                "spectral_flatness": float(
                    np.exp(np.mean(np.log(power + 1e-24))) / max(power.mean(), 1e-24)
                ),
                "spectral_flux": 0.0
                if last is None
                else float(np.sqrt(np.sum(np.maximum(spectrum - last, 0) ** 2))),
                "autocorrelation_strength": periodicity,
            }
        )
        last = spectrum
    return rows


def plot(source, unit, values, rate, rows, energy):
    """Standalone vector plots from numerical arrays; same x axis on every panel."""
    i = unit["index"]
    neighbors = source["units"][max(0, i - 1) : i + 2]
    lo, hi = max(0, unit["whole"][0] - 0.18), min(len(values) / rate, unit["whole"][1] + 0.18)
    selected = [r for r in rows if lo <= r["time"] <= hi]
    panels = [
        (
            "waveform",
            [(j / rate, values[j]) for j in range(int(lo * rate), int(hi * rate), 4)],
            -1,
            1,
        ),
        (
            "saved RMS / gate",
            [(t, e / source["threshold"]) for t, e in energy if lo <= t <= hi],
            0,
            None,
        ),
    ]
    panels += [
        (key, [(r["time"], r[key]) for r in selected], low, high)
        for key, low, high in [
            ("dbfs", -90, 0),
            ("zcr", 0, 1),
            ("speech_band_fraction", 0, 1),
            ("spectral_flux", 0, 1),
            ("autocorrelation_strength", 0, 1),
        ]
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1050" viewBox="0 0 1200 1050">',  # noqa: E501
        '<rect width="1200" height="1050" fill="white"/>',
        f'<text x="70" y="25" font-size="20">{html.escape(source["name"])} unit {i}: aligned acoustic evidence (seconds)</text>',  # noqa: E501
    ]

    def xp(t):
        return 90 + (t - lo) / (hi - lo) * 1070

    for pi, (label, data, low, high) in enumerate(panels):
        y = 55 + pi * 136
        high = high if high is not None else max(v for _, v in data) * 1.05

        def yp(v, y=y, high=high, low=low):
            return y + 96 - (min(high, max(low, v)) - low) / (high - low) * 96

        parts.append(f'<text x="90" y="{y - 7}" font-size="14">{label}</text>')
        parts.append(
            f'<rect x="{xp(unit["whole"][0]):.2f}" y="{y}" width="{xp(unit["whole"][1]) - xp(unit["whole"][0]):.2f}" height="96" fill="#eaf4fc"/>'  # noqa: E501
        )
        parts.append(
            '<polyline fill="none" stroke="#175e85" stroke-width="1" points="'
            + " ".join(f"{xp(t):.2f},{yp(v):.2f}" for t, v in data)
            + '"/>'
        )
        if pi == 1:
            parts.append(f'<path d="M 90 {yp(1)} H 1160" stroke="#b33" stroke-dasharray="4 4"/>')
        for n in neighbors:
            for t in n["whole"]:
                if lo <= t <= hi:
                    parts.append(
                        f'<path d="M {xp(t)} {y} v 96" stroke="#888" stroke-dasharray="3 3"/>'
                    )
                    parts.append(
                        f'<text x="{xp(t) + 2}" y="{y + 108}" font-size="10">{t:.3f} (u{n["index"]})</text>'  # noqa: E501
                    )
        parts.append(
            f'<text x="5" y="{y + 12}" font-size="12">{high:.2f}</text><text x="5" y="{y + 95}" font-size="12">{low:.2f}</text>'  # noqa: E501
        )
    parts.append("</svg>")
    path = OUT / f"diagnostics/{source['name']}-{i}.svg"
    path.write_text("\n".join(parts))


def diagnose():
    (OUT / "diagnostics").mkdir(parents=True, exist_ok=True)
    summaries = []
    for source in sources():
        values, rate = audio(source["audio"])
        frames = features(values, rate)
        energy = [(p["timestamp_seconds"], p["energy_rms"]) for p in source["raw"]["f0"]]
        source["threshold"] = source["raw"]["energy_gate"]["threshold_rms"]
        with (OUT / f"diagnostics/{source['name']}-features.csv").open("x") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(frames[0]))
            writer.writeheader()
            writer.writerows(frames)
        for unit in source["units"]:
            runs = energy_runs(unit["whole"], energy, source["threshold"])
            for run in runs:
                inside = [r for r in frames if run["span"][0] <= r["time"] < run["span"][1]]
                run["feature_medians"] = {
                    k: float(np.median([r[k] for r in inside])) for k in frames[0] if k != "time"
                }
            gaps = []
            for j, run in enumerate(runs):
                if run["supported"] or j == 0 or j == len(runs) - 1:
                    continue
                left, right = runs[j - 1], runs[j + 1]
                gaps.append(
                    {
                        "span": run["span"],
                        "duration_ms": run["duration_ms"],
                        "median_depression_db": float(
                            20
                            * np.log10(
                                max(run["median_rms"], 1e-12)
                                / min(left["median_rms"], right["median_rms"])
                            )
                        ),
                        "left_ms": left["duration_ms"],
                        "right_ms": right["duration_ms"],
                        "smaller_share": min(left["duration_ms"], right["duration_ms"])
                        / (left["duration_ms"] + right["duration_ms"]),
                        "edge_distances_ms": [
                            1000 * (run["span"][0] - unit["whole"][0]),
                            1000 * (unit["whole"][1] - run["span"][1]),
                        ],
                    }
                )
            summaries.append(
                {
                    "recording": source["name"],
                    "index": unit["index"],
                    "whole": unit["whole"],
                    "threshold": source["threshold"],
                    "runs": runs,
                    "gaps": gaps,
                }
            )
            if (source["name"], unit["index"]) in {
                ("google", 2),
                ("google", 3),
                ("take-2", 1),
                ("take-2", 2),
                ("take-3", 0),
            }:
                plot(source, unit, values, rate, frames, energy)
    write_json(OUT / "diagnostics/summary.json", summaries)


if __name__ == "__main__":
    freeze()
    diagnose()
