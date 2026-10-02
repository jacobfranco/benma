"""Unblind ONLY sealed measurements; this module never decodes or analyzes audio."""

import argparse
import json
from pathlib import Path

from benchmark.pronunciation_v2.phonetic_evidence import dump, sha, verify_seal


def number(v, digits=1):
    return "—" if v is None else f"{v:.{digits}f}"


def report(packet, key_path, embeddings, output, receipt):
    seal = verify_seal(packet)
    # Load sealed observations before opening identities. No acoustic computation follows.
    rows = json.loads((packet / "summary.json").read_text())
    embedding_receipt = json.loads((embeddings / "receipt.json").read_text())
    if embedding_receipt["packet_seal_sha256"] != seal:
        raise ValueError("Embedding receipt refers to a different packet")
    key = json.loads(key_path.read_text())
    identities = {r["id"]: r for r in key["regions"]}
    if set(identities) != {r["id"] for r in rows}:
        raise ValueError("Unblinding key IDs do not match")
    if output.exists() or receipt.exists():
        raise FileExistsError("Refusing to overwrite unblinded report/receipt")
    lines = [
        "# Region results (unblinded after extraction)",
        "",
        "**MEASURED OBSERVATION:** saved timing/pitch plus independent waveform measurements. "
        "No target or phone label was an extraction input. All spans are provider evidence, "
        "not independently verified boundaries. "
        "No pronunciation correctness judgment is available.",
        "",
        "These tables join the separately stored key only after verifying the sealed blind packet. "
        "See [method](method.md) for definitions and fixed guards and "
        "[feasibility](segmental-feasibility.md) for interpretation.",
        "",
        "## Selection and exact timing",
        "",
        "| ID | Region | Source unit | Span ms | Duration ms | Selection |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        k = identities[r["id"]]
        s = k["span"]
        if abs(s["end_ms"] - s["start_ms"] - r["duration_ms"]) > 1e-6:
            raise ValueError("Key duration mismatch")
        lines.append(
            f"| {r['id']} | {k['study']} {k['character']} | {k['unit']} | "
            f"{s['start_ms']:g}-{s['end_ms']:g} | {r['duration_ms']:g} | {k['selection']} |"
        )
    lines += [
        "",
        "## Saved pitch and voicing evidence",
        "",
        "Raw missingness uses existing raw gated F0; selected counts use exactly the saved "
        "selection and quality flag. Runs are contiguous selected-frame supports, not "
        "independent voicing duration. Candidate strength is not a calibrated probability.",
        "",
        "| ID | Usable/total | Raw voiced fraction | Raw missing % | Selected missing % | "
        "Median Hz | Min-max Hz | Longest run ms | Existing instability frames |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        p = r["pitch"]
        f = p["selected_hz"]
        lines.append(
            f"| {r['id']} | {p['usable_frame_count']}/{p['frame_count']} | "
            f"{p['raw_voiced_fraction']:.3f} | {p['raw_missing_fraction'] * 100:.1f} | "
            f"{p['selected_missing_fraction'] * 100:.1f} | {number(f['median'] if f else None)} | "
            f"{number(f['min'] if f else None)}-{number(f['max'] if f else None)} | "
            f"{p['longest_run_support_ms']:.1f} | {p['tracker_instability_frames']} |"
        )
    lines += [
        "",
        "| ID | First usable (ms:Hz) | Midpoint ±10 ms (ms:Hz) | Last usable (ms:Hz) | "
        "Longest-run slope Hz/s | Mean saved strength |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        p = r["pitch"]
        points = [
            f"{v['time_ms']:.1f}:{v['hz']:.1f}" if v else "—"
            for v in (p["first_usable"], p["midpoint_usable"], p["last_usable"])
        ]
        lines.append(
            f"| {r['id']} | "
            + " | ".join(points)
            + f" | {number(p['longest_run_slope_hz_per_second'])} | "
            f"{p['saved_candidate_strength']['mean']:.3f} |"
        )
    lines += [
        "",
        "## Waveform and spectrum",
        "",
        "RMS is digital amplitude, not SPL. Spectra are whole-span frame medians except "
        "the explicitly labeled RMS envelope mean. **All twelve near-full-scale sample "
        "fractions are zero.** No SNR was measured.",
        "",
        "| ID | Whole RMS | RMS envelope mean/median | Centroid Hz | Bandwidth Hz | "
        "85% rolloff Hz | ≥4 kHz fraction | ZCR |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        s = r["spectrum"]
        lines.append(
            f"| {r['id']} | {r['energy']['rms']:.4f} | "
            f"{s['rms']['mean']:.4f}/{s['rms']['median']:.4f} | "
            f"{s['centroid_hz']['median']:.0f} | {s['bandwidth_hz']['median']:.0f} | "
            f"{s['rolloff85_hz']['median']:.0f} | {s['high_frequency_fraction']['median']:.4f} | "
            f"{s['zcr']['median']:.4f} |"
        )
    lines += [
        "",
        "## Formant feasibility",
        "",
        "All values below describe the fixed Burg attempt. `Passing` means joint frame "
        "sanity only, not accepted vowel evidence. Support span is the first-to-last "
        "passing center and may contain gaps. F1/F2/F3 availability counts finite raw "
        "estimates before bandwidth/bounds checks. All accepted summaries remain **null**.",
        "",
        "| ID | Candidate relative ms | Attempted | Raw F1/F2/F3 available | Passing | "
        "Passing-center span ms | Rejected | Adjacent jumps | Outcome / reasons |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        f = r["formants"]
        w = next(
            (w for w in r["analysis_windows"] if w["kind"] == "voiced_nucleus_candidate"), None
        )
        candidate = f"{w['start_ms']:.1f}-{w['end_ms']:.1f}" if w else "absent"
        lines.append(
            f"| {r['id']} | {candidate} | {f['attempted_frames']} | "
            + "/".join(map(str, f["availability_f1_f2_f3"]))
            + f" | {f['usable_frames']} | {f['usable_center_span_ms']:.1f} | "
            f"{f['sanity_rejected_frames']} | {f['adjacent_jump_count']} | "
            f"{f['status']}; {', '.join(f['reason_flags']) or '—'} |"
        )
    lines += [
        "",
        "## Prefix / onset feasibility",
        "",
        "Prefix ends at the longest saved voiced-run candidate, so it may contain earlier "
        "voicing, transitions, neighboring sound, or missed pitch. It is **not an isolated "
        "initial**. No confirmed aperiodic duration is available for any region. Large "
        "centroid IQRs indicate changing spectral content; no stability classifier is used.",
        "",
        "| ID | Prefix ms | Full FFT frames | Saved raw voiced frames in prefix | "
        "Centroid median/IQR Hz | ≥4 kHz fraction median | Result |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        o = r["onset"]
        s = o["spectrum"]
        c = f"{s['centroid_hz']['median']:.0f}/{s['centroid_hz']['iqr']:.0f}" if s else "—"
        h = number(s["high_frequency_fraction"]["median"], 4) if s else "—"
        lines.append(
            f"| {r['id']} | {number(o.get('duration_ms'))} | {o['frames']} | "
            f"{o.get('saved_raw_voiced_frames', '—')} | {c} | {h} | {o['status']} |"
        )
    lines += [
        "",
        "## Evidence-quality representation",
        "",
        "No overall score. Every region is waveform/spectrum-analyzable under the supplied "
        "span, and every boundary remains unvalidated. The full independent flags are:",
        "",
    ]
    for r in rows:
        lines.append(
            f"- **{r['id']}**: " + ", ".join(r["quality_flags"]) + "; embedding_available."
        )
    lines += [
        "",
        "## Frozen representation",
        "",
        "Twelve 768-dimensional block-6 mean-pooled vectors; unchanged frozen CPU encoder; "
        "all per-crop repeats bitwise equal. No labels, distances, head or classification.",
        "",
        "| ID | Hidden frames pooled |",
        "| --- | --- |",
    ]
    for rid, n in zip(embedding_receipt["ids"], embedding_receipt["hidden_frames"], strict=True):
        lines.append(f"| {rid} | {n} |")
    lines += [
        "",
        "## Control ranking",
        "",
        "Eligible nonfocal S02/S03 regions, descending selected-frame fraction then count. "
        "The first three were selected. Source unit labels are revealed only here.",
        "",
        "| Study | Unit | Usable fraction | Usable frames | Selected |",
        "| --- | --- | --- | --- | --- |",
    ]
    for i, (study, unit, fraction, count) in enumerate(key["control_ranking"]):
        lines.append(
            f"| {study} | {unit} | {fraction:.3f} | {count} | {'yes' if i < 3 else 'no'} |"
        )
    output.write_text("\n".join(lines) + "\n")
    dump(
        receipt,
        {
            "packet_seal_sha256": seal,
            "key_sha256": sha(key_path),
            "report_sha256": sha(output),
            "operation": "join_after_seal_no_acoustic_recomputation",
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("packet", "key", "embeddings", "output", "receipt"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    a = parser.parse_args()
    report(a.packet, a.key, a.embeddings, a.output, a.receipt)


if __name__ == "__main__":
    main()
