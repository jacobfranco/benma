"""Render the sealed four-case audit; plotting dependencies stay outside inference."""

import csv
import json
import wave
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PACKAGE = Path(__file__).resolve().parents[1]
OUT = PACKAGE / "data/generated/frame-attribution-v1"
COLORS = ("#3875b8", "#b45c17", "#328551", "#9b4eae")


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(map(str, r)) + " |" for r in rows),
        ]
    )


def main():
    results = json.loads((OUT / "results.json").read_text())
    appendix = [
        "# Four-case numerical audit",
        "",
        "All probabilities are uncalibrated; class order T1, T2, T3, T4. "
        "Regions are frame-position quintiles, not asserted phone boundaries. "
        "Pair margin is expanded new class minus expanded old class for both heads. "
        "TV compares with the complete new span. Full logits are in results.json.",
    ]
    acoustic_rows = []
    for case in results["cases"]:
        folder = OUT / case["case"]
        centers = np.array(case["centers"])
        current, new = [case["plan"][k] for k in ("current", "new")]
        lo, hi = case["new_contract"]["context"]
        with wave.open(case["new_contract"]["audio_reference"]) as f:
            rate = f.getframerate()
            audio = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2") / 32768
        raw = case["acoustics"]["raw"]
        points = raw["f0"]
        times = np.array([p["timestamp_seconds"] for p in points])
        rms = np.array([p["energy_rms"] for p in points])
        with (
            PACKAGE
            / "data/generated/ownership-selector-v1/diagnostics"
            / f"{case['recording']}-features.csv"
        ).open() as f:
            spectral = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
        st = np.array([r["time"] for r in spectral])
        fig, axes = plt.subplots(
            7,
            1,
            figsize=(13, 15),
            sharex=True,
            gridspec_kw={"height_ratios": [1, 1.5, 1, 0.8, 1.3, 1.3, 1]},
        )
        t = np.arange(len(audio)) / rate
        use = (t >= lo) & (t <= hi)
        axes[0].plot(t[use][::3], audio[use][::3], color="#33485c", linewidth=0.5)
        axes[0].set_ylabel("Waveform")
        _, _, bins, spectrogram = axes[1].specgram(
            audio[use],
            NFFT=512,
            Fs=rate,
            noverlap=432,
            cmap="magma",
            vmin=-100,
            vmax=-30,
        )
        crop_start = t[use][0]
        half_hop = (512 - 432) / rate / 2
        spectrogram.set_extent(
            (crop_start + bins[0] - half_hop, crop_start + bins[-1] + half_hop, 0, rate / 2)
        )
        axes[1].set_ylim(0, 5000)
        axes[1].set_ylabel("Spectrum (Hz)")
        axes[2].plot(times, rms / raw["energy_gate"]["threshold_rms"], label="saved RMS / gate")
        axes[2].axhline(1, color="#aa3333", linestyle=":", label="existing gate")
        axes[2].set_ylabel("Support")
        ax2 = axes[2].twinx()
        ax2.plot(st, [r["zcr"] for r in spectral], color="#c57c21", alpha=0.7, label="ZCR")
        ax2.set_ylim(0, 1)
        ax2.set_ylabel("ZCR", color="#c57c21")
        axes[2].legend(loc="upper right", fontsize=8)
        axes[3].scatter(centers, np.zeros(len(centers)), marker="|", color="#aaa", label="context")
        axes[3].scatter(centers[current], np.ones(len(current)), marker="s", color="#253d80")
        axes[3].scatter(centers[new], 2 * np.ones(len(new)), marker="s", color="#bf7429")
        axes[3].set_yticks([0, 1, 2], ["all centers", "current", "new"])
        for label, ids in case["plan"]["regions"].items():
            axes[3].text(centers[ids].mean(), 2.6, label, ha="center", fontsize=8)
        axes[3].set_ylim(-0.5, 3.2)
        for ax, head in zip(axes[4:6], ("expanded", "pilot"), strict=True):
            data = case["heads"][head]
            rows = data["frames"]
            x = np.array([r["seconds"] for r in rows])
            ax.bar(
                x - 0.003,
                [r["pair_current_contribution"] for r in rows],
                width=0.006,
                color="#253d80",
                label="current contribution",
            )
            ax.bar(
                x + 0.003,
                [r["pair_new_contribution"] for r in rows],
                width=0.006,
                color="#bf7429",
                label="new contribution",
            )
            ax.axhline(0, color="#888", lw=0.7)
            ax.set_ylabel(head + "\n" + data["pair"][1] + " minus " + data["pair"][0])
            ax.legend(loc="upper right", fontsize=8)
        f0 = np.array(
            [p["selected_f0_hz"] if p["selected_f0_hz"] is not None else np.nan for p in points]
        )
        axes[6].plot(times, f0, ".-", linewidth=0.7, markersize=3, color="#386458")
        axes[6].set_ylabel("Saved F0 (Hz)")
        axes[6].set_title(
            "Interpretation only; saved eligibility: "
            + case["acoustics"]["pitch_evidence"]["status"],
            fontsize=9,
            loc="left",
        )
        for ax in axes:
            for bounds in case["acoustics"]["neighbors"]:
                for b in bounds:
                    ax.axvline(b, color="#777", linestyle=":", lw=0.7)
            for b in case["new_contract"]["pooling"]:
                ax.axvline(b, color="#bf7429", lw=1)
            ax.set_xlim(lo, hi)
            ax.grid(alpha=0.15)
        axes[0].set_title(
            case["case"] + " | fixed context; orange = Azure owner; "
            "dotted = neighboring Azure bounds"
        )
        axes[-1].set_xlabel("Seconds in frozen waveform")
        fig.subplots_adjust(left=0.12, right=0.88, top=0.97, bottom=0.04, hspace=0.34)
        for suffix in ("png", "pdf"):
            fig.savefig(folder / f"timeline.{suffix}", dpi=160, bbox_inches="tight")
        plt.close(fig)
        fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharey=True)
        for i, head in enumerate(("expanded", "pilot")):
            for j, direction in enumerate(("prefix", "suffix")):
                rows = [
                    v
                    for k, v in case["heads"][head]["subsets"].items()
                    if k.startswith(direction + "_")
                ]
                for c, color in enumerate(COLORS):
                    axes[i, j].plot(
                        [r["count"] for r in rows],
                        [r["probabilities"][c] for r in rows],
                        "o-",
                        markersize=3,
                        color=color,
                        label=f"T{c + 1}",
                    )
                axes[i, j].set_title(f"{head}: {direction} accumulation")
                axes[i, j].set_xlabel("Included frames (20 ms cells each)")
                axes[i, j].set_ylabel("Probability")
                axes[i, j].set_ylim(0, 1)
                axes[i, j].grid(alpha=0.2)
                axes[i, j].legend(ncol=4, fontsize=8)
        fig.suptitle(case["case"] + ": deterministic positional accumulation; no preferred span")
        fig.tight_layout()
        for suffix in ("png", "pdf"):
            fig.savefig(folder / f"stability.{suffix}", dpi=160, bbox_inches="tight")
        plt.close(fig)
        appendix += [
            "",
            f"## {case['recording']} {case['character']}",
            "",
            f"![Aligned timeline]({case['case']}/timeline.png)",
            "",
            f"![Stability]({case['case']}/stability.png)",
        ]
        for head, data in case["heads"].items():
            appendix += [
                "",
                f"### {head}: subsets, ablations, prefix and suffix",
                "",
                table(
                    [
                        "Subset",
                        "N",
                        "Center extent ms",
                        "p(T1,T2,T3,T4)",
                        "Argmax",
                        "TV",
                        "Pair margin",
                        "Top-two logit gap",
                    ],
                    [
                        [
                            k,
                            v["count"],
                            f"{v['center_extent_ms']:.2f}",
                            ", ".join(f"{p:.6f}" for p in v["probabilities"]),
                            v["argmax"],
                            f"{v['tv_from_new']:.6f}",
                            f"{v['pair_margin']:.6f}",
                            f"{v['top_two_logit_margin']:.6f}",
                        ]
                        for k, v in data["subsets"].items()
                    ],
                ),
                "",
                f"### {head}: per-frame standardized logit evidence",
                "",
                "Scores below divide by N to obtain contributions; fixed intercept is separate. "
                "CSV includes raw-origin scores, all four class contributions at both N, "
                "pair contributions and cosine similarities.",
                "",
                table(
                    [
                        "Frame",
                        "Time s",
                        "Set",
                        "Position",
                        "T1",
                        "T2",
                        "T3",
                        "T4",
                        "Pair / Nnew",
                        "Pair delta",
                    ],
                    [
                        [
                            r["frame"],
                            f"{r['seconds']:.8f}",
                            "shared" if r["current"] else "added",
                            r["region"],
                            *[f"{r[f'T{j}_standardized_score']:.5f}" for j in range(1, 5)],
                            f"{r['pair_new_contribution']:.6f}",
                            f"{r['pair_delta_contribution']:.6f}",
                        ]
                        for r in data["frames"]
                    ],
                ),
            ]
        for frame in new:
            time = centers[frame]
            spec = spectral[int(abs(st - time).argmin())]
            ac = points[int(abs(times - time).argmin())]
            acoustic_rows.append(
                {
                    "case": case["case"],
                    "frame": frame,
                    "time": time,
                    "set": "shared" if frame in current else "added",
                    "spectral_time": spec["time"],
                    "rms_time": ac["timestamp_seconds"],
                    "rms_over_gate": ac["energy_rms"] / raw["energy_gate"]["threshold_rms"],
                    "saved_selected_f0_hz": ac["selected_f0_hz"],
                    **{k: v for k, v in spec.items() if k != "time"},
                }
            )
    with (OUT / "acoustic-frame-diagnostics.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(acoustic_rows[0]))
        writer.writeheader()
        writer.writerows(acoustic_rows)
    (OUT / "numerical-appendix.md").write_text("\n".join(appendix) + "\n")


if __name__ == "__main__":
    main()
