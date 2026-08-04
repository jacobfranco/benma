"""Command-line entry point for corpus, annotation, provider, and report workflows."""

from __future__ import annotations

import argparse
import json
import secrets
import tempfile
from pathlib import Path

from benchmark.acoustics.alignment import MontrealForcedAligner
from benchmark.acoustics.alignment_comparison import compare_alignment_files
from benchmark.acoustics.calibration import materialize_acoustic_calibrations
from benchmark.acoustics.comparison import compare_pitch_algorithms
from benchmark.acoustics.pitch import (
    AutocorrelationPitchAnalyzer,
    ParselmouthPitchAnalyzer,
    TorchCrepePitchAnalyzer,
)
from benchmark.acoustics.plot import write_diagnostic_svg
from benchmark.annotation_workbench import AnnotationWorkbench, serve_workbench
from benchmark.annotations import commit_blind, commit_revealed
from benchmark.audio import capture_with_ffmpeg, import_recording, play_audio
from benchmark.corpus.seed import seed_manifest
from benchmark.evaluation.calibration import create_stratified_split, persist_split
from benchmark.evaluation.cost import calculate_scenarios, load_catalog
from benchmark.fixtures import materialize_replay_fixtures
from benchmark.models import (
    BlindListenerResponse,
    CorpusManifest,
    ListenerRole,
    RaterProfile,
    RevealedTargetResponse,
)
from benchmark.providers.known_target.azure import AzurePronunciationAdapter
from benchmark.providers.known_target.captures import import_live_capture
from benchmark.providers.unknown_target.google import GoogleChirpAdapter
from benchmark.providers.unknown_target.openai import OpenAITranscriptionAdapter
from benchmark.reports.generation import generate_report
from benchmark.reports.pronunciation_calibration import generate_pronunciation_calibration
from benchmark.runner import run_known_target, run_unknown_target
from benchmark.schemas import export_json_schemas
from benchmark.storage import load_model, write_json, write_model

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "benchmark/corpus/manifests/benma-v0.1.0.json"
DEFAULT_RECORDINGS = ROOT / "benchmark/corpus/recordings"
DEFAULT_ANNOTATIONS = ROOT / "benchmark/corpus/annotations"
DEFAULT_RUNS = ROOT / "benchmark/reports/outputs/runs"
FIXTURES = ROOT / "benchmark/reports/fixtures"
OUTPUTS = ROOT / "benchmark/reports/outputs"
PRICING = ROOT / "benchmark/evaluation/cost/pricing-v2026-08-03.json"
CAPABILITIES = ROOT / "benchmark/reports/templates/provider-capabilities.json"


def _sample(manifest: CorpusManifest, sample_id: str):  # type: ignore[no-untyped-def]
    for sample in manifest.samples:
        if sample.sample_id == sample_id:
            return sample
    raise SystemExit(f"unknown sample ID: {sample_id}")


def _yes_no(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False


def _replace_audio(manifest: CorpusManifest, sample_id: str, audio) -> CorpusManifest:  # type: ignore[no-untyped-def]
    samples = tuple(
        sample.model_copy(update={"audio": audio, "status": "recorded"})
        if sample.sample_id == sample_id
        else sample
        for sample in manifest.samples
    )
    return manifest.model_copy(update={"samples": samples})


def command_init_corpus(args: argparse.Namespace) -> None:
    path = Path(args.manifest)
    if path.exists() and not args.force:
        raise SystemExit(f"manifest already exists: {path}; pass --force to regenerate")
    write_model(path, seed_manifest())
    print(f"wrote {len(seed_manifest().samples)} planned samples to {path}")


def command_validate(args: argparse.Namespace) -> None:
    manifest = load_model(Path(args.manifest), CorpusManifest)
    recorded = sum(sample.audio is not None for sample in manifest.samples)
    print(
        f"valid corpus {manifest.corpus_version}: {len(manifest.samples)} defined, "
        f"{recorded} recorded, {manifest.desired_sample_count} desired"
    )


def command_import(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    manifest = load_model(manifest_path, CorpusManifest)
    _sample(manifest, args.sample_id)
    audio = import_recording(
        Path(args.source), sample_id=args.sample_id, recordings_root=Path(args.recordings)
    )
    write_model(manifest_path, _replace_audio(manifest, args.sample_id, audio))
    print(f"preserved original and generated canonical audio for {args.sample_id}")


def command_record(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    manifest = load_model(manifest_path, CorpusManifest)
    sample = _sample(manifest, args.sample_id)
    print(f"Prompt: {sample.intended_text or '[silence/nonsense/control per notes]'}")
    print(f"Pinyin: {' '.join(sample.intended_pinyin) or '[none]'}")
    print(f"Recording condition: {sample.deliberate_error or 'control'}")
    with tempfile.TemporaryDirectory(prefix="benma-record-") as temporary:
        capture = Path(temporary) / f"{args.sample_id}.wav"
        while True:
            input(
                "Press Enter to begin recording. Stop ffmpeg with Ctrl-C if no --duration was set."
            )
            capture_with_ffmpeg(
                capture,
                input_format=args.input_format,
                input_device=args.input_device,
                duration_seconds=args.duration,
            )
            play_audio(capture)
            if _yes_no("Keep this recording?"):
                break
        audio = import_recording(
            capture, sample_id=args.sample_id, recordings_root=Path(args.recordings)
        )
    write_model(manifest_path, _replace_audio(manifest, args.sample_id, audio))
    print(f"recorded {args.sample_id}")


def command_annotate_blind(args: argparse.Namespace) -> None:
    manifest = load_model(Path(args.manifest), CorpusManifest)
    sample = _sample(manifest, args.sample_id)
    if sample.audio is None:
        raise SystemExit("sample has no audio")
    play_audio(sample.audio.asset_path)
    response = BlindListenerResponse(
        perceived_text=input("What did you hear? ").strip(),
        perceived_pinyin=tuple(input("Perceived pinyin (optional, spaces): ").strip().split()),
        understood_first_pass=_yes_no("Understood on first listen?"),
        would_request_repetition=_yes_no("Would you request repetition?"),
        confidence=float(input("Confidence from 0.0 to 1.0: ").strip()),
        notes=input("Blind notes (optional): ").strip() or None,
    )
    path = Path(args.annotations) / "blind" / f"{args.annotation_id}.json"
    commit_blind(
        path,
        annotation_id=args.annotation_id,
        sample_id=args.sample_id,
        listener_id=args.listener_id,
        randomized_order=args.order,
        response=response,
        rater_profile=RaterProfile(
            rater_id=args.listener_id,
            native_mandarin_self_report=args.native_mandarin,
            role=ListenerRole(args.role),
            region_or_accent_note=args.region_or_accent,
        ),
    )
    print(f"blind response committed immutably at {path}")


def command_annotate_reveal(args: argparse.Namespace) -> None:
    manifest = load_model(Path(args.manifest), CorpusManifest)
    sample = _sample(manifest, args.sample_id)
    blind_path = Path(args.annotations) / "blind" / f"{args.annotation_id}.json"
    if not blind_path.exists():
        raise SystemExit("blind stage must be committed before target reveal")
    print(f"Target: {sample.intended_text}")
    print(f"Pinyin: {' '.join(sample.intended_pinyin)}")
    affected = tuple(
        int(value) for value in input("Affected syllable indices (0-based, spaces): ").split()
    )
    severity = input("Severity [none/minor/moderate/severe]: ").strip()
    response = RevealedTargetResponse(
        tone_problem=_yes_no("Tone problem?"),
        affected_syllable_indices=affected,
        initial_problem=_yes_no("Initial problem?"),
        final_problem=_yes_no("Final problem?"),
        rhythm_or_prosody_issue=_yes_no("Rhythm/prosody issue?"),
        still_understandable=_yes_no("Still understandable?"),
        severity=severity,
        notes=input("Revealed notes (optional): ").strip() or None,
    )
    revealed_path = Path(args.annotations) / "revealed" / f"{args.annotation_id}.json"
    commit_revealed(blind_path, revealed_path, response=response)
    print(f"revealed stage committed at {revealed_path}")


def command_fixtures(args: argparse.Namespace) -> None:
    runs, annotations = materialize_replay_fixtures(Path(args.output))
    print(f"materialized {runs} replay runs and {annotations} synthetic listener fixtures")


def command_report(args: argparse.Namespace) -> None:
    actual_runs = Path(args.runs)
    use_fixture = args.fixtures or not any(actual_runs.glob("*.json"))
    runs = FIXTURES / "runs" if use_fixture else actual_runs
    annotations = FIXTURES / "annotations" if use_fixture else Path(args.annotations)
    summary = generate_report(
        manifest_path=Path(args.manifest),
        runs_dir=runs,
        annotations_dir=annotations,
        pricing_path=Path(args.pricing),
        capabilities_path=Path(args.capabilities),
        output_dir=Path(args.output),
    )
    print(f"generated {summary['data_status']} report at {Path(args.output) / 'report.md'}")


def command_pronunciation_calibration(args: argparse.Namespace) -> None:
    summary = generate_pronunciation_calibration(
        manifest_path=Path(args.manifest),
        runs_dir=Path(args.runs),
        annotations_dir=Path(args.annotations),
        output_dir=Path(args.output),
        split_path=Path(args.split) if args.split else None,
    )
    counts = summary["counts"]
    print(
        "pronunciation calibration "
        f"{'READY' if summary['calibration_ready'] else 'NOT READY'}: "
        f"{counts['real_recordings']}/50 real pilot recordings"
    )


def command_create_calibration_split(args: argparse.Namespace) -> None:
    manifest = load_model(Path(args.manifest), CorpusManifest)
    recorded = [
        sample
        for sample in manifest.samples
        if sample.audio is not None
        and sample.speaker_category.value != "synthetic_reference"
    ]
    split = create_stratified_split(
        recorded,
        benchmark_version=manifest.corpus_version,
        split_version=args.split_version,
    )
    persisted = persist_split(Path(args.output), split)
    print(
        f"split {persisted.split_version}: {len(persisted.calibration_sample_ids)} calibration, "
        f"{len(persisted.held_out_sample_ids)} held out"
    )


def command_import_provider_capture(args: argparse.Namespace) -> None:
    manifest = load_model(Path(args.manifest), CorpusManifest)
    sample = _sample(manifest, args.sample_id)
    run = import_live_capture(Path(args.capture), sample, output_dir=Path(args.output))
    print(f"imported {run.provider}/{run.product} as {run.run_id}")


def _workbench(args: argparse.Namespace) -> AnnotationWorkbench:
    manifest = load_model(Path(args.manifest), CorpusManifest)
    return AnnotationWorkbench(manifest, Path(args.annotations), seed=args.seed)


def command_annotation_workbench(args: argparse.Namespace) -> None:
    if args.bind not in {"127.0.0.1", "localhost", "::1"} and not args.allow_network:
        raise SystemExit("non-loopback bind requires --allow-network")
    token = args.access_token or secrets.token_urlsafe(24)
    serve_workbench(_workbench(args), bind=args.bind, port=args.port, access_token=token)


def command_export_annotations(args: argparse.Namespace) -> None:
    destination = Path(args.output)
    _workbench(args).export_bundle(destination)
    print(f"exported create-only annotation bundle to {destination}")


def command_import_annotations(args: argparse.Namespace) -> None:
    blind, revealed = _workbench(args).import_bundle(Path(args.bundle))
    print(f"imported {blind} blind and {revealed} revealed commits")


def command_cost(args: argparse.Namespace) -> None:
    result = calculate_scenarios(load_catalog(Path(args.pricing)))
    if args.output:
        write_json(Path(args.output), result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def command_schemas(args: argparse.Namespace) -> None:
    count = export_json_schemas(Path(args.output))
    print(f"exported {count} JSON Schema documents to {args.output}")


def command_acoustics(args: argparse.Namespace) -> None:
    analyzers = {
        "autocorrelation": AutocorrelationPitchAnalyzer,
        "parselmouth": ParselmouthPitchAnalyzer,
        "torchcrepe": TorchCrepePitchAnalyzer,
    }
    analyzer = analyzers[args.algorithm]()
    result = analyzer.analyze(args.audio)
    write_model(Path(args.output_json), result)
    write_diagnostic_svg(Path(args.audio), result, Path(args.output_svg), title=args.title)
    print(f"wrote acoustic result and plot using {result.pitch_algorithm}")


def command_acoustic_fixtures(args: argparse.Namespace) -> None:
    count = materialize_acoustic_calibrations(Path(args.output))
    print(f"materialized {count} clearly labeled synthetic acoustic calibrations")


def command_align(args: argparse.Namespace) -> None:
    result = MontrealForcedAligner().align(args.audio, args.transcript)
    write_model(Path(args.output), result)
    print(f"wrote {len(result.words)} alignment intervals")


def command_compare_acoustics(args: argparse.Namespace) -> None:
    report = compare_pitch_algorithms(
        [Path(path) for path in args.audio],
        output_dir=Path(args.output),
        evidence_origin=args.evidence_origin,
    )
    print(
        f"compared {report['audio_count']} audio files; decision: "
        f"{report['production_decision']}"
    )


def command_compare_alignments(args: argparse.Namespace) -> None:
    candidates: dict[str, Path] = {}
    for value in args.candidate:
        name, separator, path = value.partition("=")
        if not separator or not name or not path:
            raise SystemExit("--candidate values must use NAME=PATH")
        candidates[name] = Path(path)
    report = compare_alignment_files(
        Path(args.manual),
        candidates,
        output_path=Path(args.output),
        evidence_origin=args.evidence_origin,
    )
    print(f"compared {len(candidates)} alignments; decision: {report['production_decision']}")


def command_live(args: argparse.Namespace) -> None:
    manifest = load_model(Path(args.manifest), CorpusManifest)
    sample = _sample(manifest, args.sample_id)
    if args.provider == "openai":
        run = run_unknown_target(OpenAITranscriptionAdapter(), sample, output_dir=Path(args.output))
    elif args.provider == "google":
        run = run_unknown_target(GoogleChirpAdapter(), sample, output_dir=Path(args.output))
    elif args.provider == "azure":
        run = run_known_target(AzurePronunciationAdapter(), sample, output_dir=Path(args.output))
    else:
        raise SystemExit(f"unsupported provider: {args.provider}")
    print(f"{run.provider}/{run.product}: {run.status}; run ID {run.run_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m benchmark")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init-corpus", help="materialize the versioned pilot manifest")
    init.add_argument("--manifest", default=DEFAULT_MANIFEST)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=command_init_corpus)

    validate = commands.add_parser("validate-corpus")
    validate.add_argument("--manifest", default=DEFAULT_MANIFEST)
    validate.set_defaults(func=command_validate)

    imported = commands.add_parser("import-audio")
    imported.add_argument("sample_id")
    imported.add_argument("source")
    imported.add_argument("--manifest", default=DEFAULT_MANIFEST)
    imported.add_argument("--recordings", default=DEFAULT_RECORDINGS)
    imported.set_defaults(func=command_import)

    record = commands.add_parser("record")
    record.add_argument("sample_id")
    record.add_argument("--manifest", default=DEFAULT_MANIFEST)
    record.add_argument("--recordings", default=DEFAULT_RECORDINGS)
    record.add_argument("--input-format", default="pulse")
    record.add_argument("--input-device", default="default")
    record.add_argument("--duration", type=float)
    record.set_defaults(func=command_record)

    blind = commands.add_parser("annotate-blind")
    blind.add_argument("sample_id")
    blind.add_argument("annotation_id")
    blind.add_argument("listener_id")
    blind.add_argument("--order", type=int, required=True)
    blind.add_argument("--manifest", default=DEFAULT_MANIFEST)
    blind.add_argument("--annotations", default=DEFAULT_ANNOTATIONS)
    blind.add_argument("--native-mandarin", action="store_true")
    blind.add_argument(
        "--role",
        choices=[role.value for role in ListenerRole],
        default=ListenerRole.ORDINARY_NATIVE_LISTENER.value,
    )
    blind.add_argument("--region-or-accent")
    blind.set_defaults(func=command_annotate_blind)

    reveal = commands.add_parser("annotate-reveal")
    reveal.add_argument("sample_id")
    reveal.add_argument("annotation_id")
    reveal.add_argument("--manifest", default=DEFAULT_MANIFEST)
    reveal.add_argument("--annotations", default=DEFAULT_ANNOTATIONS)
    reveal.set_defaults(func=command_annotate_reveal)

    fixtures = commands.add_parser("run-fixtures")
    fixtures.add_argument("--output", default=FIXTURES)
    fixtures.set_defaults(func=command_fixtures)

    report = commands.add_parser("report")
    report.add_argument("--manifest", default=DEFAULT_MANIFEST)
    report.add_argument("--runs", default=DEFAULT_RUNS)
    report.add_argument("--annotations", default=DEFAULT_ANNOTATIONS)
    report.add_argument("--pricing", default=PRICING)
    report.add_argument("--capabilities", default=CAPABILITIES)
    report.add_argument("--output", default=OUTPUTS)
    report.add_argument("--fixtures", action="store_true")
    report.set_defaults(func=command_report)

    calibration = commands.add_parser("pronunciation-calibration")
    calibration.add_argument("--manifest", default=DEFAULT_MANIFEST)
    calibration.add_argument("--runs", default=DEFAULT_RUNS)
    calibration.add_argument("--annotations", default=DEFAULT_ANNOTATIONS)
    calibration.add_argument("--output", default=OUTPUTS)
    calibration.add_argument("--split")
    calibration.set_defaults(func=command_pronunciation_calibration)

    split = commands.add_parser("create-calibration-split")
    split.add_argument("--split-version", required=True)
    split.add_argument("--manifest", default=DEFAULT_MANIFEST)
    split.add_argument("--output", required=True)
    split.set_defaults(func=command_create_calibration_split)

    capture = commands.add_parser("import-provider-capture")
    capture.add_argument("capture")
    capture.add_argument("sample_id")
    capture.add_argument("--manifest", default=DEFAULT_MANIFEST)
    capture.add_argument("--output", default=DEFAULT_RUNS)
    capture.set_defaults(func=command_import_provider_capture)

    workbench = commands.add_parser("annotation-workbench")
    workbench.add_argument("--manifest", default=DEFAULT_MANIFEST)
    workbench.add_argument("--annotations", default=DEFAULT_ANNOTATIONS)
    workbench.add_argument("--seed", default="benma-annotation-v1")
    workbench.add_argument("--bind", default="127.0.0.1")
    workbench.add_argument("--port", type=int, default=8765)
    workbench.add_argument("--access-token")
    workbench.add_argument("--allow-network", action="store_true")
    workbench.set_defaults(func=command_annotation_workbench)

    export_annotations = commands.add_parser("export-annotations")
    export_annotations.add_argument("--output", required=True)
    export_annotations.add_argument("--manifest", default=DEFAULT_MANIFEST)
    export_annotations.add_argument("--annotations", default=DEFAULT_ANNOTATIONS)
    export_annotations.add_argument("--seed", default="benma-annotation-v1")
    export_annotations.set_defaults(func=command_export_annotations)

    import_annotations = commands.add_parser("import-annotations")
    import_annotations.add_argument("bundle")
    import_annotations.add_argument("--manifest", default=DEFAULT_MANIFEST)
    import_annotations.add_argument("--annotations", default=DEFAULT_ANNOTATIONS)
    import_annotations.add_argument("--seed", default="benma-annotation-v1")
    import_annotations.set_defaults(func=command_import_annotations)

    cost = commands.add_parser("cost")
    cost.add_argument("--pricing", default=PRICING)
    cost.add_argument("--output")
    cost.set_defaults(func=command_cost)

    schemas = commands.add_parser("export-schemas")
    schemas.add_argument("--output", default=ROOT / "benchmark/corpus/schemas")
    schemas.set_defaults(func=command_schemas)

    acoustics = commands.add_parser("acoustics")
    acoustics.add_argument("audio")
    acoustics.add_argument(
        "--algorithm",
        choices=["autocorrelation", "parselmouth", "torchcrepe"],
        default="autocorrelation",
    )
    acoustics.add_argument("--output-json", required=True)
    acoustics.add_argument("--output-svg", required=True)
    acoustics.add_argument("--title", default="Benma acoustic diagnostic")
    acoustics.set_defaults(func=command_acoustics)

    acoustic_fixtures = commands.add_parser("acoustic-fixtures")
    acoustic_fixtures.add_argument("--output", default=FIXTURES / "acoustics")
    acoustic_fixtures.set_defaults(func=command_acoustic_fixtures)

    align = commands.add_parser("align")
    align.add_argument("audio")
    align.add_argument("transcript")
    align.add_argument("--output", required=True)
    align.set_defaults(func=command_align)

    acoustic_comparison = commands.add_parser("compare-acoustics")
    acoustic_comparison.add_argument("audio", nargs="+")
    acoustic_comparison.add_argument("--output", required=True)
    acoustic_comparison.add_argument(
        "--evidence-origin", choices=["real_recording", "synthetic_test"], required=True
    )
    acoustic_comparison.set_defaults(func=command_compare_acoustics)

    alignment_comparison = commands.add_parser("compare-alignments")
    alignment_comparison.add_argument("--manual", required=True)
    alignment_comparison.add_argument("--candidate", action="append", required=True)
    alignment_comparison.add_argument("--output", required=True)
    alignment_comparison.add_argument(
        "--evidence-origin", choices=["real_recording", "synthetic_test"], required=True
    )
    alignment_comparison.set_defaults(func=command_compare_alignments)

    live = commands.add_parser("smoke-live")
    live.add_argument("provider", choices=["openai", "google", "azure"])
    live.add_argument("sample_id")
    live.add_argument("--manifest", default=DEFAULT_MANIFEST)
    live.add_argument("--output", default=DEFAULT_RUNS)
    live.set_defaults(func=command_live)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)
