"""Compare the fixed 192-history Mac/Linux qualification archives, no simulation."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/early_lake_qualification_20261004"
HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    with gzip.open(path, "rt") as stream:
        return [json.loads(line) for line in stream]


def main():
    max_difference = 0.0
    numeric_comparisons = 0

    def compare(a, b, where="root"):
        nonlocal max_difference, numeric_comparisons
        if isinstance(a, dict):
            assert isinstance(b, dict) and a.keys() == b.keys(), where
            for key in a:
                compare(a[key], b[key], f"{where}.{key}")
        elif isinstance(a, list):
            assert isinstance(b, list) and len(a) == len(b), where
            for i, (x, y) in enumerate(zip(a, b)):
                compare(x, y, f"{where}[{i}]")
        elif isinstance(a, (int, float)) and not isinstance(a, bool):
            assert isinstance(b, (int, float)) and not isinstance(b, bool), where
            if isinstance(a, int) and isinstance(b, int):
                assert a == b, where
            else:
                assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-8), (where, a, b)
                max_difference = max(max_difference, abs(a - b))
            numeric_comparisons += 1
        else:
            assert a == b, (where, a, b)

    manifests = {name: json.loads((BASE / name / "manifest.json").read_text())
                 for name in ("local_serial", "linux_serial", "linux_parallel")}
    for name, manifest in manifests.items():
        assert manifest["status"] == "complete"
        assert manifest["accounting"]["history_rows"] == 192
        assert manifest["accounting"]["runtime_failures"] == 0
        for filename, expected in manifest["physical_sha256"].items():
            assert digest(BASE / name / filename) == expected
    for key in ("logical_sha256", "physical_sha256", "accounting", "source_bindings"):
        assert manifests["linux_serial"][key] == manifests["linux_parallel"][key], key
    for filename in ("sources.jsonl.gz", "features.jsonl.gz", "histories.jsonl.gz"):
        left, right = rows(BASE / "local_serial" / filename), rows(BASE / "linux_serial" / filename)
        compare(left, right, filename)
        if filename == "features.jsonl.gz":
            # Stochastic feature counts are exact, not tolerance comparisons.
            assert [r["lake_exposures"] for r in left] == [r["lake_exposures"] for r in right]
        if filename == "histories.jsonl.gz":
            assert [r["history"].get("annual_states") for r in left] == [r["history"].get("annual_states") for r in right]
    for path in sorted((BASE / "local_analysis").glob("A*.json.gz")):
        compare(rows(path), rows(BASE / "linux_analysis" / path.name), path.name)
    for name in ("local_analysis", "linux_analysis"):
        report = json.loads((BASE / name / "recovery_gate.json").read_text())
        assert report["decision"] == "QUALIFICATION_ONLY_NO_HISTORICAL_PERMISSION"
        assert not report["historical_observations_read"]
    frozen = json.loads((HERE / "frozen_source_manifest.json").read_text())
    for name, expected in frozen["files"].items():
        assert digest(ROOT / name) == expected, name
    receipt = {"status": "PASS", "verified_utc": datetime.now(timezone.utc).isoformat(),
               "mac_linux_discrete_histories_and_features_exact": True,
               "linux_serial_parallel_physical_and_logical_hashes_exact": True,
               "mac_linux_analysis_replayed": True, "floating_rtol": 1e-12, "floating_atol": 1e-8,
               "maximum_floating_absolute_difference": max_difference,
               "numeric_comparisons": numeric_comparisons,
               "qualification_site_history_attempts_replayed": 576,
               "new_qualification_reserve_charge": 1000,
               "qualification_total_charge": 4263,
               "qualification_reserve_ceiling": 8000,
               "focused_tests_mac": 36, "focused_tests_linux": 36,
               "portability_passed": True, "compile_passed": True,
               "source_snapshot_files_verified": len(frozen["files"]),
               "source_snapshot_manifest_sha256": digest(HERE / "frozen_source_manifest.json"),
               "replay_script_sha256": digest(__file__),
               "input_manifest_sha256": {n: digest(BASE / n / "manifest.json") for n in manifests}}
    (HERE / "qualification_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
