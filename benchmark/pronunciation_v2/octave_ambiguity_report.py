"""Local replay/forensics for the Oct 6 six-take octave ambiguity pass.

Run with PYTHONPATH=.:services/api/src services/api/.venv/bin/python -m
benchmark.pronunciation_v2.octave_ambiguity_report [--extract]. The optional flag
extracts only current production Praat on the six explicitly listed WAVs.
Existing baseline snapshots are verified, never overwritten. All waveform data,
full raw results and rendered figures stay in ignored services/api/var/.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import math
import statistics
import wave
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.pitch_evidence import (
    build_pitch_track,
    display_from_track,
    gate_observation,
    interpretation_eligibility,
    project_pitch,
)
from benma_api.pronunciation.pitch_types import UtterancePitchTrack
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence

from benchmark.pronunciation_v2.octave_ambiguity import (
    branches,
    experiment,
    parameter_neighborhood,
    semitones,
)

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "services/api/var/octave-ambiguity"
REPORT = ROOT / "docs/research/pronunciation-v2/2026-10-07-octave-ambiguity"
SAVED = ROOT / "services/api/var/f0-foundation"
IDS = (
    "40357072fc994a0ab052752ca119b2e6",
    "8d2522640da64860bd83c33b0b7b7e14",
    "d47274bcdb604380abbeac49930a5dad",
    "4b9dbd2bb17b434498fcbd16a7dd4b69",
    "8faf1a90f564479cac56a41aeab22177",
    "a5acd04c21b742fbbfd53741a2aed1dd",
)
CANONICAL = ROOT / "services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical"
# These windows label acoustic events, not transcript units or reference tones.
WINDOWS = {
    IDS[0]: [
        ("A1", 2.0747, 2.1647),
        ("A2", 2.3847, 2.3847),
        ("A3", 4.2847, 4.3147),
        ("A4", 4.7147, 4.7447),
    ],
    IDS[1]: [
        ("B1-low-dip", 1.1102, 1.2102),
        ("B2", 2.5102, 2.5102),
        ("B3", 2.5602, 2.5902),
        ("B4", 4.1002, 4.3402),
    ],
    IDS[2]: [("C1-low-dip", 1.1516, 1.3616), ("C2", 6.0516, 6.0716)],
    IDS[3]: [],
    IDS[4]: [],
    IDS[5]: [("F1", 1.2217, 1.2417), ("F2", 1.6518, 1.6718)],
    "7787300e": [("protected-low", 2.4824, 2.5124)],
}


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def make_track(result: dict[str, Any]) -> UtterancePitchTrack:
    return build_pitch_track(
        result,
        audio_sha256="saved-production-control",
        tracker_source="saved-production-praat",
        tracker_version="frozen",
        parameters={"provenance": "existing production JSON; no re-extraction"},
    )


def masked_track(track: UtterancePitchTrack, rejected: list[int]) -> UtterancePitchTrack:
    """Pure counterfactual selection, with exact raw fields and no filter cascade.

    Reuse production median-of-three within the remaining segments. Never rerun
    the old rejection rules on changed neighborhoods, which could hide further
    attrition. This copy cannot be mistaken for an accepted production track.
    """
    rejected_set = set(rejected)
    raw = [
        dict(
            timestamp_seconds=f.timestamp_seconds,
            f0_hz=f.selected_f0_hz if i not in rejected_set else None,
            voicing_probability=f.periodicity,
        )
        for i, f in enumerate(track.frames)
    ]
    # Pure display smoothing: repeat the established arithmetic without executing
    # the old rejection rules a second time on changed neighborhoods.
    retained = [p["f0_hz"] for p in raw if p["f0_hz"] is not None]
    baseline = statistics.median(retained) if retained else None
    segments: list[list[int]] = []
    for i, p in enumerate(raw):
        if p["f0_hz"] is None:
            continue
        if (
            not segments
            or i != segments[-1][-1] + 1
            or p["timestamp_seconds"] - raw[segments[-1][-1]]["timestamp_seconds"] > 0.045
        ):
            segments.append([])
        segments[-1].append(i)
    display = {}
    for segment in segments:
        values = [semitones(raw[i]["f0_hz"] / baseline) for i in segment]
        for n, i in enumerate(segment):
            display[i] = round(
                statistics.median(values[n - 1 : n + 2]) if 0 < n < len(segment) - 1 else values[n],
                4,
            )
    frames = tuple(
        f.model_copy(
            update=dict(
                selected_f0_hz=f.selected_f0_hz if i not in rejected_set else None,
                display_semitones=display.get(i),
                exclusion_reasons=f.exclusion_reasons
                + (("octave_candidate_ambiguous",) if i in rejected_set else ()),
            )
        )
        for i, f in enumerate(track.frames)
    )
    return track.model_copy(
        update=dict(
            evidence_id="research-only-"
            + hashlib.sha256((track.evidence_id + str(rejected)).encode()).hexdigest(),
            selection_version="REJECTED-EXPERIMENT-not-production",
            frames=frames,
            baseline_hz=round(baseline, 3) if baseline else None,
        )
    )


def metrics(track: UtterancePitchTrack, raw: list[dict[str, Any]]) -> dict[str, Any]:
    display = display_from_track(track)
    graph = sentence_pitch_evidence(raw, display, [], track=track)
    values = [p.normalized_semitones for s in display.segments for p in s]

    # Exact PitchPlot default domain: server limits union every displayed vertex.
    # Mine inherits unsimplified limits. Detail expands for unsmoothed extrema.
    def domain(contour: Any) -> list[float]:
        y = [p.normalized_semitones for s in contour.segments for p in s]
        return [
            min(contour.minimum_semitones, min(y, default=0) - 1),
            max(contour.maximum_semitones, max(y, default=0) + 1),
        ]

    return dict(
        total_frames=len(track.frames),
        raw_voiced=sum(f.raw_f0_hz is not None for f in track.frames),
        selected_frames=sum(f.selected_f0_hz is not None for f in track.frames),
        baseline_hz=track.baseline_hz,
        display_range=[min(values), max(values)] if values else [],
        mine_domain=domain(graph.mine),
        detail_domain=domain(graph.filtered),
        islands=[
            dict(
                start=s[0].timestamp_seconds,
                end=s[-1].timestamp_seconds,
                frames=len(s),
                minimum_st=min(p.normalized_semitones for p in s),
                maximum_st=max(p.normalized_semitones for p in s),
            )
            for s in display.segments
        ],
    )


def old_rules(raw: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Mirror the inspected guards for explanation, checked against diagnostics."""
    diagnostics: list[dict[str, Any]] = []
    display_contour(raw, diagnostics=diagnostics)
    valid = [
        bool(
            p.get("quality_usable", True)
            and p["f0_hz"] is not None
            and 40 <= p["f0_hz"] <= 1000
            and (p.get("voicing_probability") is None or p["voicing_probability"] >= 0.45)
        )
        for p in raw
    ]
    regions: list[list[int]] = []
    for i, p in enumerate(raw):
        if not valid[i]:
            continue
        if (
            i == 0
            or not valid[i - 1]
            or p["timestamp_seconds"] - raw[i - 1]["timestamp_seconds"] > 0.045
            or abs(semitones(p["f0_hz"] / raw[i - 1]["f0_hz"])) > 6
        ):
            regions.append([])
        regions[-1].append(i)
    output = {}
    for i, p in enumerate(raw):
        item: dict[str, Any] = dict(
            reasons=diagnostics[i]["reasons"], retained=diagnostics[i]["retained"]
        )
        if not valid[i]:
            item.update(island="prior_gate", hampel="prior_gate")
            output[i] = item
            continue
        r = next(n for n, s in enumerate(regions) if i in s)
        mid = regions[r]
        if r == 0 or r == len(regions) - 1:
            item["island"] = "no_both_sides"
        else:
            before, after = regions[r - 1], regions[r + 1]
            a, b, c, d = [
                raw[k]["timestamp_seconds"] for k in (before[-1], mid[0], mid[-1], after[0])
            ]

            def med(s: list[int]) -> float:
                return statistics.median(semitones(raw[k]["f0_hz"]) for k in s)

            x, y, z = med(before[-5:]), med(mid), med(after[:5])
            failed = []
            if c - b > 0.08:
                failed.append("span_gt_80ms")
            if b - a > 0.12:
                failed.append("before_gt_120ms")
            if d - c > 0.12:
                failed.append("after_gt_120ms")
            if abs(x - z) > 2:
                failed.append("flanks_disagree_gt_2st")
            if abs(y - x) <= 6 or abs(y - z) <= 6:
                failed.append("not_outlier_to_both_flanks")
            item["island"] = ";".join(failed) or "reject"
        neighbors = []
        for direction in (-1, 1):
            side = []
            previous = i
            for distance in range(1, 4):
                j = i + direction * distance
                if not 0 <= j < len(raw) or not valid[j]:
                    break
                if (
                    not 0
                    < abs(raw[j]["timestamp_seconds"] - raw[previous]["timestamp_seconds"])
                    <= 0.045
                ):
                    break
                side.append(semitones(raw[j]["f0_hz"]))
                previous = j
            neighbors.append(side)
        left, right = neighbors
        item.update(hampel_left=len(left), hampel_right=len(right))
        if min(len(left), len(right)) < 2:
            item["hampel"] = "fewer_than_2_neighbors_each_side"
        else:
            center = statistics.median(left + right)
            mad = statistics.median(abs(v - center) for v in left + right)
            threshold = max(6, 3 * 1.4826 * mad)
            deviation = abs(semitones(p["f0_hz"]) - center)
            item.update(
                hampel_threshold_st=threshold,
                hampel_deviation_st=deviation,
                hampel="reject" if deviation > threshold else "below_local_threshold",
            )
        assert (item["island"] == "reject") == ("bracketed_short_pitch_island" in item["reasons"])
        assert (item["hampel"] == "reject") == ("local_hampel_outlier" in item["reasons"])
        output[i] = item
    return output


def samples(path: Path) -> tuple[int, Any]:
    with wave.open(str(path), "rb") as stream:
        assert stream.getnchannels() == 1 and stream.getsampwidth() == 2
        return stream.getframerate(), np.frombuffer(
            stream.readframes(stream.getnframes()), dtype="<i2"
        ).astype(float) / 32768


def spectrum(rate: int, values: Any, timestamp: float, hz: float) -> dict[str, Any]:
    half = round(rate * 0.05)
    center = round(timestamp * rate)
    frame = values[max(0, center - half) : center + half]
    power = abs(np.fft.rfft((frame - frame.mean()) * np.hanning(len(frame)), 16384)) ** 2
    frequencies = np.fft.rfftfreq(16384, 1 / rate)
    band = (frequencies >= 40) & (frequencies <= 1000)
    maximum = max(float(power[band].max()), 1e-20)
    peaks = [
        i
        for i in range(1, len(power) - 1)
        if band[i] and power[i] > power[i - 1] and power[i] > power[i + 1]
    ]
    peaks = sorted(peaks, key=lambda i: power[i], reverse=True)[:6]

    def peak(target: float) -> float:
        return round(
            10
            * math.log10(max(float(power[abs(frequencies - target) <= 8].max()), 1e-20) / maximum),
            2,
        )

    return dict(
        peaks_hz_db=[
            [round(float(frequencies[i]), 2), round(10 * math.log10(float(power[i]) / maximum), 2)]
            for i in peaks
        ],
        selected_band_db=peak(hz),
        half_band_db=peak(hz / 2),
        double_band_db=peak(hz * 2),
        note=(
            "100 ms Hann; +/-8 Hz band maxima; zero padding is not added resolution; "
            "harmonic support is not F0 ground truth"
        ),
    )


def visual_signal(rate: int, values: Any) -> dict[str, Any]:
    hop, width = round(rate * 0.005), round(rate * 0.10)
    columns = []
    for center in range(0, len(values), hop):
        frame = np.zeros(width)
        lo, hi = max(0, center - width // 2), min(len(values), center + width // 2)
        offset = lo - (center - width // 2)
        frame[offset : offset + hi - lo] = values[lo:hi]
        power = abs(np.fft.rfft((frame - frame.mean()) * np.hanning(width), 2048)) ** 2
        frequencies = np.fft.rfftfreq(2048, 1 / rate)
        columns.append(np.interp(np.arange(0, 1001, 5), frequencies, power))
    power = np.array(columns).T
    db = 10 * np.log10(np.maximum(power / max(float(power.max()), 1e-20), 1e-8))
    pixels = np.clip((db + 60) / 60 * 255, 0, 255).astype(np.uint8)
    block = max(1, len(values) // 1600)
    waveform = [
        [
            round(i / rate, 5),
            round(float(values[i : i + block].min()), 5),
            round(float(values[i : i + block].max()), 5),
        ]
        for i in range(0, len(values), block)
    ]
    return dict(
        waveform=waveform,
        spectrogram=dict(
            width=pixels.shape[1],
            height=pixels.shape[0],
            pixels=base64.b64encode(pixels.tobytes()).decode(),
            maximum_hz=1000,
        ),
    )


def forensics(
    id: str, result: dict[str, Any], track: UtterancePitchTrack, rate: int, values: Any
) -> list[dict[str, Any]]:
    raw = result["f0"]
    audit = old_rules(raw)
    frames = track.model_dump(mode="json")["frames"]
    graph = sentence_pitch_evidence(raw, display_from_track(track), [], track=track)
    mine_times = {p.timestamp_seconds for s in graph.mine.segments for p in s}
    run_list = branches(frames)
    rows = []
    for label, start, end in WINDOWS[id]:
        preceding = [
            part
            for s in run_list
            if len(part := [i for i in s if frames[i]["timestamp_seconds"] < start]) >= 5
        ]
        following = [
            part
            for s in run_list
            if len(part := [i for i in s if frames[i]["timestamp_seconds"] > end]) >= 5
        ]
        before = (
            statistics.median(frames[i]["selected_f0_hz"] for i in preceding[-1][-5:])
            if preceding
            else None
        )
        after = (
            statistics.median(frames[i]["selected_f0_hz"] for i in following[0][:5])
            if following
            else None
        )
        for i, f in enumerate(frames):
            if not start - 1e-8 <= f["timestamp_seconds"] <= end + 1e-8 or f["raw_f0_hz"] is None:
                continue
            hz = f["raw_f0_hz"]
            candidates = []
            for c in f["candidates"]:
                if c["frequency_hz"] == hz:
                    continue
                delta = semitones(c["frequency_hz"] / hz)
                octave = min((-24, -12, 12, 24), key=lambda k: abs(delta - k))
                candidates.append(
                    dict(
                        **c,
                        strength_margin=f["periodicity"] - c["strength"],
                        ratio=c["frequency_hz"] / hz,
                        nearest_octave_ratio=2 ** (octave / 12),
                        error_st=abs(delta - octave),
                    )
                )
            octave_alts = [c for c in candidates if c["error_st"] <= 1]
            credible = [
                c for c in octave_alts if c["strength"] >= 0.45 and c["strength_margin"] <= 0.25
            ]
            without = masked_track(track, [i]) if f["selected_f0_hz"] else track
            domain_before = metrics(track, raw)["mine_domain"]
            domain_without = metrics(without, raw)["mine_domain"]
            rows.append(
                dict(
                    recording=id,
                    event=label,
                    start=start,
                    end=end,
                    duration_seconds=round(end - start + 0.01, 4),
                    index=i,
                    timestamp_seconds=f["timestamp_seconds"],
                    raw_f0_hz=hz,
                    selected_f0_hz=f["selected_f0_hz"],
                    selected_strength=f["periodicity"],
                    previous_stable_hz=before,
                    following_stable_hz=after,
                    previous_stable_end=frames[preceding[-1][-1]]["timestamp_seconds"]
                    if preceding
                    else None,
                    following_stable_start=frames[following[0][0]]["timestamp_seconds"]
                    if following
                    else None,
                    jump_from_previous_st=semitones(hz / before) if before else None,
                    jump_to_following_st=semitones(after / hz) if after else None,
                    candidates=f["candidates"],
                    octave_alternatives=octave_alts,
                    nearest_octave_candidate=min(candidates, key=lambda c: c["error_st"])
                    if candidates
                    else None,
                    credible_octave_alternative=bool(credible),
                    rules=audit[i],
                    selected_support_for_mine=f["selected_f0_hz"] is not None,
                    reaches_detail=f["selected_f0_hz"] is not None,
                    reaches_server_mine=f["timestamp_seconds"] in mine_times,
                    changes_domain_if_only_this_frame_removed=any(
                        abs(a - b) > 1e-4
                        for a, b in zip(domain_before, domain_without, strict=True)
                    ),
                    domain_span_reduction_if_only_this_frame_removed_st=(
                        domain_before[1] - domain_before[0]
                    )
                    - (domain_without[1] - domain_without[0]),
                    spectrum=spectrum(rate, values, f["timestamp_seconds"], hz),
                )
            )
    return rows


def check_preservation(before: UtterancePitchTrack, after: UtterancePitchTrack) -> None:
    for a, b in zip(before.frames, after.frames, strict=True):
        exclude = {"selected_f0_hz", "display_semitones", "exclusion_reasons"}
        assert a.model_dump(exclude=exclude) == b.model_dump(exclude=exclude)
        assert b.selected_f0_hz is None or b.selected_f0_hz == a.selected_f0_hz


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", action="store_true")
    args = parser.parse_args()
    REPORT.mkdir(parents=True, exist_ok=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    analyzer = PraatAcousticAnalyzer()
    primary, visuals, forensic_rows = [], [], []
    for id in IDS:
        path = CANONICAL / (id + ".wav")
        snapshot = LOCAL / "before" / (id + ".json")
        if not snapshot.exists():
            if not args.extract:
                raise SystemExit(
                    "Missing frozen baseline; explicitly pass --extract for local production replay"
                )
            result = analyzer.analyze(path)
            track = build_pitch_track(
                result,
                audio_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                tracker_source=analyzer.algorithm_name,
                tracker_version=analyzer.algorithm_version,
                parameters=analyzer.parameters,
            )
            dump(
                snapshot,
                dict(
                    path=str(path.relative_to(ROOT)),
                    sha256=track.audio_sha256,
                    parameters=analyzer.parameters,
                    version=analyzer.algorithm_version,
                    result=result,
                    track=track.model_dump(mode="json"),
                ),
            )
        saved = json.loads(snapshot.read_text())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == saved["sha256"]
        raw = saved["result"]["f0"]
        track = UtterancePitchTrack.model_validate(saved["track"])
        current = build_pitch_track(
            saved["result"],
            audio_sha256=track.audio_sha256,
            tracker_source=track.tracker_source,
            tracker_version=track.tracker_version,
            parameters=json.loads(track.tracker_configuration_json),
        )
        assert current == track, "Production selection changed since frozen baseline"
        frames = track.model_dump(mode="json")["frames"]
        trial = experiment(frames)
        strict = experiment(frames, require_complete_run=True)
        after = masked_track(track, trial["rejected_indices"])
        strict_track = masked_track(track, strict["rejected_indices"])
        check_preservation(track, after)
        check_preservation(track, strict_track)
        rate, values = samples(path)
        rows = forensics(id, saved["result"], track, rate, values)
        forensic_rows.extend(rows)
        row = dict(
            recording=id,
            path=str(path.relative_to(ROOT)),
            sha256=track.audio_sha256,
            before=metrics(track, raw),
            frame_rule_after=metrics(after, raw),
            consensus_after=metrics(strict_track, raw),
            experiment=trial,
            consensus=strict,
            neighborhood={
                name: dict(
                    rejected_indices=experiment(frames, p)["rejected_indices"],
                    consensus_rejected_indices=experiment(frames, p, require_complete_run=True)[
                        "rejected_indices"
                    ],
                )
                for name, p in parameter_neighborhood().items()
            },
        )
        primary.append(row)
        visuals.append(
            dict(
                id=id,
                duration=track.duration_seconds,
                frames=frames,
                after=after.model_dump(mode="json")["frames"],
                summary=row,
                windows=WINDOWS[id],
                **visual_signal(rate, values),
            )
        )
    controls = []
    proxy = {
        r["recording"]: set(r["times"])
        for r in json.loads((SAVED / "low-f0-proxy-samples.json").read_text())
    }
    low = json.loads(
        (
            ROOT / "docs/research/pronunciation-v2/2026-10-05-utterance-evidence/low-f0-replay.json"
        ).read_text()
    )
    low = {(r["recording"], r["timestamp"]) for r in low}
    manifest = {r["id"]: r for r in json.loads((SAVED / "manifest-local.json").read_text())}
    for file in sorted((SAVED / "production").glob("*.json")):
        saved = json.loads(file.read_text())
        track = make_track(saved["result"])
        assert [f.timestamp_seconds for f in track.frames if f.selected_f0_hz] == saved[
            "retained_times"
        ]
        frames = track.model_dump(mode="json")["frames"]
        trial = experiment(frames)
        strict = experiment(frames, require_complete_run=True)
        after = masked_track(track, trial["rejected_indices"])
        check_preservation(track, after)
        times = [frames[i]["timestamp_seconds"] for i in trial["rejected_indices"]]
        windows = []
        for w in manifest[file.stem].get("diagnostic_windows", []):
            states = []
            for t in (track, after, masked_track(track, strict["rejected_indices"])):
                p = project_pitch(t, w["start"], w["end"], timing_source="frozen_control_interval")
                e = interpretation_eligibility(t, p)
                observed = classify_contour(
                    display_from_track(t),
                    w["start"],
                    w["end"],
                    raw=saved["result"]["f0"],
                    pitch_track=t,
                )
                states.append(
                    dict(
                        eligibility=e.model_dump(mode="json"),
                        observed=gate_observation(observed, e).model_dump(),
                    )
                )
            windows.append(
                dict(**w, before=states[0], frame_rule_after=states[1], consensus_after=states[2])
            )
        controls.append(
            dict(
                id=file.stem,
                kind=manifest[file.stem]["kind"],
                selected_before=len(saved["retained_times"]),
                rejected_times=times,
                consensus_rejected_times=[
                    frames[i]["timestamp_seconds"] for i in strict["rejected_indices"]
                ],
                protected_proxy_times=sorted(proxy.get(file.stem, set())),
                protected_lost=sorted(set(times) & proxy.get(file.stem, set())),
                under70_protected_lost=[t for t in times if (file.stem, t) in low],
                windows=windows,
                neighborhood={
                    name: dict(
                        protected_lost=[
                            frames[i]["timestamp_seconds"]
                            for i in experiment(frames, p)["rejected_indices"]
                            if frames[i]["timestamp_seconds"] in proxy.get(file.stem, set())
                        ],
                        consensus_protected_lost=[
                            frames[i]["timestamp_seconds"]
                            for i in experiment(frames, p, require_complete_run=True)[
                                "rejected_indices"
                            ]
                            if frames[i]["timestamp_seconds"] in proxy.get(file.stem, set())
                        ],
                    )
                    for name, p in parameter_neighborhood().items()
                },
            )
        )
        if file.stem == "7787300e":
            rate, values = samples(Path(manifest[file.stem]["audio_path"]))
            visuals.append(
                dict(
                    id=file.stem,
                    duration=track.duration_seconds,
                    frames=frames,
                    after=after.model_dump(mode="json")["frames"],
                    summary=dict(
                        before=metrics(track, saved["result"]["f0"]),
                        frame_rule_after=metrics(after, saved["result"]["f0"]),
                        consensus=strict,
                        consensus_after=metrics(
                            masked_track(track, strict["rejected_indices"]),
                            saved["result"]["f0"],
                        ),
                    ),
                    windows=WINDOWS[file.stem],
                    **visual_signal(rate, values),
                )
            )
            forensic_rows.extend(forensics(file.stem, saved["result"], track, rate, values))
    summary = dict(
        primary=primary,
        controls=controls,
        parameters={k: asdict(v) for k, v in parameter_neighborhood().items()},
        production_changed=False,
        decision="B_PHYSICAL_ARTIFACTS_EXPLAINED_BUT_RULE_NOT_SAFE",
    )
    dump(REPORT / "replay.json", summary)
    dump(REPORT / "frame-forensics.json", forensic_rows)
    dump(LOCAL / "viewer-data.json", visuals)
    with (REPORT / "frame-forensics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(forensic_rows[0]))
        writer.writeheader()
        for row in forensic_rows:
            writer.writerow(
                {
                    k: json.dumps(v, separators=(",", ":")) if isinstance(v, (list, dict)) else v
                    for k, v in row.items()
                }
            )
    template = (Path(__file__).with_name("octave_ambiguity_viewer.html")).read_text()
    (LOCAL / "viewer.html").write_text(
        template.replace("__EVIDENCE_JSON__", json.dumps(visuals, separators=(",", ":")))
    )
    print(
        json.dumps(
            dict(
                physical=[
                    dict(
                        id=r["recording"][:8],
                        before=r["before"]["selected_frames"],
                        frame_rule=len(r["experiment"]["rejected_indices"]),
                        consensus=len(r["consensus"]["rejected_indices"]),
                        domain_before=r["before"]["mine_domain"],
                        domain_after=r["frame_rule_after"]["mine_domain"],
                    )
                    for r in primary
                ],
                control_count=len(controls),
                protected_frames=sum(len(s) for s in proxy.values()),
                protected_lost=[
                    dict(id=r["id"], times=r["protected_lost"])
                    for r in controls
                    if r["protected_lost"]
                ],
                forensic_rows=len(forensic_rows),
                viewer=str(LOCAL / "viewer.html"),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
