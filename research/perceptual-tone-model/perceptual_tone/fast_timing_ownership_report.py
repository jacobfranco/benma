"""Write-once evidence tables from sealed offline inference."""

import csv

from .azure_timing_report import interval, optional, table, vector
from .azure_timing_replay import CLASSES
from .common import read_json, write_json
from .fast_timing_ownership import OUT, SAVED


def main():
    final = read_json(OUT / "final-results.json")
    alternatives = read_json(OUT / "alternatives.json")
    boundaries, outputs, f0, comparisons, alternatives_table, csv_rows = [], [], [], [], [], []
    for row in final["rows"]:
        result = row["representations"]["final"]
        ac = result["acoustics"]
        output = result["model_outputs"]
        actual = output["expanded"].get("embedding", {}).get("owned_frames", 0)
        boundaries.append([
            row["take"], row["character"], interval(row["azure_whole"]),
            interval(result["contract"]["pooling"]), f"{result['duration_ms']:.1f}",
            ac["usable_frames"], f"{ac['voiced_support_ms']:.1f}",
            result["geometric_frames"], actual,
            output["expanded"].get("reason") or "usable",
        ])
        outputs.append([
            row["take"], row["character"], output["expanded"]["prediction"] or "abstain",
            vector(output["expanded"]), output["pilot"]["prediction"] or "abstain",
            vector(output["pilot"]),
        ])
        f0.append([
            row["take"], row["character"], ac["islands"], optional(ac["first"], 4),
            optional(ac["last"], 4), optional(ac["range_st"], 3),
            optional(ac.get("largest_island_net_st"), 3), optional(ac["fall_st"], 3),
            optional(ac["recovery_st"], 3),
        ])
        for model in ("expanded", "pilot"):
            cmp = result["comparison"][model]
            ref, new = row["reference"][model], output[model]
            comparisons.append([
                row["take"], row["character"], model, ref["prediction"] or "abstain",
                new["prediction"] or "abstain", optional(cmp.get("total_variation")),
                optional(cmp.get("margin_delta")),
                " / ".join(optional(cmp.get("class_probability_deltas", {}).get(c)) for c in CLASSES),
            ])
            csv_rows.append({
                "take": row["take"], "character": row["character"], "model": model,
                "azure_start": row["azure_whole"][0], "azure_end": row["azure_whole"][1],
                "pool_start": result["contract"]["pooling"][0],
                "pool_end": result["contract"]["pooling"][1],
                "duration_ms": result["duration_ms"],
                "retained_f0_frames": ac["usable_frames"], "voiced_support_ms": ac["voiced_support_ms"],
                "geometric_frames": result["geometric_frames"],
                "actual_pooled_frames": new.get("embedding", {}).get("owned_frames", 0),
                "prediction": new["prediction"], "reason": new["reason"],
                **{c: (new["probabilities"] or {}).get(c) for c in CLASSES},
            })
    for row in alternatives:
        result = row["result"]
        ac, outputs_pair = result["acoustics"], result["model_outputs"]
        alternatives_table.append([
            row["take"], row["character"], row["alternative"],
            interval(result["contract"]["read_unit"]), interval(result["contract"]["pooling"]),
            f"{result['duration_ms']:.1f}", f"{ac['usable_frames']} / {ac['voiced_support_ms']:.1f}",
            outputs_pair["expanded"].get("embedding", {}).get("owned_frames", 0),
            outputs_pair["expanded"]["prediction"] or "abstain", vector(outputs_pair["expanded"]),
            outputs_pair["pilot"]["prediction"] or "abstain", vector(outputs_pair["pilot"]),
            ac["islands"], optional(ac.get("largest_island_net_st"), 3),
            row["comparison_to_provider_envelope"]["expanded"].get("same_argmax", "unavailable"),
        ])
    sections = [
        "# Final fast timing: complete offline evidence",
        "MFA is a frozen diagnostic reference, not truth. All probabilities are frozen "
        "raw model preferences. Final spans were sealed before diagnostic alternative inference. "
        "No retained support means the displayed pool is a raw-span placeholder, not usable material. "
        "The interrupted take-2 pool is retained for audit but rejected before model execution. "
        "Zero actual frames on an abstention means no inference, not zero geometric centers.",
        "## Timing and evidence coverage",
        table(["Take", "Unit", "Azure raw s", "Envelope s", "Duration ms", "F0 frames",
               "F0 cell support ms", "Geometric HuBERT frames", "Actual pooled frames", "State"],
              boundaries),
        "## Expanded and pilot probabilities",
        "Vectors are T1 / T2 / T3 / T4. The external neutral scope remains neutral even "
        "when the earlier duration gate supplies the machine-readable abstention reason.",
        table(["Take", "Unit", "Expanded", "Expanded probabilities", "Pilot", "Pilot probabilities"],
              outputs),
        "## Deterministic F0 support",
        "No new deterministic tone family was manufactured. These summaries use the unchanged "
        "retained F0 graph on the final numeric regions. Net, fall and recovery use the largest "
        "contiguous island only; overall range is descriptive, and gaps are never interpolated. "
        "The earlier deterministic MFA-span labels remain in the frozen report and are not "
        "relabelled as final-span outputs.",
        table(["Take", "Unit", "Islands", "First F0 s", "Last F0 s", "Range st",
               "Largest-island net st", "Fall st", "Recovery st"], f0),
        "## Descriptive reference comparison",
        "TV is half L1 distance. No confidence cutoff or probability-based acceptance threshold "
        "was introduced. Non-comparable abstentions have no synthetic vector.",
        table(["Take", "Unit", "Head", "MFA", "Final", "TV", "Margin delta",
               "T1/T2/T3/T4 deltas"], comparisons),
        "## Predeclared ownership alternatives",
        "All alternative calls bypass only the new interruption guard to show diagnostic "
        "behavior; existing no-support, duration and external neutral gates remain. They use "
        "the original Azure context to isolate ownership/pooling from encoder-context changes. "
        "No alternative is selected by its prediction. The final policy remains the provider "
        "envelope plus an acoustic interruption abstention. F0 frames/support and full "
        "acoustic details are preserved in alternatives.json.",
        table(["Take", "Unit", "Alternative", "Whole s", "Pool s", "Duration ms",
               "F0 frames / ms", "Actual pooled frames", "Expanded", "Expanded probabilities",
               "Pilot", "Pilot probabilities", "Islands", "Largest-island net st",
               "Same expanded family as unguarded envelope"], alternatives_table),
    ]
    with (OUT / "evidence-tables.md").open("x") as stream:
        stream.write("\n\n".join(sections) + "\n")
    with (OUT / "final-outputs.csv").open("x") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    latency = {}
    saved_latency = read_json(SAVED / "latency-summary.json")
    for tid, values in final["timings"].items():
        prior = saved_latency["takes"][tid]
        core = sum(prior[k] for k in [
            "azure_request_seconds_including_transport_json_decode",
            "timestamp_parsing_seconds", "f0_seconds",
        ]) + values["refinement_and_guard_seconds"] + values["inference_seconds"]
        prior_overhead = (
            prior["conservative_warm_estimate_including_entire_batch_report_seconds"]
            - prior["warm_sequential_core_seconds"]
        )
        latency[tid] = {
            "saved_azure_seconds": prior["azure_request_seconds_including_transport_json_decode"],
            "saved_f0_seconds": prior["f0_seconds"], **values,
            "composed_warm_core_seconds": core,
            "composed_warm_with_prior_io_report_allowance_seconds": core + prior_overhead,
        }
    write_json(OUT / "latency.json", {
        "takes": latency, "fresh_process_setup": final["performance"],
        "qualification": "Saved Azure and F0 measurements plus fresh no-cache resident inference. "
        "Not a new provider request or browser end-to-end benchmark. Full evidence-report "
        "work, startup imports, client upload, microphone finalization and rendering are not "
        "freshly timed. Prior evidence I/O/report allowance shown separately.",
    })


if __name__ == "__main__":
    main()
