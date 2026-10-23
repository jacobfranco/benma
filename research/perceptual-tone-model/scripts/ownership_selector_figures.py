"""Render sealed numerical diagnostics with Matplotlib; no selection or inference."""

import csv
import site

from perceptual_tone.common import read_json, write_json
from perceptual_tone.f0_independent_replay import sources
from perceptual_tone.ownership_diagnostics import OUT, audio

# Optional plotting dependency isolated from the research/model Python environment.
site.addsitedir("/tmp/ownership-plotting")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    folder = OUT / "figures"
    folder.mkdir(exist_ok=False)
    summaries = {
        (r["recording"], r["index"]): r for r in read_json(OUT / "diagnostics/summary.json")
    }
    keys = {("google", 2), ("google", 3), ("take-2", 1), ("take-2", 2), ("take-3", 0)}
    for source in sources():
        values, rate = audio(source["audio"])
        with (OUT / f"diagnostics/{source['name']}-features.csv").open() as stream:
            frames = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)]
        for unit in source["units"]:
            index = unit["index"]
            if (source["name"], index) not in keys:
                continue
            start, end = unit["whole"]
            lo, hi = start - 0.18, end + 0.18
            fig, axes = plt.subplots(7, 1, figsize=(12, 12), sharex=True, layout="constrained")
            times = [r["time"] for r in frames]
            samples = range(max(0, int(lo * rate)), min(len(values), int(hi * rate)), 2)
            axes[0].plot([j / rate for j in samples], [values[j] for j in samples], lw=0.55)
            axes[0].set_ylabel("PCM amplitude")
            axes[1].plot(times, [r["dbfs"] for r in frames], label="20 ms waveform RMS (dBFS)")
            import numpy as np

            energy = source["raw"]["f0"]
            axes[1].plot(
                [r["timestamp_seconds"] for r in energy],
                [20 * np.log10(max(r["energy_rms"], 1e-12)) for r in energy],
                alpha=0.65,
                label="saved RMS (dB)",
            )
            axes[1].axhline(
                20 * np.log10(source["raw"]["energy_gate"]["threshold_rms"]),
                color="firebrick",
                ls=":",
                label="saved gate",
            )
            axes[1].set_ylim(-90, 0)
            axes[1].set_ylabel("Energy (dB)")
            axes[1].legend(loc="lower left", fontsize=7)
            for axis, key, label in zip(
                axes[2:],
                [
                    "zcr",
                    "high_band_fraction",
                    "speech_band_fraction",
                    "spectral_flux",
                    "autocorrelation_strength",
                ],
                [
                    "Zero-crossing rate",
                    "Power >=3400 Hz",
                    "Power 300-3400 Hz",
                    "Spectral flux",
                    "Autocorrelation\nstrength (no F0)",
                ],
                strict=True,
            ):
                axis.plot(times, [r[key] for r in frames], lw=0.8)
                axis.set_ylabel(label)
                axis.set_ylim(0, 1)
            for axis in axes:
                axis.set_xlim(lo, hi)
                axis.axvspan(start, end, color="steelblue", alpha=0.09)
                for gap in summaries[source["name"], index]["gaps"]:
                    axis.axvspan(*gap["span"], color="orange", alpha=0.20)
                for neighbor in source["units"][max(0, index - 1) : index + 2]:
                    for boundary in neighbor["whole"]:
                        axis.axvline(boundary, color="gray", lw=0.7, ls="--")
                axis.grid(axis="y", alpha=0.2)
            for offset, neighbor in enumerate(source["units"][max(0, index - 1) : index + 2]):
                for boundary in neighbor["whole"]:
                    if lo <= boundary <= hi:
                        axes[0].text(
                            boundary,
                            1.02 + 0.13 * (offset % 2),
                            f"u{neighbor['index']} {boundary:.3f}",
                            fontsize=7,
                            transform=axes[0].get_xaxis_transform(),
                            ha="center",
                        )
            axes[-1].set_xlabel(
                "Recording time (seconds); blue = Azure owner, orange = internal below-gate run"
            )
            fig.suptitle(
                f"{source['name']} / unit {index} — aligned F0-independent diagnostics", fontsize=14
            )
            fig.savefig(folder / f"{source['name']}-{index}.png", dpi=150)
            fig.savefig(folder / f"{source['name']}-{index}.pdf")
            plt.close(fig)
    write_json(
        folder / "rendering.json",
        {
            "matplotlib": matplotlib.__version__,
            "dependency_scope": (
                "/tmp/ownership-plotting only; no project or model environment changes"
            ),
            "inputs": (
                "sealed diagnostics CSV/JSON and frozen PCM; no acoustic recomputation or inference"
            ),
        },
    )


if __name__ == "__main__":
    main()
