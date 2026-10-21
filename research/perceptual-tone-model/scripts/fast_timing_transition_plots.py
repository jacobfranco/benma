"""Offline waveform/spectrum diagnostics; reads sealed artifacts only."""

import json
import wave
from pathlib import Path

import matplotlib
import numpy as np
from scipy.signal import spectrogram

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PACKAGE = Path(__file__).resolve().parents[1]
SAVED = PACKAGE / "data/generated/azure-timing-replay-v1"
REFERENCE = PACKAGE / "data/generated/three-take-stability-v1"
OUT = PACKAGE / "data/generated/fast-timing-ownership-v1"


def main():
    rows = json.loads((SAVED / "voiced_envelope-results.json").read_text())["rows"]
    for take, limits in [(2, (1.65, 2.48)), (3, (2.25, 2.85))]:
        rr = [r for r in rows if r["take"] == take]
        tid = rr[0]["take_id"]
        graph = json.loads((SAVED / tid / "acoustics.json").read_text())["graph"]
        with wave.open(str(REFERENCE / "frozen" / tid / "canonical.wav")) as stream:
            rate = stream.getframerate()
            y = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2") / 32768
        f, times, power = spectrogram(y, rate, nperseg=320, noverlap=240)
        fig, axes = plt.subplots(4, 1, figsize=(16, 10), sharex=True)
        t = np.arange(len(y)) / rate
        axes[0].plot(t, y, lw=0.3)
        rms = np.sqrt(np.convolve(y * y, np.ones(160) / 160, mode="same"))
        axes[1].plot(t, 20 * np.log10(rms + 1e-8))
        axes[2].pcolormesh(
            times, f, 10 * np.log10(power + 1e-12),
            cmap="magma", vmin=-95, vmax=-40, shading="auto",
        )
        axes[2].set_ylim(0, 5000)
        for segment in graph["filtered"]["segments"]:
            axes[3].plot(
                [p["timestamp_seconds"] for p in segment],
                [p["normalized_semitones"] for p in segment], ".-",
            )
        for row in rr:
            if row["azure_whole"][1] < limits[0] or row["azure_whole"][0] > limits[1]:
                continue
            for ax in axes:
                for edge in row["azure_whole"]:
                    ax.axvline(edge, color="blue", alpha=0.6)
                ax.axvspan(
                    *row["representations"]["voiced_envelope"]["contract"]["pooling"],
                    color="green", alpha=0.12,
                )
            axes[0].text(
                np.mean(row["azure_whole"]), 0.9, str(row["index"]),
                transform=axes[0].get_xaxis_transform(), clip_on=True,
            )
        for ax, label in zip(
            axes, ["Waveform", "10 ms RMS dBFS", "Spectrum Hz", "Retained F0 st"], strict=True
        ):
            ax.set_ylabel(label)
            ax.grid(alpha=0.2)
        axes[-1].set_xlim(*limits)
        axes[-1].set_xticks(np.arange(limits[0], limits[1], 0.025))
        axes[-1].tick_params(axis="x", rotation=90)
        fig.suptitle(f"Take {take}: blue Azure edges; green saved envelope; indices 0..4")
        fig.tight_layout()
        fig.savefig(OUT / f"take-{take}-transition.png", dpi=160)
        fig.savefig(OUT / f"take-{take}-transition.svg")
        plt.close(fig)


if __name__ == "__main__":
    main()
