"""Config-driven baselines; all preprocessing fits training speakers only."""

import copy
import subprocess
import warnings
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .annotations import aggregate
from .audio import verify_window_config
from .common import (
    LABELS,
    PACKAGE,
    ROOT,
    digest,
    file_hash,
    read_json,
    runtime,
    write_json,
    write_rows,
)
from .embeddings import FrozenEncoder
from .features import VERSION, baseline_prediction, matrix
from .manifest import replay, validate, verify_baseline
from .metrics import metrics, ratio
from .splits import apply_split, leakage_checks

GROUPS = {
    1: ["benma"],
    2: ["embeddings"],
    3: ["embeddings", "benma"],
    4: ["embeddings", "benma", "context"],
}


def validate_config(config):
    template = read_json(PACKAGE / "configs/pilot.json")

    def keys(actual, expected):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError("Unknown/missing experiment config keys")
        for key in expected:
            if isinstance(expected[key], dict):
                keys(actual[key], expected[key])

    keys(config, template)
    if config["version"] != "1.0" or config["feature_version"] != VERSION:
        raise ValueError("Unsupported experiment/feature version")
    if type(config["seed"]) is not int or type(config["scientific"]) is not bool:
        raise ValueError("Invalid seed/scientific config")
    if (
        not config["models"]
        or any(m not in GROUPS for m in config["models"])
        or len(set(config["models"])) != len(config["models"])
    ):
        raise ValueError("Unsupported/duplicate model family")
    if not config["classifiers"] or any(
        c not in ("logistic", "mlp") for c in config["classifiers"]
    ):
        raise ValueError("Unsupported classifier")
    if config["encoder"] not in read_json(PACKAGE / "configs/encoders.json"):
        raise ValueError("Unknown pinned encoder")
    if (
        not 0 <= config["policy"]["abstain_below"] <= 1
        or not 0 <= config["policy"]["confident_incorrect"] <= 1
        or config["policy"]["calibration_bins"] < 1
    ):
        raise ValueError("Invalid evaluation policy")
    if (
        len(config["mlp"]["hidden_layer_sizes"]) != 1
        or not 1 <= config["mlp"]["hidden_layer_sizes"][0] <= 128
        or config["mlp"]["solver"] != "lbfgs"
    ):
        raise ValueError(
            "Pilot MLP must be a small single-layer network with no internal random split"
        )
    aggregate([], config["aggregation"])
    return config


def experiment_identity(rows, split, config, encoder):
    # Paths/provenance are hashed for audit only. They never enter numeric matrices.
    return {
        "dataset_sha256": digest(sorted(rows, key=lambda r: r["example_id"])),
        "dataset_version": rows[0]["dataset_version"],
        "split_sha256": split["sha256"],
        "split_version": split["config"]["version"],
        "config_sha256": digest(config),
        "encoder": encoder,
        "seed": config["seed"],
        "feature_version": VERSION,
    }


def _report(rows, predictions, probabilities, config):
    policy = config["policy"]
    result = {}
    for partition in ("validation", "test"):
        indices = [i for i, r in enumerate(rows) if r["partition"] == partition]
        usable = [i for i in indices if rows[i]["aggregate"]["label"] in LABELS]
        excluded = [i for i in indices if i not in usable]

        def measured(selection):
            return (
                metrics(
                    [rows[i]["aggregate"]["label"] for i in selection],
                    [predictions[i] for i in selection],
                    probabilities[selection] if probabilities is not None else None,
                    policy["confident_incorrect"],
                    policy["calibration_bins"],
                )
                if selection
                else None
            )

        speakers = sorted({rows[i]["speaker_id"] for i in usable})
        by_speaker = {
            speaker: measured([i for i in usable if rows[i]["speaker_id"] == speaker])
            for speaker in speakers
        }
        result[partition] = {
            "consensus": measured(usable),
            "by_speaker": by_speaker,
            "speaker_macro_f1": float(np.mean([v["macro_f1"] for v in by_speaker.values()]))
            if by_speaker
            else None,
            "unanimous": measured([i for i in usable if rows[i]["aggregate"]["unanimous"]]),
            "all_examples": len(indices),
            "consensus_examples": len(usable),
            "all_example_abstention": ratio(
                sum(predictions[i] == "abstain" for i in indices), len(indices)
            ),
            "excluded_reasons": dict(
                Counter(
                    rows[i]["aggregate"]["reason"]
                    if rows[i]["aggregate"]["label"] is None
                    else "ungradable"
                    for i in excluded
                )
            ),
            "excluded_prediction_counts": dict(Counter(predictions[i] for i in excluded)),
        }
    return result


def run(rows, split, config, output):
    validate_config(config)
    validate(rows)
    baseline = verify_baseline()
    if split["config"] != config["split"]:
        raise ValueError("Frozen split differs from experiment split config")
    # A changed assignment is an error, never silently repaired for a training run.
    assigned = apply_split(rows, split)
    if any(a["partition"] != b["partition"] for a, b in zip(rows, assigned, strict=True)):
        raise ValueError("Manifest partitions differ from frozen split")
    checked = leakage_checks(rows, scientific=config["scientific"])
    verify_window_config(rows, config["windows"])
    # Re-execute the frozen adapter. Reject forged/stale deterministic numeric inputs.
    replayed, _ = replay(rows)
    if any(a["deterministic"] != b["deterministic"] for a, b in zip(rows, replayed, strict=True)):
        raise ValueError("Stored deterministic features differ from verified replay")
    rows = copy.deepcopy(sorted(rows, key=lambda r: r["example_id"]))
    for row in rows:
        row["aggregate"] = aggregate(row["annotations"], config["aggregation"])
    train = [
        i
        for i, r in enumerate(rows)
        if r["partition"] == "train" and r["aggregate"]["label"] in LABELS
    ]
    y_train = [rows[i]["aggregate"]["label"] for i in train]
    if set(y_train) != set(LABELS):
        raise ValueError(
            "Training speakers need independent consensus examples from all three classes"
        )
    for partition in ("validation", "test"):
        if not any(r["partition"] == partition and r["aggregate"]["label"] in LABELS for r in rows):
            raise ValueError(f"No consensus examples for {partition}")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "leakage-checks.json", checked)  # Written before any fitting.
    print(
        f"Leakage checks passed: {checked['speakers']} speakers, "
        f"{checked['checked_windows']} windows",
        flush=True,
    )
    encoder_config = read_json(PACKAGE / "configs/encoders.json")[config["encoder"]]
    identity = experiment_identity(rows, split, config, encoder_config)
    write_json(output / "resolved-config.json", config)
    write_json(output / "split.json", split)
    write_rows(output / "dataset.jsonl", rows)
    embeddings, embedding_metadata = None, {}
    encoder = None
    if any(m in (2, 3, 4) for m in config["models"]):
        encoder = FrozenEncoder(encoder_config, config["embedding"])
        embeddings, embedding_metadata = encoder.extract_all(rows)
        write_json(output / "embedding-index.json", embedding_metadata)
    report = {
        "status": "engineering_smoke_only" if not config["scientific"] else "pilot_evaluation",
        "product_performance_evidence": config["scientific"],
        "identity": identity,
        "baseline": baseline,
        "runtime": runtime(),
        "models": {},
        "policy_selection": "Predeclared config; no thresholds selected on test labels",
        "annotation_summary": dict(
            Counter(r["aggregate"]["label"] or r["aggregate"]["reason"] for r in rows)
        ),
        "partition_counts": dict(Counter(r["partition"] for r in rows)),
        "source_files": {
            str(p.relative_to(PACKAGE)): file_hash(p)
            for folder in ("perceptual_tone", "configs", "data", "scripts")
            for p in sorted((PACKAGE / folder).glob("*"))
            if p.is_file()
        },
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    baseline_preds = [baseline_prediction(row) for row in rows]
    report["models"]["model0_frozen_benma"] = _report(rows, baseline_preds, None, config)
    report["models"]["always_acceptable_sanity"] = _report(
        rows, ["acceptable"] * len(rows), None, config
    )
    write_rows(
        output / "model0.predictions.jsonl",
        [
            {"example_id": row["example_id"], "prediction": pred}
            for row, pred in zip(rows, baseline_preds, strict=True)
        ],
    )
    for family in config["models"]:
        x, columns = matrix(rows, GROUPS[family], embeddings)
        np.savez_compressed(
            output / f"model{family}.features.npz",
            values=x,
            example_ids=np.array([r["example_id"] for r in rows]),
        )
        write_json(
            output / f"model{family}.feature-schema.json",
            {"version": VERSION, "groups": GROUPS[family], "columns": columns},
        )
        for classifier in config["classifiers"]:
            name = f"model{family}_{classifier}"
            if classifier == "logistic":
                estimator = LogisticRegression(
                    **config["logistic"], random_state=config["seed"], solver="lbfgs"
                )
            else:
                estimator = MLPClassifier(
                    **config["mlp"], random_state=config["seed"], early_stopping=False
                )
            model = make_pipeline(
                SimpleImputer(strategy="median", keep_empty_features=True),
                StandardScaler(),
                estimator,
            )
            with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                model.fit(x[train], y_train)
                raw_probs = model.predict_proba(x)
            probs = raw_probs[:, [list(model.classes_).index(label) for label in LABELS]]
            predictions = [
                LABELS[i] if confidence >= config["policy"]["abstain_below"] else "abstain"
                for i, confidence in zip(probs.argmax(1), probs.max(1), strict=True)
            ]
            report["models"][name] = _report(rows, predictions, probs, config)
            report["models"][name]["fit_warnings"] = [str(w.message) for w in caught]
            report["models"][name]["groups"] = GROUPS[family]
            report["models"][name]["feature_count"] = len(columns)
            joblib.dump(model, output / f"{name}.joblib")
            write_rows(
                output / f"{name}.predictions.jsonl",
                [
                    {
                        "example_id": r["example_id"],
                        "partition": r["partition"],
                        "prediction": pred,
                        "probabilities": dict(zip(LABELS, map(float, prob), strict=True)),
                    }
                    for r, pred, prob in zip(rows, predictions, probs, strict=True)
                ],
            )
            for partition in ("validation", "test"):
                base = report["models"]["model0_frozen_benma"][partition]["consensus"]
                learned = report["models"][name][partition]["consensus"]
                report["models"][name][partition]["difference_vs_frozen_benma"] = {
                    "macro_f1": learned["macro_f1"] - base["macro_f1"],
                    **{
                        key: (
                            learned[key]["rate"] - base[key]["rate"]
                            if learned[key]["rate"] is not None and base[key]["rate"] is not None
                            else None
                        )
                        for key in (
                            "warning_on_acceptable",
                            "incorrect_on_acceptable",
                            "incorrect_recall",
                        )
                    },
                }
    report["embedding_cache"] = (
        {"hits": encoder.hits, "misses": encoder.misses} if encoder else None
    )
    write_json(output / "report.json", report)
    return report
