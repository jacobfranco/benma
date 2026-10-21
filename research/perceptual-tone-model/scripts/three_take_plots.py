"""Standalone scientific figures from frozen audio and diagnostic evidence."""

import json
import sys
import wave
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

LABELS = ("wo", "xiang", "mai", "zhe", "ge")


def main(folder):
    diagnostics = json.loads((folder / "diagnostics.json").read_text())
    acoustic = json.loads((folder / "full-acoustics.json").read_text())
    for take, (tid, data) in enumerate(acoustic.items(), 1):
        rows = [u for u in diagnostics["rows"] if u["take_id"] == tid]
        take = rows[0]["take"]
        with wave.open(str(folder / "frozen" / tid / "canonical.wav")) as w:
            rate = w.getframerate()
            y = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768.0
        fig, axes = plt.subplots(3, 1, figsize=(15, 8), sharex=True)
        t = np.arange(len(y)) / rate
        axes[0].plot(t, y, lw=0.4, color="#374151")
        axes[0].set_ylabel("PCM amplitude")
        f, st, power = spectrogram(y, rate, nperseg=400, noverlap=320)
        axes[1].pcolormesh(
            st, f, 10 * np.log10(power + 1e-12), cmap="magma", vmin=-90, vmax=-35, shading="auto"
        )
        axes[1].set_ylim(0, 4000)
        axes[1].set_ylabel("Frequency (Hz)")
        for seg in data["graph"]["filtered"]["segments"]:
            axes[2].plot(
                [p["timestamp_seconds"] for p in seg],
                [p["normalized_semitones"] for p in seg],
                ".-",
                ms=3,
            )
        axes[2].set_ylabel("Retained F0 (st)\nutterance median = 0")
        axes[2].set_xlabel("Canonical audio time (s)")
        for row in rows:
            for ax in axes:
                ax.axvspan(*row["pool"], color="#22c55e", alpha=0.15)
                for edge in row["whole"]:
                    ax.axvline(edge, color="#0ea5e9", lw=0.8)
            axes[0].text(
                np.mean(row["whole"]),
                0.85,
                LABELS[row["index"]],
                transform=axes[0].get_xaxis_transform(),
                ha="center",
            )
            for phone in row["phones"]:
                axes[1].axvline(phone["start"], color="white", alpha=0.5, lw=0.5)
        axes[2].set_xlim(max(0, rows[0]["whole"][0] - 0.3), min(t[-1], rows[-1]["whole"][1] + 0.25))
        fig.suptitle(
            f"Take {take}: waveform, spectrum, retained F0 — blue = whole boundaries; green = pool"
        )
        fig.tight_layout()
        fig.savefig(folder / f"take-{take}-acoustics.png", dpi=150)
        fig.savefig(folder / f"take-{take}-acoustics.svg")
        plt.close(fig)
    fig, axes = plt.subplots(5, 3, figsize=(15, 14), sharey="row")
    for row in diagnostics["rows"]:
        ax = axes[row["index"], row["take"] - 1]
        data = acoustic[row["take_id"]]
        for seg in data["graph"]["filtered"]["segments"]:
            pts = [p for p in seg if row["whole"][0] <= p["timestamp_seconds"] < row["whole"][1]]
            if pts:
                ax.plot(
                    [(p["timestamp_seconds"] - row["whole"][0]) * 1000 for p in pts],
                    [p["normalized_semitones"] for p in pts],
                    ".-",
                )
        ax.axvspan(*[(v - row["whole"][0]) * 1000 for v in row["pool"]], alpha=0.15, color="green")
        ax.set_xlim(0, 430)
        ax.set_title(
            f"{LABELS[row['index']]} / take {row['take']} / "
            f"{row['expanded']['prediction'] or 'abstain'}"
        )
        ax.grid(alpha=0.2)
    fig.supxlabel("Milliseconds from whole-unit start (gaps preserved)")
    fig.supylabel("Semitones relative to each utterance's median; green = pooling")
    fig.tight_layout()
    fig.savefig(folder / "cross-take-contours.png", dpi=150)
    fig.savefig(folder / "cross-take-contours.svg")
    plt.close(fig)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
