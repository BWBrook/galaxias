from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_prior_pack.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_prior_pack", VALIDATOR_PATH)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)


def test_direct_pedder_prior_requires_evidence_link() -> None:
    rows = deepcopy(VALIDATOR.read_csv(VALIDATOR.DATA_DIR / "parameter_priors.csv"))
    direct_row = next(row for row in rows if row["source_strategy"] == "direct_pedder")
    direct_row["evidence_ids"] = ""

    with pytest.raises(ValueError, match="cannot be direct_pedder without evidence_ids"):
        VALIDATOR.validate_prior_rows(rows, VALIDATOR.load_evidence_ids())
