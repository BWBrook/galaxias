#!/usr/bin/env python3
"""Summarize a completed probability gate without consuming historical R."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from scripts.run_age_recovery import binding, utc, verify_bindings


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def numeric_range(rows, field):
    values = []
    for row in rows:
        try:
            value = float(row.get(field, ""))
        except (ValueError, TypeError):
            continue
        if math.isfinite(value):
            values.append(value)
    return [min(values), max(values)] if values else None


def run(args):
    directory = args.input_dir.resolve()
    generation = json.loads((directory / "gate/run_manifest.json").read_text())
    analysis = json.loads((directory / "analysis/analysis_receipt.json").read_text())
    execution = json.loads((directory / "execution_receipt.json").read_text())
    if generation["status"] != "complete" or execution["status"] != "complete":
        raise ValueError("generation and execution must be complete")
    if not analysis["full_design"] or analysis["metric_rows"] != 1152:
        raise ValueError("summary requires the complete frozen design")
    if analysis["actual_remaining_evidence_read"]:
        raise ValueError("this summary is only for the synthetic gate")
    for name, expected in analysis["outputs"].items():
        if binding(directory / "analysis" / name) != expected:
            raise ValueError(f"analysis output changed: {name}")
    verify_bindings(generation["source_bindings"])
    verify_bindings(analysis["source_bindings"])
    metrics = read_csv(directory / "analysis/gate_metrics.csv")
    composition = read_csv(directory / "analysis/conditional_composition.csv")
    selection = read_csv(directory / "analysis/future_feasibility_selection.csv")
    primary = [r for r in metrics if int(r["maximum_age"]) == 6]
    if len(metrics) != 1152 or len(primary) != 576:
        raise ValueError("assessment row counts differ from the frozen design")
    groups = []
    for age, restriction, stratum in sorted({(int(r["maximum_age"]), r["restriction"], r["index_stratum"]) for r in metrics}):
        rows = [r for r in metrics if (int(r["maximum_age"]), r["restriction"], r["index_stratum"]) == (age, restriction, stratum)]
        groups.append(dict(maximum_age=age, restriction=restriction, index_stratum=stratum,
            rows=len(rows), qualified=sum(r["qualified"] == "True" for r in rows),
            status_counts=dict(Counter(r["status"] for r in rows)),
            precision_truth_weight=numeric_range(rows, "precision_truth_weight"),
            E_only_loss=numeric_range(rows, "E_only_loss"),
            E_only_loss_low=numeric_range(rows, "E_only_loss_low"),
            E_only_loss_high=numeric_range(rows, "E_only_loss_high"),
            truth_source_ess=numeric_range(rows, "truth_source_ess"),
            bank_source_ess=numeric_range(rows, "bank_source_ess")))
    summary = dict(status=analysis["status"], summarized_utc=utc(),
        nominal_site_history_attempts=generation["nominal_site_histories"],
        joint_history_attempts=sum(generation["history_status_counts"].values()),
        history_status_counts=generation["history_status_counts"],
        paired_cell_source_rows=generation["source_rows"], independent_source_ids=2048,
        generation_elapsed_seconds=generation["elapsed_seconds"],
        analysis_elapsed_seconds=analysis["elapsed_seconds"],
        all_status_counts=dict(Counter(r["status"] for r in metrics)),
        primary_status_counts=dict(Counter(r["status"] for r in primary)),
        primary_qualified=sum(r["qualified"] == "True" for r in primary),
        primary_computationally_assessed=sum(r.get("computationally_assessed") == "True" for r in primary),
        primary_calibration_equivalence_pass=sum(r.get("calibration_equivalence_pass") == "True" for r in primary),
        primary_zero_probability_contradictions=sum(r.get("proper_score_contradiction") == "True" for r in primary),
        groups=groups,
        primary_composition={role:{field:numeric_range([r for r in composition if int(r["maximum_age"]) == 6 and r["role"] == role],field)
            for field in ("source_ess","largest_source_share","loss_2002","lake_mean_2002","refuge_mean_2002","breeding_pair","same_compartment_pair","age1plus10")}
            for role in ("truth","bank")},
        future_feasibility_selection={role:{field:numeric_range([r for r in selection if int(r["maximum_age"]) == 6 and r["role"] == role],field)
            for field in ("raw_exclusion_fraction","E_weighted_exclusion_fraction","E_weighted_loss_before_future_exclusion")}
            for role in ("truth","bank")},
        actual_remaining_evidence_read=False, actual_historical_probability_computed=False,
        source_bindings={str(Path(__file__).relative_to(ROOT)):binding(Path(__file__))},
        input_bindings={str(p.relative_to(ROOT)):binding(p) for p in [
            directory/"gate/run_manifest.json",directory/"analysis/analysis_receipt.json",
            directory/"analysis/gate_metrics.csv",directory/"analysis/conditional_composition.csv",
            directory/"analysis/future_feasibility_selection.csv",directory/"execution_receipt.json"]})
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "report_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=False)+"\n")
    for name in ("gate_metrics.csv","reliability.csv","conditional_composition.csv","future_feasibility_selection.csv"):
        (output / name).write_bytes((directory / "analysis" / name).read_bytes())
    print(json.dumps({k:summary[k] for k in ("status","primary_qualified","primary_computationally_assessed","primary_status_counts")},sort_keys=True))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    run(parser.parse_args())
