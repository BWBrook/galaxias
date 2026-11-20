#!/usr/bin/env python3
"""Export descriptive tables from the completed, frozen early-Lake gate."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize(run, output):
    run, output = Path(run), Path(output)
    report = json.loads((run / "analysis/recovery_gate.json").read_text())
    manifest = json.loads((run / "gate/manifest.json").read_text())
    assert manifest["status"] == "complete" and manifest["accounting"]["history_rows"] == 49152
    assert report["attempted_histories"] == 49152 and report["run_mode"] == "gate"
    assert len(report["groups"]) == 32 and not report["historical_observations_read"]
    output.mkdir(parents=True, exist_ok=True)
    coverage, directed, stability, counts = [], [], [], []
    for group in report["groups"]:
        identity = {key: group[key] for key in ("maximum_age", "quality_regime", "index_stratum", "profile")}
        for role, classes in group["counts"].items():
            for true, values in classes.items():
                counts.append(identity | {"role": role, "true_restriction": true} | values)
        for bank, values in group["banks"].items():
            for true, values_true in values["coverage"].items():
                coverage.append(identity | {"bank": bank, "true_restriction": true} | values_true |
                                {"support_fraction": values["support_fraction"][true],
                                 "empty_sets": values["empty_sets"][true]})
            for pair, values_pair in values["directed"].items():
                directed.append(identity | {"bank": bank, "directed_pair": pair} | values_pair |
                                {"informative": values_pair["lower"] > .5})
        for comparison, classes in group["stability"].items():
            for true, values in classes.items():
                stability.append(identity | {"bank_comparison": comparison, "true_restriction": true} | values)
    for filename, rows in (("conditional_sample_counts.csv", counts), ("coverage.csv", coverage),
                           ("directed_exclusion.csv", directed), ("bank_stability.csv", stability)):
        write_csv(output / filename, rows)
    with gzip.open(run / "gate/sources.jsonl.gz", "rt") as handle:
        sources = [json.loads(line) for line in handle]
    source_counts = Counter((s["maximum_age"], s["role"], s["index_stratum"], s["quality_regime"], s["feasible"]) for s in sources)
    write_csv(output / "source_accounting.csv", [dict(zip(
        ("maximum_age", "role", "index_stratum", "quality_regime", "feasible", "sources"), (*key, value)))
        for key, value in sorted(source_counts.items())])
    primary = [g for g in report["groups"] if g["maximum_age"] == 6]
    sensitivity = [g for g in report["groups"] if g["maximum_age"] == 8]
    summary = {key: report[key] for key in ("decision", "qualified_primary_groups", "primary_failure_reasons",
                                          "robust_primary_directed_pairs", "historical_comparison_permitted")}
    summary.update({"history_accounting": manifest["accounting"], "source_rows": len(sources),
                    "raw_pair_intersection_is_qualifying": report["historical_comparison_permitted"],
                    "qualified_directed_pairs": report["robust_primary_directed_pairs"]
                    if report["historical_comparison_permitted"] else [],
                    "distinct_source_ids": len({s["source_id"] for s in sources}),
                    "algebraically_feasible_source_ids": len({s["source_id"] for s in sources if s["feasible"]}),
                    "sensitivity_qualified_groups": sum(g["qualified"] for g in sensitivity),
                    "sensitivity_failure_reasons": dict(Counter(r for g in sensitivity for r in g["reasons"])),
                    "generation_seconds": manifest["elapsed_seconds"], "analysis_seconds": report["runtime_seconds"],
                    "historical_observations_read": report["historical_observations_read"]})
    for label, groups in (("primary", primary), ("sensitivity", sensitivity)):
        bank_values = [v for g in groups for bank in g["banks"].values() for v in bank["coverage"].values()]
        pair_values = [v for g in groups for bank in g["banks"].values() for v in bank["directed"].values()]
        agreements = [v["set_agreement"] for g in groups for bank in g["stability"].values() for v in bank.values()]
        summary[label + "_descriptive_ranges"] = {
            "calibration_z1": [min(g["counts"]["calibration"][r]["z1"] for g in groups for r in g["counts"]["calibration"]),
                                max(g["counts"]["calibration"][r]["z1"] for g in groups for r in g["counts"]["calibration"])],
            "coverage_rate": [min(v["rate"] for v in bank_values), max(v["rate"] for v in bank_values)] if bank_values else None,
            "coverage_lower": [min(v["lower"] for v in bank_values), max(v["lower"] for v in bank_values)] if bank_values else None,
            "directed_exclusion_lower": [min(v["lower"] for v in pair_values), max(v["lower"] for v in pair_values)] if pair_values else None,
            "set_agreement": [min(agreements), max(agreements)] if agreements else None}
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    for filename in ("recovery_gate.json", "group_summary.csv"):
        source = run / "analysis" / filename
        if filename.endswith(".csv"):
            # The immutable run artifact stays intact; the compact repository
            # table uses the project's LF convention with identical cell values.
            (output / filename).write_text(source.read_text())
        else:
            (output / filename).write_bytes(source.read_bytes())
    for filename, original in (("generation_manifest.json", run / "gate/manifest.json"),
                               ("execution_receipt.json", run / "execution_receipt.json")):
        (output / filename).write_bytes(original.read_bytes())
    print(json.dumps(summary, sort_keys=True))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data/early_lake_mechanism_20261004")
    args = parser.parse_args()
    summarize(args.run, args.output)
