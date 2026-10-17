"""Render standalone waveform/spectrogram QA artifacts; never mark audio reviewed."""

import argparse
import json
import wave
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import spectrogram


def render(packet):
    items = [json.loads(line) for line in (packet / "items.jsonl").read_text().splitlines()]
    destination = packet / "plots"
    destination.mkdir(exist_ok=False)
    for item in items:
        row = item["row"]
        media = item["playback"]["context"]
        with wave.open(str(packet / media["reference"])) as stream:
            rate = stream.getframerate()
            samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2") / 32768.0
        times = np.arange(len(samples)) / rate + media["start_seconds"]
        frequencies, frames, power = spectrogram(samples, rate, nperseg=512, noverlap=384)
        power = 10 * np.log10(np.maximum(power, 1e-14))
        fig, axes = plt.subplots(
            2, 1, figsize=(11, 4.2), sharex=True, gridspec_kw={"height_ratios": [1, 2]}
        )
        axes[0].plot(times[::8], samples[::8], color="#273b53", lw=0.5)
        axes[0].set_ylabel("PCM amplitude")
        axes[1].pcolormesh(
            frames + media["start_seconds"],
            frequencies,
            power,
            cmap="magma",
            vmin=power.max() - 65,
            vmax=power.max(),
            shading="auto",
        )
        axes[1].set_ylim(0, 5000)
        axes[1].set_ylabel("Hz")
        axes[1].set_xlabel("Seconds in original utterance")
        for ax in axes:
            ax.axvline(row["start"], color="#25d9ed", lw=1.3)
            ax.axvline(row["end"], color="#25d9ed", lw=1.3)
            ax.set_xlim(times[0], times[-1])
        axes[0].axvspan(row["start"], row["end"], alpha=0.14, color="orange")
        for phone in row["aligned_phones"]:
            axes[1].axvline(phone["start"], color="white", alpha=0.45, lw=0.65)
            axes[1].text(
                (phone["start"] + phone["end"]) / 2,
                4600,
                phone["phone"],
                color="white",
                ha="center",
                va="center",
                fontsize=9,
            )
        previous = row["preceding"]["corpus_pinyin"] if row["preceding"] else "START"
        following = row["following"]["corpus_pinyin"] if row["following"] else "END"
        fig.suptitle(
            f"{item['item']} | {row['utterance_id']}:{row['index']} | "
            f"{previous} > {row['corpus_pinyin']} [{row['label']}] > {following}\n"
            f"Target {row['start']:.3f}-{row['end']:.3f} s | "
            "MFA boundary lines; listening still required",
            fontsize=11,
        )
        fig.tight_layout()
        fig.savefig(destination / f"{item['item']}.png", dpi=130)
        plt.close(fig)
    for offset in range(0, len(items), 5):
        subset = items[offset : offset + 5]
        fig, axes = plt.subplots(len(subset), 1, figsize=(13, len(subset) * 4.5), squeeze=False)
        for ax, item in zip(axes[:, 0], subset, strict=True):
            ax.imshow(plt.imread(destination / f"{item['item']}.png"))
            ax.axis("off")
        fig.tight_layout(pad=0.3)
        fig.savefig(destination / f"contact-{offset // 5 + 1:02d}.png", dpi=110)
        plt.close(fig)
    print(f"Rendered {len(items)} QA plots; no listening checks were filled.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    render(parser.parse_args().packet)
