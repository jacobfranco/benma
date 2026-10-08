"""Create static research plots and tables from saved Silero probabilities."""

from __future__ import annotations

import csv
import html
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import spectrogram
from silero_vad_audit import PRIOR, RATE, REPORT, corpus, normalize_audio, write_json

REPRESENTATIVES = {
    "silence_accidental": "Newest accidental silence — false accept",
    "silence_periodic": "Earlier periodic silence — rejected",
    "short_human_b": "110 ms human speech — false reject",
    "short_native": "300 ms digital speech — false reject at default",
    "native_gain": "Quiet digital speech — retained",
    "7787300e": "Quiet low-F0 speech — retained",
    "low_f0_excerpt_2": "270 ms low-F0 excerpt — retained at default",
    "human_control": "Ordinary human speech — retained",
}
NEGATIVE_CATEGORIES = {
    "silence_accidental": "newest accidental silence",
    "silence_periodic": "periodic-background silence",
    "silence_original": "original silence hallucination",
    "neg_digital_silence": "digital silence",
    "neg_stationary_noise": "stationary noise",
    "neg_clicks": "clicks/transients",
}


def table(headers, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
                *["| " + " | ".join(map(str, row)) + " |" for row in rows],
            ]
        )
        + "\n"
    )


def decision(value):
    return "accept" if value else "reject"


def fmt(value, places=3):
    return "—" if value is None else f"{value:.{places}f}"


def categories(row):
    if row["label"] == "negative":
        return NEGATIVE_CATEGORIES.get(row["id"], "padding excerpt")
    return ", ".join(row["tags"]) or "unresolved"


def main():
    _, entries, audio = corpus()
    default = json.loads((REPORT / "default-results.json").read_text())
    rows = default["rows"]
    lookup = {r["id"]: r for r in rows}
    sweep = json.loads((REPORT / "threshold-results.json").read_text())["runs"]
    overlays = json.loads((REPORT / "accidental-overlays.json").read_text())
    asr = {r["id"]: r for r in json.loads((PRIOR / "asr-audit.json").read_text())}
    figures = REPORT / "figures"
    figures.mkdir(exist_ok=True)
    for key, title in REPRESENTATIVES.items():
        timeline = json.loads((REPORT / "probabilities" / f"{key}.json").read_text())
        samples, _ = normalize_audio(audio[key])
        result = lookup[key]["silero"]
        accidental = key == "silence_accidental"
        fig, axes = plt.subplots(
            4 if accidental else 3,
            1,
            figsize=(13, 9 if accidental else 7.8),
            sharex=True,
            layout="constrained",
            gridspec_kw={"height_ratios": [1, 1.5, 1, 0.55] if accidental else [1, 1.5, 1]},
        )
        fig.suptitle(f"{title}\n{key} · default threshold 0.50 · min speech 250 ms", fontsize=14)
        axes[0].plot(np.arange(len(samples)) / RATE, samples, color="#1c5478", linewidth=0.5)
        axes[0].set_ylabel("PCM amplitude")
        hz, seconds, power = spectrogram(
            samples,
            RATE,
            window="hann",
            nperseg=400,
            noverlap=240,
            nfft=1024,
            detrend="constant",
            scaling="density",
        )
        axes[1].pcolormesh(
            seconds,
            hz,
            10 * np.log10(np.maximum(power, 1e-14)),
            shading="auto",
            cmap="magma",
            vmin=-110,
            vmax=-35,
        )
        axes[1].set_ylim(0, 4000)
        axes[1].set_ylabel("Hz (25 ms STFT)")
        probs = [f["probability"] for f in timeline["frames"]]
        edges = [f["start_seconds"] for f in timeline["frames"]] + [
            timeline["frames"][-1]["window_end_seconds"]
        ]
        axes[2].stairs(probs, edges, color="#2166ad", linewidth=1.5, label="Silero / 32 ms")
        axes[2].axhline(0.5, color="#a02c2c", linestyle="--", label="start ≥ 0.50")
        axes[2].axhline(0.35, color="#999999", linestyle=":", label="exit < 0.35")
        axes[2].set_ylim(-0.03, 1.05)
        axes[2].set_ylabel("Speech probability")
        for i, region in enumerate(result["regions_seconds"]):
            for ax in (axes[0], axes[2]):
                ax.axvspan(
                    region["start"],
                    region["end"],
                    color="#228b22",
                    alpha=0.12,
                    label="detected region (+30 ms pad)" if i == 0 else None,
                )
        axes[2].legend(loc="lower right", fontsize=8)
        if accidental:
            for name, y, color in (
                ("energy_runs", 0.7, "#d17a0c"),
                ("periodic_runs", 0.15, "#774caa"),
            ):
                axes[3].broken_barh(
                    [(r["start_seconds"], r["duration_seconds"]) for r in overlays[name]],
                    (y, 0.3),
                    facecolors=color,
                )
            axes[3].set_ylim(0, 1.2)
            axes[3].set_yticks([0.85, 0.30], ["old energy", "old periodic"])
            axes[3].text(2.39, 1.03, "290 ms", fontsize=8)
            axes[3].text(0.57, 0.5, "470 ms", fontsize=8)
        for ax in axes:
            ax.set_xlim(0, len(samples) / RATE)
            ax.grid(alpha=0.15)
        axes[-1].set_xlabel("Seconds from start of this frozen waveform/excerpt")
        fig.savefig(figures / f"{key}.png", dpi=140)
        plt.close(fig)

    panels = "\n".join(
        f"<section><h2>{html.escape(title)}</h2>"
        f'<img src="figures/{key}.png" alt="{html.escape(title)}">'
        f'<p><a href="probabilities/{key}.json">Raw probability timeline</a></p></section>'
        for key, title in REPRESENTATIVES.items()
    )
    (REPORT / "viewer.html").write_text(
        (
            '<!doctype html><html lang="en"><meta charset="utf-8"><title>Silero'
            " frozen presence audit</title><style>body{font:16px "
            "system-ui;max-width:1200px;margin:32px auto;padding:0 "
            "20px;color:#17324a}img{width:100%;height:auto}section{margin:45px "
            "0;border-top:1px solid #ddd}a{color:#2166ad}</style><h1>Silero: "
            "critical false accept remains</h1><p>Official defaults: 9/10 "
            "negatives rejected; 33/37 positives retained. All panels show the "
            "same 0-1 probability scale. Waveform amplitude axes scale per "
            "recording; spectrogram uses a fixed -110 to -35 dB/Hz color range."
            " Green shows padded detected speech. Orange/purple show the "
            "existing guard's decision cells.</p><p><a "
            'href="corpus-results.md">Complete results</a> · <a '
            'href="decision.md">Decision</a></p>'
        )
        + panels
        + "</html>\n"
    )

    header = [
        "File",
        "Category",
        "Old",
        "Silero",
        "Peak p",
        "Median p",
        "Speech s",
        "Longest s",
        "Regions",
        "First s",
        "Last s",
    ]

    def metrics(row):
        s = row["silero"]
        return [
            row["id"],
            categories(row),
            decision(row["current_accepted"]),
            decision(s["accepted"]),
            fmt(s["max_probability"], 6),
            fmt(s["median_probability"], 6),
            fmt(s["total_speech_seconds"]),
            fmt(s["longest_region_seconds"]),
            s["number_regions"],
            fmt(s["first_speech_seconds"]),
            fmt(s["last_speech_seconds"]),
        ]

    content = (
        "# Exact frozen corpus results\n\nThe manifest is a byte-for-byte "
        "copy of the prior presence manifest: **37 positives, 10 negatives,"
        " one unresolved**. All 48 SHA-256 identities and every excerpt's "
        "parent hash were checked before inference; none was added, removed"
        " or skipped. [Hashes](hash-verification.json), [unchanged "
        "manifest](corpus.json), [fresh baseline "
        "replay](baseline-replay.json).\n\nThese are 48 cases, not 48 "
        "independent recordings. Positives comprise 28 captures, three "
        "existing digital variants, and six exact excerpts. Negatives "
        "comprise three user-labelled captures, three stored synthetic "
        "non-speech controls, and four existing padding excerpts. The "
        "unresolved capture stays outside all positive/negative "
        "denominators. Every evaluated input is mono PCM16: 46 use 16 kHz; "
        "native_gain and native_bandlimit use 24 kHz and were normalized to "
        "16 kHz by the documented resampler. Crops "
        "are reconstructed in memory without creating new audio files.\n\n"
        "Speech duration and first/last boundaries below come from the "
        "official helper, including its 30 ms padding after the strict >250"
        " ms pre-padding duration filter. Median probability covers all "
        "chunks, including silence and the zero-padded final chunk; it is "
        "not a conditional speech-region median. Speech present means at "
        "least one returned region. Full-precision values and interval "
        "lists are in [default-results.json](default-results.json); all raw"
        " frames are under [probabilities/](probabilities/).\n\n## Ten "
        "negatives\n\nBaseline: 4/10 rejected, 6 false accepts. Silero "
        "defaults: **9/10 rejected, one false accept**. The remaining false"
        " accept is the required newest accidental-silence case. Categories"
        " are 1 original silence, 1 periodic silence, 1 accidental silence,"
        " 1 digital silence, 1 stationary noise, 1 clicks/transients, 4 "
        "padding excerpts.\n\n"
    )
    content += table(header, [metrics(r) for r in rows if r["label"] == "negative"])
    content += (
        "\n## All 37 positives\n\nBaseline retains 37/37; Silero defaults "
        "retain **33/37**. All 31 whole waveforms survive; four of six "
        "short excerpts fail.\n\n"
    )
    content += table(header, [metrics(r) for r in rows if r["label"] == "positive"])
    content += "\n## Exact overlapping positive category counts\n\n"
    content += table(
        ["Frozen tag", "Count", "Old retained", "Default retained"],
        [
            [tag, counts["total"], counts["total"], counts["retained"]]
            for tag, counts in default["summary"]["categories"].items()
        ],
    )
    content += (
        "\n`ordinary` includes the connected Mandarin captures. "
        "`sparse_pitch` is the existing voiced-fraction proxy, not "
        "independently labelled unvoiced-heavy speech. Quiet RMS and low-F0"
        " are existing acoustic proxies. No independently labelled whisper "
        "or noisy-speech category exists. Categories overlap and must not "
        "be summed.\n"
    )
    short = sorted([r for r in rows if "short" in r["tags"]], key=lambda r: r["duration_seconds"])
    content += (
        "\n## Short speech is a blocking regression\n\nActual duration is the "
        "entire frozen speech excerpt. Peak margin is peak p minus 0.50; a "
        "positive margin does not guarantee the minimum region length.\n\n"
    )
    content += table(
        [
            "File",
            "Actual ms",
            "Detected ms",
            "Peak p",
            "Peak-0.50",
            "First p≥0.50 ms",
            "Default",
            "Accepted thresholds",
        ],
        [
            [
                r["id"],
                fmt(r["duration_seconds"] * 1000, 1),
                fmt(r["silero"]["total_speech_seconds"] * 1000, 1),
                fmt(r["silero"]["max_probability"], 6),
                fmt(r["silero"]["max_probability"] - 0.5, 6),
                fmt(
                    next(
                        (
                            f["start_seconds"] * 1000
                            for f in json.loads(
                                (REPORT / "probabilities" / f"{r['id']}.json").read_text()
                            )["frames"]
                            if f["probability"] >= 0.5
                        ),
                        None,
                    ),
                    1,
                ),
                decision(r["silero"]["accepted"]),
                ", ".join(
                    fmt(run["threshold"], 2)
                    for run in sweep
                    if next(x for x in run["rows"] if x["id"] == r["id"])["silero"]["accepted"]
                )
                or "none",
            ]
            for r in short
        ],
    )
    raw_short = []
    for row in short:
        frames = json.loads((REPORT / "probabilities" / f"{row['id']}.json").read_text())["frames"]
        above = [frame for frame in frames if frame["probability"] >= 0.5]
        raw_short.append(
            [
                row["id"],
                len(frames),
                len(above),
                fmt(sum(f["end_seconds"] - f["start_seconds"] for f in above) * 1000, 1),
            ]
        )
    content += (
        "\nRaw high-probability evidence is present even in the four false rejects. "
        "The table counts actual valid audio under each p>=0.50 chunk; the "
        "zero-padded tail is not counted as additional duration. These durations "
        "are distinct from hysteresis-based segmented durations.\n\n"
    )
    content += table(["File", "All frames", "Frames p>=0.50", "Time p>=0.50 ms"], raw_short)
    content += (
        "\nThe 110/170/200 ms human excerpts cannot pass the default >250 ms"
        " rule, despite peaks above 0.5. The 300 ms native excerpt crosses "
        "0.5 only at 96 ms, leaving 204 ms to EOF, so it also fails; "
        "threshold 0.30 starts at zero and retains it. The 260/270 ms "
        "low-F0 excerpts pass at 0.50 but are vulnerable to small onset "
        "delays at higher thresholds. Peak confidence alone conceals these "
        "failures. No minimum-duration policy is promoted or swept, because"
        " threshold-only evaluation already fails the critical negative "
        "requirement.\n\n## All five low-F0 controls\n\nThese retain the frozen"
        " 54-70 Hz evidence labels; no tracker, floor or eligibility was "
        "changed. Quantiles cover all raw chunks (p10 / median / p90 / "
        "max). Whole recordings include leading/trailing silence.\n\n"
    )
    content += table(
        ["File", "Default", "Speech s", "p10", "Median", "p90", "Max", "Accepted thresholds"],
        [
            [
                r["id"],
                decision(r["silero"]["accepted"]),
                fmt(r["silero"]["total_speech_seconds"]),
                *[
                    fmt(r["silero"]["probability_quantiles_0_10_25_50_75_90_95_100"][i], 6)
                    for i in (1, 3, 5, 7)
                ],
                ", ".join(
                    fmt(run["threshold"], 2)
                    for run in sweep
                    if next(x for x in run["rows"] if x["id"] == r["id"])["silero"]["accepted"]
                ),
            ]
            for r in rows
            if "low_f0_54_70_proxy" in r["tags"]
        ],
    )
    content += (
        "\nAt default, Silero does not appear to confuse legitimate 54-70 Hz "
        "speech with non-speech in these five frozen controls. This is a positive "
        "result despite the overall failure. Silero distinguishes the earlier "
        "periodic hum (peak 0.048586) "
        "from all five low-F0 controls at default. It still gives the "
        "accidental negative a 0.997681 peak. At 0.60 one low-F0 excerpt "
        "fails; at 0.70 both fail. This is duration/onset sensitivity, not "
        "evidence for raising a pitch floor.\n"
    )
    content += (
        "\n## Transcript-free and lexically unreliable cases\n\nNo transcript,"
        " intended target, language, character count, lexical tone, pinyin,"
        " ASR score or semantic validity enters either audio adapter or the"
        " primary decisions. Six metadata contexts over all 48 waveforms "
        "reproduce identical raw probabilities and intervals, including "
        "every false accept/reject. Invariance cannot turn a rejected valid"
        " waveform into a passing gibberish result.\n\n"
    )
    absent = [r for r in rows if r["label"] == "positive" and not entries[r["id"]]["transcript"]]
    content += table(
        ["Absent-transcript positive", "Default", "Speech s", "Peak p"],
        [
            [
                r["id"],
                decision(r["silero"]["accepted"]),
                fmt(r["silero"]["total_speech_seconds"]),
                fmt(r["silero"]["max_probability"], 6),
            ]
            for r in absent
        ],
    )
    content += (
        "\n**5/9 absent-transcript positives survive; four short excerpts "
        "fail acoustically/temporally.** The three full digital controls "
        "and two low-F0 excerpts succeed without any ASR rescue.\n\n"
    )
    content += table(
        ["Case", "Saved text (comparison only)", "Saved mean token logprob", "Default", "Speech s"],
        [
            [
                key,
                asr[key]["raw_transcript"],
                fmt(asr[key]["mean_logprob"], 6),
                decision(lookup[key]["silero"]["accepted"]),
                fmt(lookup[key]["silero"]["total_speech_seconds"]),
            ]
            for key in ("5b995fff", "370aa8f4", "90aa0d8d")
        ],
    )
    content += (
        "\n`5b995fff` is the weakest saved positive ASR by mean token "
        "logprob; the other two have fragmentary/lexically unreliable saved"
        " wording. These labels describe metadata, not new ground truth "
        "about what was spoken. All survive from audio alone. **No "
        "confirmed nonsense/nonlexical speech recording exists in the "
        "frozen corpus.** Metadata substitution proves text independence, "
        "not general gibberish recall. No claim of full language diversity "
        "validation is made.\n"
    )
    content += "\n## Unresolved case (not scored)\n\n"
    content += table(header, [metrics(r) for r in rows if r["label"] == "unresolved"])
    content += (
        "\nIts prior failed ASR does not justify changing the frozen label. "
        "No case is removed to improve the result.\n"
    )
    (REPORT / "corpus-results.md").write_text(content)
    with (REPORT / "corpus-results.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["id", "label", "audio_sha256", "duration_seconds", *header[1:]])
        for r in rows:
            writer.writerow(
                [r["id"], r["label"], r["audio_sha256"], r["duration_seconds"], *metrics(r)[1:]]
            )

    timeline = json.loads((REPORT / "probabilities/silence_accidental.json").read_text())
    frame_rows = timeline["frames"]

    def interval_stats(start, end):
        selected = [
            (f, max(0, min(end, f["end_seconds"]) - max(start, f["start_seconds"])))
            for f in frame_rows
        ]
        selected = [(f, w) for f, w in selected if w > 1e-10]
        return {
            "start_seconds": start,
            "end_seconds": end,
            "probability_min": min(f["probability"] for f, w in selected),
            "probability_median_over_overlapping_chunks": float(
                np.median([f["probability"] for f, w in selected])
            ),
            "probability_max": max(f["probability"] for f, w in selected),
            "seconds_p_ge_0_5": sum(w for f, w in selected if f["probability"] >= 0.5),
            "seconds_p_ge_0_9": sum(w for f, w in selected if f["probability"] >= 0.9),
        }

    energy = max(overlays["energy_runs"], key=lambda r: r["duration_seconds"])
    periodic = max(overlays["periodic_runs"], key=lambda r: r["duration_seconds"])
    forensic = {
        "whole_clip": interval_stats(0, timeline["input_duration_seconds"]),
        "energy_290_ms": interval_stats(energy["start_seconds"], energy["end_seconds"]),
        "periodic_470_ms": interval_stats(periodic["start_seconds"], periodic["end_seconds"]),
        "default_detected_region": interval_stats(1.026, 2.878),
    }
    write_json(REPORT / "accidental-analysis.json", forensic)
    print(json.dumps(forensic, indent=2))
    print("Generated", len(REPRESENTATIVES), "figures, static viewer, complete corpus tables.")


if __name__ == "__main__":
    main()
