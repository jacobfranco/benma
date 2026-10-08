"""Local standalone scientific figures and an offline HTML research viewer."""

from __future__ import annotations

import argparse
import html
import json
import random
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import stft

from benchmark.pronunciation_v2.f0_foundation import ORIGINAL_TRACKERS, minimal_cleanup, read_audio
from benchmark.pronunciation_v2.f0_foundation_run import load_track

COLORS = ["#d81b60", "#1976d2", "#00845a", "#b36800", "#673ab7", "#008c99"]


def tracker_path(root: Path, recording: str, name: str) -> Path:
    directory = root / "rmvpe" if name == "rmvpe" else root
    return directory / "tracks" / f"{recording}--{name}.json"


def build(root: Path, only=None):
    rows = json.loads((root / "manifest.json").read_text())
    if only:
        rows = [r for r in rows if r["id"] in only]
    sixth = (root / "rmvpe/tracks/native_24k--rmvpe.json").exists()
    figures = root / ("figures-six" if sixth else "figures")
    figures.mkdir(exist_ok=True)
    key = root / ("blind-key-six.json" if sixth else "blind-key.json")
    if not key.exists():
        names = [*ORIGINAL_TRACKERS, "rmvpe"] if sixth else list(ORIGINAL_TRACKERS)
        # A fresh hidden permutation avoids reusing the already-revealed A-E key.
        random.SystemRandom().shuffle(names) if sixth else random.Random(5839).shuffle(names)
        key.write_text(json.dumps(dict(zip("ABCDEF"[: len(names)], names, strict=True)), indent=2))
    mapping = json.loads(key.read_text())
    cards = []
    important = {
        "native_24k",
        "native_16k",
        "take_1",
        "take_2",
        "take_3",
        "google_old",
        "human_control",
        "f5dc0cc1",
        "9b1d959a",
        "f3c642b5",
        "e59a6350",
        "7787300e",
        "silence_original",
        "silence_periodic",
        "silence_accidental",
        "syn_steady_70",
        "syn_weak_fundamental",
        "c95673d3",
        "27ea3b92",
    }
    for row in rows:
        audio, rate = read_audio(Path(row["audio_path"]))
        fig, axes = plt.subplots(
            3, 1, figsize=(13, 7), sharex=True, gridspec_kw={"height_ratios": [1, 3, 1]}
        )
        wave, spec, conf = axes
        step = max(1, len(audio) // 9000)
        wave.plot(np.arange(0, len(audio), step) / rate, audio[::step], color="#555", lw=0.5)
        wave.set_ylabel("Waveform")
        frequencies, times, z = stft(
            audio,
            rate,
            nperseg=round(rate * 0.064),
            noverlap=round(rate * 0.059),
            nfft=4096,
            boundary="zeros",
        )
        db = 20 * np.log10(np.maximum(abs(z), 1e-8))
        spec.pcolormesh(
            times,
            frequencies,
            db,
            cmap="Greys",
            vmin=db.max() - 65,
            vmax=db.max(),
            shading="auto",
            rasterized=True,
        )
        spec.set_ylim(40, 650)
        spec.set_ylabel("Frequency / F0 (Hz)")
        conf.set_ylabel("Native confidence")
        conf.set_ylim(-0.03, 1.03)
        conf.set_xlabel("Actual utterance time (seconds)")
        arrays = {}
        for i, (blind, name) in enumerate(mapping.items()):
            track = load_track(tracker_path(root, row["id"], name))
            ts, hz, cs = track.arrays()
            clean = minimal_cleanup(track, audio)
            arrays[blind] = (ts, hz, cs, clean)
            for view, values in [("raw", hz), ("minimal", clean)]:
                (line,) = spec.plot(ts, values, color=COLORS[i], lw=1.1, label=f"Tracker {blind}")
                line.set_gid(f"track-{blind}-{view}")
                if view == "minimal":
                    line.set_alpha(0)
            (line,) = conf.plot(ts, cs, color=COLORS[i], lw=0.8)
            line.set_gid(f"confidence-{blind}")
        production = root / "production" / f"{row['id']}.json"
        if production.exists():
            saved = json.loads(production.read_text())
            keep = set(saved["retained_times"])
            ts = [p["timestamp_seconds"] for p in saved["result"]["f0"]]
            hz = [
                p["f0_hz"] if p["timestamp_seconds"] in keep else np.nan
                for p in saved["result"]["f0"]
            ]
            (line,) = spec.plot(ts, hz, color="black", lw=2, ls="--", alpha=0)
            line.set_gid("production")
        wave.set_xlim(0, row["duration_seconds"])
        wave.set_title(row["id"] + " — " + row["source_provenance"], loc="left", fontsize=10)
        for ax in axes:
            ax.grid(alpha=0.15)
        fig.tight_layout()
        fig.savefig(figures / f"{row['id']}.svg")
        plt.close(fig)
        content = (figures / f"{row['id']}.svg").read_text()
        content = content[content.index("<svg") :]
        # Per-card CSS classes make tracker toggles independent and keep raw data unchanged.
        content = re.sub(
            r'id="(track-[A-F]-(?:raw|minimal)|confidence-[A-F]|production)"',
            r'class="\1"',
            content,
        )
        content = re.sub(r"opacity: 0(?=;|\")", "opacity: 1", content)
        checks = " ".join(
            f'<label><input type="checkbox" data-track="{b}" checked>Tracker {b}</label>'
            for b in mapping
        )
        cards.append(
            f'<details id="{row["id"]}" {"open" if row["id"] == "native_24k" else ""}>'
            f"<summary>{html.escape(row['id'])}</summary>"
            f"<p>{html.escape(row['source_provenance'])} · {row['duration_seconds']:.3f} s "
            f"· {row['sha256']}</p>"
            f'<div class="controls">{checks} <select class="mode">'
            '<option value="raw">Raw/native</option>'
            '<option value="minimal">Minimal cleanup</option></select>'
            '<label><input type="checkbox" class="production-toggle">'
            "Production Praat retained</label></div>"
            f'{content}<p><a href="{figures.name}/{row["id"]}.svg">Standalone SVG</a> · '
            f'<audio controls preload="none" src="audio-links/{row["id"]}.wav">'
            "</audio></p></details>"
        )
        link = root / "audio-links" / f"{row['id']}.wav"
        link.parent.mkdir(exist_ok=True)
        if not link.exists():
            link.symlink_to(Path(row["audio_path"]).resolve())
        if row["id"] in important:
            # Separate blinded panels avoid hiding branches under overlapping tracks.
            fig, axs = plt.subplots(
                len(mapping), 1, figsize=(13, 2.4 * len(mapping)), sharex=True, sharey=True
            )
            for i, (b, values) in enumerate(arrays.items()):
                ts, hz, cs, clean = values
                axs[i].pcolormesh(
                    times,
                    frequencies,
                    db,
                    cmap="Greys",
                    vmin=db.max() - 65,
                    vmax=db.max(),
                    shading="auto",
                    rasterized=True,
                )
                axs[i].plot(ts, hz, color=COLORS[i], lw=1.25)
                axs[i].set_ylabel(f"Tracker {b}\nHz")
                axs[i].set_ylim(40, 650)
                axs[i].set_xlim(0, row["duration_seconds"])
            axs[0].set_title(row["id"] + " — raw/native; algorithm names withheld")
            axs[-1].set_xlabel("Actual utterance time (seconds)")
            fig.tight_layout()
            fig.savefig(figures / f"{row['id']}--blind.png", dpi=125)
            plt.close(fig)
    key_html = html.escape(json.dumps(mapping))
    template = Path(__file__).with_suffix(".html").read_text()
    page = template.replace("{{KEY}}", key_html).replace("{{CARDS}}", "".join(cards))
    (root / "viewer.html").write_text(page)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/benma-f0-bakeoff"))
    parser.add_argument("--recording", action="append")
    args = parser.parse_args()
    build(args.output, args.recording)
