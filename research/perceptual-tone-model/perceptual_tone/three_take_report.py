"""Readable tables and local playback report; descriptive annotations are not policy."""
# ruff: noqa: E501, RUF001 -- report prose/HTML and typographic ranges, not runtime code.

import csv
import hashlib
import html
import json
from itertools import pairwise

from .common import read_json
from .three_take_stability import RUN, acoustic_summary, stability, verify_snapshot, write_generated

# Reviewed alongside waveform/spectrogram and untouched phone metadata.
# No listening attestation or realized-tone gold label is inferred.
CROP_NOTES = {
    (
        1,
        0,
    ): "Whole/pool acoustically plausible. Pool excludes 50 ms of voiced glide; no clear neighboring vowel intrusion.",
    (
        1,
        1,
    ): "Vowel/coda island is inside pool. One retained frame at whole onset likely belongs to the preceding voiced transition; it fragments whole-unit evidence. No missing final apparent.",
    (
        1,
        2,
    ): "Whole/pool plausible; voiced nasal onset excluded. Most dip/recovery remains in pool. No clear neighbor intrusion.",
    (
        1,
        3,
    ): "Whole/pool plausible but final only 110 ms; shallow fall, followed by short residual voicing in ge onset. Precise shared boundary is uncertain.",
    (
        1,
        4,
    ): "30 ms pool begins around a burst and has no retained F0. Whole contains only two early voiced frames contiguous with zhe; likely carryover. Reduced/devoiced final or phone-placement error remain possible.",
    (
        2,
        0,
    ): "Whole 320 ms; MFA calls first 250 ms a glide. Pool discards 22 voiced frames and most fall. Vowel material appears broader than the narrow final; internal boundary suspicious.",
    (
        2,
        1,
    ): "FAIL/SUSPECT: nominal vowel+coda crop is broadband/no retained F0. Whole has one early carryover frame. Later vowel-like voiced material at 1.732–1.932 s is in MFA's unowned 1.58–1.94 s gap. Identity needs listening/adjudication; no automatic reassignment.",
    (
        2,
        2,
    ): "Pool contains vowel-like material, but 100 ms voiced onset label and preceding orphan voiced island make whole ownership suspect. Pool excludes most whole-span fall; truncation can flip family.",
    (
        2,
        3,
    ): "Whole/pool plausible, final 100 ms; retained support starts 8 ms before pool. No obvious large final omission, boundary into ge uncertain.",
    (
        2,
        4,
    ): "Whole 60 ms/pool 30 ms; short continuous tail of zhe-ge. Only 2 pool F0 frames, 3 more in onset. Actual reduction plus policy compression; independent ge identity unresolved.",
    (
        3,
        0,
    ): "Whole/pool show substantial energy and vowel-like spectrum, but no retained AC pitch. Pool is not silent. CC finds only 3 late frames; tracker/phonation limitation, not a demonstrated missing-vowel crop.",
    (
        3,
        1,
    ): "Whole/pool acoustically plausible. Retained final has 23 frames. Earlier pool starts include frication, causing T2/T3 flips without a stronger F0 contour change.",
    (
        3,
        2,
    ): "Whole/pool plausible but retained F0 has a short rejected transition and ~3 st jump near 1.84 s. Do not connect across that gap or treat range as a clean tone gesture.",
    (
        3,
        3,
    ): "Whole/pool plausible; strong measured fall within 120 ms final. Voicing crosses shared ge boundary; no clear large omission.",
    (
        3,
        4,
    ): "Whole 60 ms/pool 30 ms; 3 pool frames, 3 more in onset. Reduced voiced tail is real; exact k/vowel ownership remains uncertain. No numbered classification.",
}

MARGIN_NOTES = {
    (
        1,
        0,
    ): "T2 preference ranges .538–.832: substantial movement toward a near tie, without a flip.",
    (
        1,
        3,
    ): "T3 preference ranges .363–.627: diffuse versus more decisive preference, without a flip.",
    (2, 3): "T3 preference ranges .775–.963: substantial sharpening, without a flip.",
    (3, 2): "T3 preference ranges .734–.920: substantial sharpening, without a flip.",
}


def fmt(value, digits=3):
    return "—" if value is None else f"{value:.{digits}f}"


def bounds(values):
    return "–".join(fmt(v) for v in values)


def learned(value):
    if value["status"] != "ok":
        return "ABSTAIN: " + value["reason"]
    return value["prediction"] + " / " + fmt(value["confidence"], 6)


def probability_text(value):
    return (
        "—"
        if not value.get("probabilities")
        else "; ".join(f"{k}={v:.6f}" for k, v in value["probabilities"].items())
    )


def fields(row):
    p, w, d = row["pool_acoustics"], row["whole_acoustics"], row["deterministic"]
    return {
        "Whole read-unit seconds": bounds(row["whole"]),
        "Tone-bearing seconds": bounds(row["pool"]),
        "Tone-bearing duration ms": fmt(row["pool_duration_ms"], 1),
        "Context seconds (fixed)": bounds(row["context"]),
        "Phones (seconds; labels are reference phones)": "; ".join(
            f"{v['phone']} [{v['start']:.3f},{v['end']:.3f})" for v in row["phones"]
        ),
        "Owned phone indices (zero based)": str(row["owned_phone_indices"]),
        "HuBERT pooled frames (actual; geometric if gated)": (
            str(row["original_pooled_frames"])
            if row["original_pooled_frames"] is not None
            else f"not run; geometry={row['geometric_pooled_frames']}"
        ),
        "Voiced support ms: pool / whole": f"{p['voiced_support_ms']:.1f} / {w['voiced_support_ms']:.1f}",
        "Usable F0 frames: pool / whole": f"{p['usable_frames']} / {w['usable_frames']}",
        "Retained frames outside pool, inside whole": str(
            row["voiced_outside_pool_within_whole_frames"]
        ),
        "Expanded family / raw preference": learned(row["expanded"]),
        "Expanded full probabilities": probability_text(row["expanded"]),
        "Pilot family / raw preference": learned(row["pilot"]),
        "Pilot full probabilities": probability_text(row["pilot"]),
        "Deterministic family / abstention": (
            d.get("prediction") or "ABSTAIN: " + d.get("observed", {}).get("reason", "unavailable")
        ),
        "Deterministic shape / safety": (
            f"{d.get('shape', {}).get('shape')} / {d.get('shape', {}).get('familySafetyReason')}"
        ),
        "F0 pool fall / recovery / range st": " / ".join(
            fmt(p[k], 2) for k in ("fall_st", "recovery_st", "range_st")
        ),
        "F0 whole fall / recovery / range st": " / ".join(
            fmt(w[k], 2) for k in ("fall_st", "recovery_st", "range_st")
        ),
        "Pitch evidence state": d.get("eligibility", {}).get("state", "unavailable")
        + ": "
        + ", ".join(d.get("eligibility", {}).get("reasons", [])),
        "Comparison state / reason (separate from pitch eligibility)": (
            row["comparison"]["state"] + ": " + row["comparison"]["reason"]
        ),
        "Alignment log likelihood (utterance level)": fmt(row["alignment_log_likelihood"], 6),
        "Diagnostic stability": row["stability"],
        "Crop assessment (signal inspection; not listening gold)": row["crop_assessment"],
        "Margin assessment (descriptive only)": row["margin_assessment"],
    }


def comparison_markdown(rows):
    lines = [
        "# Frozen three-take comparison",
        "",
        "Take numbering follows the supplied order, not capture chronology: "
        "1=`98432f75…`, 2=`d05e1d81…`, 3=`b8f38711…`.",
        "",
        "Times are seconds in canonical WAV. Voiced support sums clipped 10 ms retained-F0 cells; "
        "it is not span length. F0 fall/recovery use the largest contiguous island, not an interpolated "
        "contour across gaps. Full-precision values and every perturbation are in diagnostics.json "
        "and annotated-diagnostics.json. All classifier probabilities are raw preferences.",
        "",
    ]
    for i, char in enumerate("我想买这个"):
        group = sorted((u for u in rows if u["index"] == i), key=lambda u: u["take"])
        values = [fields(u) for u in group]
        lines += [
            f"## {char}",
            "",
            "| Measurement | Take 1 | Take 2 | Take 3 |",
            "|---|---|---|---|",
        ]
        for key in values[0]:
            lines.append(
                "| " + " | ".join([key] + [v[key].replace("|", "/") for v in values]) + " |"
            )
        lines.append("")
    return "\n".join(lines)


def render(folder=RUN):
    result = read_json(folder / "diagnostics.json")
    acoustic = read_json(folder / "full-acoustics.json")
    manifest = read_json(folder / "freeze-manifest.json")
    rows = result["rows"]
    for row in rows:
        key = (row["take"], row["index"])
        row["crop_assessment"] = CROP_NOTES[key]
        row["margin_assessment"] = MARGIN_NOTES.get(
            key,
            "See continuous confidence/margin deltas; family flips take precedence."
            if row["stability"] == "BOUNDARY-SENSITIVE"
            else "Not testable."
            if row["stability"] == "UNUSABLE"
            else "Family remains stable over this grid; no substantial qualitative margin change assigned.",
        )
        row["stability"] = stability(
            row["variants"],
            row["expanded"].get("prediction"),
            usable=row["expanded"]["status"] == "ok",
            margin_sensitive=key in MARGIN_NOTES,
        )
    result["annotations_are_production_policy"] = False
    # Preserve orphan evidence explicitly; do not assign it to a syllable.
    orphan = {}
    for tid, data in acoustic.items():
        units = [u for u in rows if u["take_id"] == tid]
        orphan[tid] = []
        for left, right in pairwise(units):
            region = [left["whole"][1], right["whole"][0]]
            if region[1] > region[0]:
                orphan[tid].append(
                    {
                        "after": left["character"],
                        "before": right["character"],
                        "region": region,
                        "acoustics": acoustic_summary(data["graph"], region),
                    }
                )
    result["unowned_gap_evidence"] = orphan
    write_generated(folder / "annotated-diagnostics.json", result)
    (folder / "comparison.md").write_text(comparison_markdown(rows))
    with (folder / "comparison.csv").open("w") as stream:
        writer = csv.DictWriter(stream, ["take", "take_id", "character", *fields(rows[0])])
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in ("take", "take_id", "character")} | fields(row))
    variants = []
    for row in rows:
        for v in row["variants"]:
            flat = {k: row[k] for k in ("take", "take_id", "character")}
            flat.update(
                {k: v[k] for k in ("start", "end", "duration_ms", "pooled_frames", "reason")}
            )
            flat["requested_offsets_ms"] = json.dumps(v["requested_offsets_ms"])
            flat["actual_delta_ms"] = json.dumps(v["actual_delta_ms"])
            flat["f0_usable_frames"] = v["f0"]["usable_frames"]
            flat["hidden_sha256"] = v["hidden_sha256"]
            for name in ("expanded", "pilot"):
                for k in (
                    "prediction",
                    "confidence",
                    "margin",
                    "family_changed",
                    "confidence_delta",
                    "max_probability_delta",
                ):
                    flat[name + "_" + k] = v.get(name, {}).get(k)
                for tone in ("T1", "T2", "T3", "T4"):
                    flat[name + "_" + tone] = v.get(name, {}).get("probabilities", {}).get(tone)
            variants.append(flat)
    with (folder / "perturbations.csv").open("w") as stream:
        writer = csv.DictWriter(stream, list(variants[0]))
        writer.writeheader()
        writer.writerows(variants)
    # These component digests identify canonical JSON projections. The report file
    # SHA in the freeze manifest is the authoritative byte-for-byte original seal.
    components = {}
    for tid in manifest["take_order"]:
        report = read_json(folder / "frozen" / tid / "report.json")
        components[tid] = {}
        for key in ("spans", "expanded", "pilot", "deterministic", "comparison"):
            payload = json.dumps(
                [u[key] for u in report["units"]],
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
            components[tid][key] = hashlib.sha256(payload).hexdigest()
    write_generated(
        folder / "component-hashes.json",
        {
            "encoding": "UTF-8 canonical JSON, sorted keys, compact separators; original bytes sealed separately",
            "takes": components,
        },
    )
    document = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Three-take stability diagnostics</title>',
        "<style>body{font:16px system-ui;margin:2rem;color:#172033}table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ccd3dc;padding:.6rem;vertical-align:top}th{background:#edf2f7}"
        "td{min-width:15rem}td:first-child{min-width:12rem;font-weight:600}"
        ".scroll{overflow-x:auto}img{max-width:100%}audio{width:230px}pre{white-space:pre-wrap}"
        "details{margin:1rem 0}h2{margin-top:3rem}</style>",
        "<h1>Three-take stability diagnostics</h1><p>Fixed audio, fixed context, frozen models. "
        "Raw model preferences; no realized-tone gold labels. Take order follows the request.</p>",
        '<p><a href="comparison.md">Comparison Markdown</a> · <a href="comparison.csv">CSV</a> · '
        '<a href="perturbations.csv">All perturbations</a> · '
        '<a href="annotated-diagnostics.json">Full evidence</a> · <a href="freeze-manifest.json">Hashes</a></p>',
        '<img src="cross-take-contours.png" alt="F0 comparison for all 15 units, gaps preserved">',
    ]
    for take, tid in enumerate(manifest["take_order"], 1):
        document += [
            f"<details><summary>Take {take}: {tid} — complete audio and acoustic inspection</summary>",
            f'<audio controls preload="none" src="frozen/{tid}/canonical.wav"></audio>',
            f'<img src="take-{take}-acoustics.png" alt="Take {take} waveform, spectrum, F0"></details>',
        ]
    for i, char in enumerate("我想买这个"):
        group = sorted((r for r in rows if r["index"] == i), key=lambda r: r["take"])
        tables = [fields(r) for r in group]
        document += [
            f'<h2>{char}</h2><div class="scroll"><table><tr><th>Measurement</th>'
            "<th>Take 1</th><th>Take 2</th><th>Take 3</th></tr>"
        ]
        for key in tables[0]:
            document.append(
                "<tr><td>"
                + html.escape(key)
                + "</td>"
                + "".join("<td>" + html.escape(t[key]) + "</td>" for t in tables)
                + "</tr>"
            )
        for kind in ("whole", "tone", "context"):
            document.append(
                f"<tr><td>{kind} playback (frozen originals)</td>"
                + "".join(
                    f'<td><audio controls preload="none" src="frozen/{r["take_id"]}/unit-{i}-{kind}.wav"></audio></td>'
                    for r in group
                )
                + "</tr>"
            )
        document.append("</table></div>")
        for row in group:
            document.append(
                f"<details><summary>Take {row['take']}: every clamped perturbation</summary><pre>"
                + html.escape(json.dumps(row["variants"], ensure_ascii=False, indent=2))
                + "</pre></details>"
            )
    document.append("</html>")
    (folder / "index.html").write_text("\n".join(document))
    write_generated(folder / "report-verification.json", verify_snapshot(folder))


if __name__ == "__main__":
    render()
