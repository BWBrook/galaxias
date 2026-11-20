"""Describe observation requirements of frozen examples; no new selection or simulation."""
from pathlib import Path
import hashlib
import json
import math

import pandas as pd
import numpy as np

from interrogate_common_histories import concentration, mean_se, read_verified, weights
from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/common_model/interrogation_20260920"
OUT = ROOT / "data/common_model/ecological_assessment_20260920"
KEY = ["source_id", "q", "observation_model"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def miss_probability(exposure, q, shared):
    if shared:
        return .5 * (math.exp(exposure * math.log1p(-.5*q))
                     + math.exp(exposure * math.log1p(-1.5*q)))
    return math.exp(exposure * math.log1p(-q))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = json.loads((SOURCE / "receipt.json").read_text())
    names = ["selected_cases.csv", "case_annual_refuge.csv", "illustrative_histories.csv",
             "survivor_conditioned_natural_counts.csv.gz", "case_parameters.csv"]
    for name in names:
        assert digest(SOURCE/name) == receipt["outputs"][name]["sha256"], name
    cases, annual, examples, counts, params = [pd.read_csv(SOURCE/n) for n in names]
    rows = []
    for key, roles in cases.groupby(KEY, sort=True):
        a = annual[(annual.source_id == key[0]) & (annual.q == key[1]) & (annual.observation_model == key[2])]
        c = counts[(counts.source_id == key[0]) & (counts.q == key[1]) & (counts.observation_model == key[2])]
        assert len(a) == 38 and len(c) == 6
        end = c[c.state_year == 2002].iloc[0]
        row = {k: roles.iloc[0][k] for k in KEY + ["restriction", "configuration", "weighted_terminal_survival", "K_R"]}
        row["selection_roles"] = ";".join(roles.role)
        for year in [1987, 1988, 1991, 1995, 2002]:
            row[f"factual_mean_refuge_{year}"] = float(a.loc[a.year == year, "weighted_refuge_mean"].iloc[0])
        row["mean_total_1997_2001_given_survival"] = c.loc[c.state_year < 2002, "natural_total_mean_given_terminal_survival"].mean()
        for col in ["natural_total_mean_given_terminal_survival", "conditional_ess", "conditional_weight_qualified"]:
            row[f"endpoint_{col}"] = end[col]
        # The existing endpoint identity is valid because extinct histories have zero endpoint counts.
        row["endpoint_refuge_mean_given_survival"] = row["factual_mean_refuge_2002"] / row["weighted_terminal_survival"]
        row["endpoint_lake_mean_given_survival"] = row["endpoint_natural_total_mean_given_terminal_survival"] - row["endpoint_refuge_mean_given_survival"]
        p = params[params.source_id == key[0]].set_index("parameter_id").value_natural
        for pid in ["PR003", "PR004", "PR005", "PR006", "PR033", "PR034"]:
            row[pid] = p[pid]
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT/"case_evidence_requirements.csv", index=False, float_format="%.17g")
    rows = []
    for e in examples.to_dict("records"):
        exposure = sum(e[f"neg_N_total_{year}"] for year in range(1998, 2003))
        row = {k: e[k] for k in KEY + ["restriction", "configuration", "replicate_index", "outcome", "outcome_weight_qualified"]}
        row["total_model_count_episodes_1997_2001"] = exposure
        row["counts_actual_1997_2002"] = ";".join(str(int(e[f"neg_N_total_{y}"])) for y in range(1998, 2003)) + ";" + str(int(e["endpoint_N_total_2002"]))
        path = [e[f"neg_N_total_{y}"] for y in range(1998, 2003)] + [e["endpoint_N_total_2002"]]
        row["one_fish_rebound_year_pairs"] = ";".join(f"{1997+i}-{1998+i}" for i in range(5) if path[i] == 1 and path[i+1] > 1)
        for q in [.005, .02, .05, .2]:
            for law in ["homogeneous", "shared_quality"]:
                row[f"late_miss_q{q}_{law}"] = miss_probability(exposure, q, law == "shared_quality")
        # Independent product identity for the homogeneous five-record block.
        product = math.prod((1-e["q"])**e[f"neg_N_total_{y}"] for y in range(1998, 2003))
        assert math.isclose(product, miss_probability(exposure, e["q"], False), rel_tol=1e-12, abs_tol=1e-300)
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT/"illustrative_detection_requirements.csv", index=False, float_format="%.17g")
    constants = [{"constant_count": n, "record_count": 5, "q": q,
                  "homogeneous_all_missed": miss_probability(5*n, q, False),
                  "shared_quality_all_missed": miss_probability(5*n, q, True)}
                 for n in [20, 50, 100, 200] for q in [.005, .02, .05, .2]]
    pd.DataFrame(constants).to_csv(OUT/"constant_population_reference.csv", index=False, float_format="%.17g")
    # A descriptive diagnosis of the existing low-count approximation, not an exclusion/reweighting rule.
    columns = list(COMMON_EPISODE_FIELDS) + ["source_id", "replicate_index", "early_early_patterns_pass",
                                            "removals_valid", "endpoint_terminal_survival", "endpoint_N_total_2002"]
    wanted = set(cases.source_id)
    chunks = read_verified("validate", "raw_histories.csv.gz", usecols=columns, chunksize=50000)
    raw = pd.concat([c[c.source_id.isin(wanted)] for c in chunks], ignore_index=True)
    groups = raw.groupby("source_id")
    assert groups.size().eq(1024).all() and set(groups.groups) == wanted
    diagnostic = []
    for row in cases.drop_duplicates(KEY).itertuples(index=False):
        part = groups.get_group(row.source_id).sort_values("replicate_index")
        w, logs = weights(part, row.q, row.observation_model)
        survive = part.endpoint_terminal_survival.to_numpy(float)
        assert math.isclose(float(w@survive), row.weighted_terminal_survival, rel_tol=1e-11, abs_tol=1e-12)
        states = part[[f"neg_N_total_{y}" for y in range(1998,2003)] + ["endpoint_N_total_2002"]].to_numpy()
        assert not np.any((states[:,:-1] == 0) & (states[:,1:] > 0))
        flag = np.any((states[:,:-1] == 1) & (states[:,1:] > 1), axis=1).astype(float)
        wc = w*survive; wc /= wc.sum()
        c = concentration(wc)
        estimate, se = mean_se(flag,wc)
        diagnostic.append({**{k:getattr(row,k) for k in KEY+["restriction","configuration"]},
                           "supported_rebound_histories":int(((flag>0)&np.isfinite(logs)).sum()),
                           "factual_weighted_rebound_mass":float(w@flag),
                           "rebound_mass_given_survival":estimate,"rebound_mass_given_survival_mc_se":se,
                           "survivor_weight_ess":c["ess"],"survivor_weight_qualified":c["qualified"]})
    pd.DataFrame(diagnostic).to_csv(OUT/"one_fish_rebound_diagnostic.csv",index=False,float_format="%.17g")
    assert miss_probability(0, .02, True) == 1
    for q in [.005, .02, .05, .2]:
        assert miss_probability(100, q, True) >= miss_probability(100, q, False)
    summary = {"status": "complete", "new_histories": 0, "case_profiles": len(cases.drop_duplicates(KEY)),
               "illustrative_histories": len(examples), "inputs": {n: digest(SOURCE/n) for n in names},
               "script_sha256": digest(Path(__file__)), "outputs": {p.name: digest(p) for p in OUT.glob("*.csv")},
               "diagnostic_inputs": {"interrogate_common_histories.py":digest(ROOT/"scripts/interrogate_common_histories.py"),
                                     "abundance_detection.py":digest(ROOT/"src/galaxias_model/abundance_detection.py"),
                                     "validate/raw_histories.csv.gz":digest(ROOT/"outputs/remote/common_model_20260918/production/validate/raw_histories.csv.gz")},
               "interpretation": "Miss probabilities are observation-model requirements for fixed illustrative paths, not new evidence, posterior predictive checks, q estimates, or mechanism ranks."}
    (OUT/"receipt.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps({k: summary[k] for k in ["status", "new_histories", "case_profiles", "illustrative_histories"]}))


if __name__ == "__main__":
    main()
