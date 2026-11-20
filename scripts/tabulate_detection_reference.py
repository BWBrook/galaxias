#!/usr/bin/env python3
"""Analytical observation reference; does not run the ecological simulator."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from galaxias_model.abundance_detection import (
    COMMON_EPISODE_FIELDS, Q_SCENARIOS, common_history_log_likelihood,
)


def tabulate() -> pd.DataFrame:
    rows = []
    for q in Q_SCENARIOS:
        optimum = math.log(5 / 12) / math.log1p(-q)
        for n in (1., 3.75, 10., 20., 50., 70., 100., 200., optimum):
            features = pd.DataFrame([[n]*7 + [0.]*2 + [n]*5], columns=COMMON_EPISODE_FIELDS)
            for model in ("homogeneous", "shared_quality"):
                log_probability = float(common_history_log_likelihood(features, q, model)[0])
                rows.append(dict(q=q, constant_refuge_n=n, observation_model=model,
                                 log_probability=log_probability, probability=math.exp(log_probability),
                                 homogeneous_optimum_n=optimum,
                                 interpretation="Constant refuge, empty lake; not a simulator prediction or viable history"))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    output.parent.mkdir(parents=True, exist_ok=True)
    tabulate().to_csv(output, index=False, float_format="%.17g")
