"""Offline, fixed four-case frame audit. No selection, fitting, or runtime integration."""

import argparse
import csv
import subprocess
from types import SimpleNamespace

import numpy as np
from scipy.special import softmax

from .aishell3_boundaries import sample_index
from .aishell3_embeddings import PAD
from .common import PACKAGE, ROOT, file_hash, read_json, runtime, write_json
from .embeddings import frame_centers

OUT = PACKAGE / "data/generated/frame-attribution-v1"
PRIOR = PACKAGE / "data/generated/ownership-selector-v1"
F0_PRIOR = PACKAGE / "data/generated/f0-independent-v1"
CASES = (("take-1", 3), ("take-2", 3), ("take-3", 1), ("take-3", 2))
CLASSES = ("T1", "T2", "T3", "T4")
REGIONS = ("earliest", "early", "central", "late", "final")


def geometry(contract):
    """Exactly the existing nearest-sample, padded convolution geometry."""
    config = SimpleNamespace(conv_kernel=[10, 3, 3, 3, 3, 2, 2], conv_stride=[5, 2, 2, 2, 2, 2, 2])
    a, b = [sample_index(t, 16000) for t in contract["context"]]
    n = b - a + 2 * PAD
    for k, s in zip(config.conv_kernel, config.conv_stride, strict=True):
        n = (n - k) // s + 1
    centers = frame_centers(config, n)
    p, q = [sample_index(t, 16000) - a + PAD for t in contract["pooling"]]
    return (centers + a - PAD) / 16000, np.flatnonzero((centers >= p) & (centers < q))


def positional_plan(current, new):
    """Only integer positions enter; all diagnostic subsets fixed before head loading."""
    current, new = np.asarray(current, int), np.asarray(new, int)
    shared = np.intersect1d(current, new)
    added, removed = np.setdiff1d(new, current), np.setdiff1d(current, new)
    early = added[added < shared.min()] if len(shared) else np.array([], int)
    late = added[added > shared.max()] if len(shared) else np.array([], int)
    regions = dict(zip(REGIONS, [a.tolist() for a in np.array_split(new, 5)], strict=True))
    sets = {
        "current": current,
        "new": new,
        "shared": shared,
        "added_only": added,
        "shared_plus_added": np.union1d(shared, added),
        "shared_plus_early": np.union1d(shared, early),
        "shared_plus_late": np.union1d(shared, late),
    }
    sets.update({"without_" + k: np.setdiff1d(new, v) for k, v in regions.items()})
    sets.update({f"prefix_{n:02}": new[:n] for n in range(1, len(new) + 1)})
    sets.update({f"suffix_{n:02}": new[-n:] for n in range(1, len(new) + 1)})
    return {
        "current": current.tolist(),
        "new": new.tolist(),
        "shared": shared.tolist(),
        "added": added.tolist(),
        "removed": removed.tolist(),
        "early_added": early.tolist(),
        "late_added": late.tolist(),
        "regions": regions,
        "subsets": {k: np.asarray(v, int).tolist() for k, v in sets.items() if len(v)},
    }


def affine_head(model):
    """Fail closed if the inspected finite-input affine pipeline changes."""
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    assert len(model.steps) == 3
    imputer, scaler, head = [v for _, v in model.steps]
    assert isinstance(imputer, SimpleImputer) and not imputer.add_indicator
    assert isinstance(scaler, StandardScaler) and scaler.with_mean and scaler.with_std
    assert isinstance(head, LogisticRegression) and head.coef_.shape == (4, 768)
    assert tuple(model.classes_) == CLASSES
    assert imputer.transform(np.zeros((1, 768))).shape == (1, 768)
    w = head.coef_ / scaler.scale_
    return scaler.mean_, scaler.scale_, head.coef_, head.intercept_, w


def frame_scores(hidden, model):
    if not np.isfinite(hidden).all():
        raise ValueError("nonfinite_embeddings_break_finite_input_contract")
    mu, scale, coef, bias, w = affine_head(model)
    # Standardized origin = this head's frozen training mean. Also save raw origin.
    centered = ((hidden.astype(float) - mu) / scale) @ coef.T
    raw = hidden.astype(float) @ w.T
    return centered, bias, raw, bias - w @ mu


def decompose(scores, bias, current, new):
    s, a, r = (np.intersect1d(current, new), np.setdiff1d(new, current), np.setdiff1d(current, new))
    n, m = len(current), len(new)
    parts = {
        "shared_current": scores[s].sum(0) / n,
        "shared_new": scores[s].sum(0) / m,
        "added_direct": scores[a].sum(0) / m,
        "removed_old": scores[r].sum(0) / n,
        "shared_dilution_delta": scores[s].sum(0) * (1 / m - 1 / n),
        "bias": bias,
        "current_logits": scores[current].mean(0) + bias,
        "new_logits": scores[new].mean(0) + bias,
    }
    parts["delta"] = parts["new_logits"] - parts["current_logits"]
    np.testing.assert_allclose(
        parts["delta"],
        parts["added_direct"] - parts["removed_old"] + parts["shared_dilution_delta"],
        atol=1e-12,
    )
    return {k: v.tolist() for k, v in parts.items()}


def evaluate(hidden, ids, model, pair, centers):
    pool = hidden[ids].astype(float).mean(0)
    logits = model.decision_function(pool[None])[0]
    prob = model.predict_proba(pool[None])[0]
    np.testing.assert_allclose(softmax(logits), prob, atol=1e-12)
    ordered = np.sort(logits)
    return {
        "frames": ids,
        "count": len(ids),
        "center_extent_ms": float(1000 * (centers[max(ids)] - centers[min(ids)])),
        "frame_cell_support_ms": 20 * len(ids),
        "probabilities": prob.tolist(),
        "logits": logits.tolist(),
        "argmax": CLASSES[int(prob.argmax())],
        "pair_margin": float(logits[pair[1]] - logits[pair[0]]),
        "top_two_logit_margin": float(ordered[-1] - ordered[-2]),
        "top_two_probability_margin": float(np.sort(prob)[-1] - np.sort(prob)[-2]),
    }


def cosine(a, b):
    return np.sum(a * b, axis=-1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1))


def seal():
    OUT.mkdir(parents=True, exist_ok=True)
    old = read_json(PRIOR / "freeze-before.json")["files"]
    paths = {ROOT / p for p in old}
    paths.update(p for p in PRIOR.rglob("*") if p.is_file())
    paths.update(p for p in F0_PRIOR.rglob("*") if p.is_file())
    paths.update(PACKAGE.glob("perceptual_tone/*.py"))
    paths.update(PACKAGE.glob("tests/*.py"))
    paths.update(PACKAGE.glob("*.md"))
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    paths.update(ROOT / p for p in tracked if p and (ROOT / p).is_file())
    # Frame outputs are not in the prior caches: prior .npy files hold (3, 768) means.
    rows = read_json(PRIOR / "results.json")["rows"]
    plan = []
    for recording, index in CASES:
        row = next(
            r
            for r in rows
            if (r["recording"], r["index"]) == (recording, index)
            and r["candidate"] == "GAP_AWARE_AZURE"
        )
        current, new = row["current_reference"]["contract"], row["contract"]
        for k in ("audio_reference", "audio_sha256", "context", "read_unit"):
            assert current[k] == new[k]
        centers, c = geometry(current)
        nc, n = geometry(new)
        np.testing.assert_array_equal(centers, nc)
        assert len(c) == row["current_reference"]["pooled_frames"]
        assert len(n) == row["pooled_frames"]
        plan.append(
            {
                "case": f"{recording}-{index}",
                "recording": recording,
                "index": index,
                "current_contract": current,
                "new_contract": new,
                "centers": centers.tolist(),
                "plan": positional_plan(c, n),
            }
        )
    write_json(
        OUT / "freeze-before.json",
        {
            "scope": "Existing tracked files, research sources/reports, prior two experiments, "
            "and inherited consumed inputs/lock; no corpus rescan",
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(),
            "files": {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(paths)},
        },
    )
    write_json(
        OUT / "plan-before-inference.json",
        {
            "scope": [list(c) for c in CASES],
            "region_rule": "numpy.array_split(new frame ids, 5)",
            "labels": "Position only; not phonetic segment claims",
            "selection_inputs": "Persisted numeric contracts and convolution geometry only",
            "known_case_selection": "Four previously reported expanded argmax flips, user specified",
            "code_sha256": file_hash(__file__),
            "runtime": runtime(),
            "rows": plan,
        },
    )


def verify_freeze():
    before = read_json(OUT / "freeze-before.json")
    changed = [p for p, sha in before["files"].items() if file_hash(ROOT / p) != sha]
    assert not changed, changed
    return {
        "verified_files": len(before["files"]),
        "changed": changed,
        "git_head_unchanged": before["git_head"]
        == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
    }


def export_csv(path, rows):
    with path.open("x") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run():
    import torch

    from .aishell3_embeddings import Encoder, input_audio
    from .f0_independent_replay import sources
    from .learner_transfer import load_models

    plan = read_json(OUT / "plan-before-inference.json")
    assert file_hash(__file__) == plan["code_sha256"]
    verify_freeze()
    lock = read_json(PACKAGE / "configs/dev-learned-lock.json")
    for p, sha in lock["files"].items():
        assert file_hash(ROOT / p) == sha
    encoder = Encoder("chinese_hubert_base", OUT / "cache/unused-pooled", OUT / "cache/canonical")
    assert encoder.base.weights == lock["encoder_weights"]
    models = load_models(lock["model_method"])
    prior = {(r["recording"], r["index"]): r for r in read_json(F0_PRIOR / "results.json")["rows"]}
    acoustic = {s["name"]: s for s in sources()}
    results, comparisons = [], []
    for item in plan["rows"]:
        case, subsets = item["case"], item["plan"]
        folder = OUT / case
        folder.mkdir(exist_ok=True)
        tensor_path = folder / "layer9.npy"
        if tensor_path.exists():
            meta = read_json(folder / "encoder.json")
            assert file_hash(tensor_path) == meta["tensor_sha256"]
            assert meta["contract"] == item["new_contract"]
            hidden = np.load(tensor_path, allow_pickle=False)
        else:
            audio, _, canonical = input_audio(
                item["new_contract"], "context", OUT / "cache/canonical"
            )
            old_audio, _, _ = input_audio(
                item["current_contract"], "context", OUT / "cache/canonical"
            )
            np.testing.assert_array_equal(audio, old_audio)
            if encoder.base.model is None:
                encoder.base._load()
            inputs = encoder.base.processor(audio, sampling_rate=16000, return_tensors="pt")
            with torch.inference_mode():
                states = encoder.base.model(**inputs, output_hidden_states=True).hidden_states
                hidden = states[9][0].cpu().numpy().copy()
            with tensor_path.open("xb") as f:
                np.save(f, hidden, allow_pickle=False)
            meta = {
                "contract": item["new_contract"],
                "layer": 9,
                "output_shape": [list(s.shape) for s in states],
                "input_samples_with_padding": len(audio),
                "canonical_sha256": file_hash(canonical),
                "identity": encoder.identity,
                "tensor_sha256": file_hash(tensor_path),
                "processor": encoder.base.processor.to_dict(),
            }
            write_json(folder / "encoder.json", meta)
        centers = np.array(item["centers"])
        assert hidden.shape == (len(centers), 768) and np.isfinite(hidden).all()
        old = prior[(item["recording"], item["index"])]
        evidence = acoustic[item["recording"]]
        unit = evidence["units"][item["index"]]
        result = {
            **item,
            "character": unit["character"],
            "heads": {},
            "encoder": meta,
            "acoustics": {
                "raw": evidence["raw"],
                "graph": evidence["graph"],
                "neighbors": [
                    u["whole"]
                    for u in evidence["units"][max(0, item["index"] - 1) : item["index"] + 2]
                ],
                "pitch_evidence": old["pitch_evidence"],
            },
        }
        c, n = subsets["current"], subsets["new"]
        pc, pn = hidden[c].astype(float).mean(0), hidden[n].astype(float).mean(0)
        result["geometry"] = {
            "cosine_distance": float(1 - cosine(pc, pn)),
            "l2_distance": float(np.linalg.norm(pc - pn)),
            "current_norm": float(np.linalg.norm(pc)),
            "new_norm": float(np.linalg.norm(pn)),
        }
        for name, model in models.items():
            score, bias, raw, raw_bias = frame_scores(hidden, model)
            cur_saved = old["representations"]["CURRENT_REFERENCE"]["outputs"][name]
            new_saved = old["representations"]["AZURE_WHOLE"]["outputs"][name]
            # Same expanded competing pair for cross-head comparisons; pilot own flip also below.
            ec = old["representations"]["CURRENT_REFERENCE"]["outputs"]["expanded"]["prediction"]
            en = old["representations"]["AZURE_WHOLE"]["outputs"]["expanded"]["prediction"]
            pair = (CLASSES.index(ec), CLASSES.index(en))
            evaluations = {
                k: evaluate(hidden, ids, model, pair, centers)
                for k, ids in subsets["subsets"].items()
            }
            for v in evaluations.values():
                np.testing.assert_allclose(
                    v["logits"], score[v["frames"]].mean(0) + bias, atol=1e-11
                )
                v["tv_from_new"] = float(
                    np.abs(np.array(v["probabilities"]) - evaluations["new"]["probabilities"]).sum()
                    / 2
                )
            errors = {}
            for key, saved, rep in (
                ("current", cur_saved, "CURRENT_REFERENCE"),
                ("new", new_saved, "AZURE_WHOLE"),
            ):
                old_p = np.array([saved["probabilities"][x] for x in CLASSES])
                error = float(np.max(abs(old_p - evaluations[key]["probabilities"])))
                assert error < 2e-6, (case, name, error)
                assert evaluations[key]["argmax"] == saved["prediction"]
                record = old["representations"][rep]["embedding"]
                matches = list(F0_PRIOR.rglob(record["key"] + ".npy"))
                assert len(matches) == 1 and file_hash(matches[0]) == record["sha256"]
                cached = np.load(matches[0], allow_pickle=False)[1]
                pool = hidden[subsets[key]].astype(float).mean(0)
                pool_error = float(np.max(abs(cached - pool)))
                assert pool_error < 2e-6
                production_pool = torch.from_numpy(hidden)[subsets[key]].mean(0).numpy()
                np.testing.assert_array_equal(production_pool, cached)
                errors[key] = {
                    "probability_max_abs": error,
                    "pool_max_abs": pool_error,
                    "torch_pool_bitwise_matches_cache": True,
                    "cached_path": str(matches[0].relative_to(ROOT)),
                }
            attribution = decompose(score, bias, c, n)
            raw_attribution = decompose(raw, raw_bias, c, n)
            margins = {k: v[pair[1]] - v[pair[0]] for k, v in attribution.items()}
            # Neutral here means zero standardized evidence; it is not an audio ablation.
            neutral_logits = np.array(attribution["shared_new"]) + bias
            weight = affine_head(model)[4][pair[1]] - affine_head(model)[4][pair[0]]
            delta = pn - pc
            own_pair = [cur_saved["prediction"], new_saved["prediction"]]
            result["heads"][name] = {
                "pair": [ec, en],
                "own_pair": own_pair,
                "subsets": evaluations,
                "attribution": attribution,
                "pair_decomposition": margins,
                "raw_origin_attribution": raw_attribution,
                "reproduction_errors": errors,
                "neutral_added_logits": neutral_logits.tolist(),
                "neutral_added_argmax": CLASSES[int(neutral_logits.argmax())],
                "neutral_added_pair_margin": float(
                    neutral_logits[pair[1]] - neutral_logits[pair[0]]
                ),
                "weight_pair_norm": float(np.linalg.norm(weight)),
                "delta_weight_cosine": float(cosine(delta, weight)),
                "normalized_current_boundary_distance": float(
                    margins["current_logits"] / np.linalg.norm(weight)
                ),
                "normalized_new_boundary_distance": float(
                    margins["new_logits"] / np.linalg.norm(weight)
                ),
            }
            frame_rows = []
            for i in sorted(set(c + n)):
                row = {
                    "frame": i,
                    "seconds": centers[i],
                    "current": int(i in c),
                    "new": int(i in n),
                    "region": next(k for k, v in subsets["regions"].items() if i in v),
                    "cosine_to_current": float(cosine(hidden[i], pc)),
                    "cosine_to_new": float(cosine(hidden[i], pn)),
                }
                for j, t in enumerate(CLASSES):
                    row[f"{t}_standardized_score"] = score[i, j]
                    row[f"{t}_raw_score"] = raw[i, j]
                    row[f"{t}_current_contribution"] = score[i, j] / len(c) if i in c else 0
                    row[f"{t}_new_contribution"] = score[i, j] / len(n) if i in n else 0
                row["pair_score"] = score[i, pair[1]] - score[i, pair[0]]
                row["pair_current_contribution"] = row["pair_score"] / len(c) if i in c else 0
                row["pair_new_contribution"] = row["pair_score"] / len(n) if i in n else 0
                row["pair_delta_contribution"] = (
                    row["pair_new_contribution"] - row["pair_current_contribution"]
                )
                frame_rows.append(row)
            result["heads"][name]["frames"] = frame_rows
            export_csv(folder / f"{name}-frames.csv", frame_rows)
            export_csv(
                folder / f"{name}-subsets.csv",
                [
                    {
                        "subset": k,
                        **{
                            a: b
                            for a, b in v.items()
                            if a not in ("probabilities", "logits", "frames")
                        },
                        "frames": " ".join(map(str, v["frames"])),
                        **{t: p for t, p in zip(CLASSES, v["probabilities"], strict=True)},
                    }
                    for k, v in evaluations.items()
                ],
            )
        ew = affine_head(models["expanded"])[4]
        pw = affine_head(models["pilot"])[4]
        result["head_pair_direction_cosine"] = float(
            cosine(ew[pair[1]] - ew[pair[0]], pw[pair[1]] - pw[pair[0]])
        )
        write_json(folder / "results.json", result)
        results.append(result)
        comparisons.append(
            {
                "case": case,
                **result["geometry"],
                "head_pair_direction_cosine": result["head_pair_direction_cosine"],
                **{
                    f"{h}_{k}": v
                    for h, r in result["heads"].items()
                    for k, v in r["pair_decomposition"].items()
                },
            }
        )
        print(
            case,
            {
                h: (
                    r["subsets"]["current"]["argmax"],
                    r["subsets"]["new"]["argmax"],
                    r["pair_decomposition"],
                )
                for h, r in result["heads"].items()
            },
            flush=True,
        )
    export_csv(OUT / "comparison.csv", comparisons)
    write_json(
        OUT / "results.json",
        {
            "cases": results,
            "classes": CLASSES,
            "plan_sha256": file_hash(OUT / "plan-before-inference.json"),
            "weights": encoder.base.weights,
            "runtime": runtime(),
            "inference_scope": "Exactly four fixed contexts, both heads; no corpus benchmark",
        },
    )
    write_json(OUT / "freeze-verification.json", verify_freeze())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seal", "run", "verify"))
    action = parser.parse_args().action
    {"seal": seal, "run": run, "verify": lambda: print(verify_freeze())}[action]()
