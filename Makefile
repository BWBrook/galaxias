.PHONY: setup portability compile test check smoke module3-5 module3-75 module4-smoke clean

setup:
	uv sync --locked

portability:
	uv run python scripts/check_portability.py

compile:
	uv run python -m compileall -q src scripts tests

test:
	uv run pytest

check: portability compile test

smoke:
	uv run python scripts/validate_prior_pack.py
	uv run python scripts/run_latent_simulation.py --family-id transient_perfect_storm --seed 1 --deterministic --output-dir outputs/smoke_latent
	uv run python scripts/score_historical_run.py --family-id transient_perfect_storm --seed 1 --stochastic --replicates 2 --output-dir outputs/smoke_score
	uv run python scripts/run_module3_calibration.py --stage stage_a --families trout_only --stage-a-draws-per-family 2 --stage-a-keep-per-family 1 --workers 1 --batch-size 1 --seed 1 --output-dir outputs/smoke_module3

module3-5:
	uv run python scripts/review_module3_5_diagnostics.py

module3-75:
	uv run python scripts/review_module3_75_observation_bridge.py

module4-smoke:
	uv run python scripts/run_module4_observation_sensitivity.py \
		--output-dir outputs/module4/smoke \
		--variants baseline_current late_bridge_soft \
		--seeds 20260410 \
		--stage-a-draws-per-family 3 \
		--stage-a-keep-per-family 1 \
		--stage-b-historical-replicates 1 \
		--final-acceptance-cap 5 \
		--workers 1 \
		--batch-size 10 \
		--clean

clean:
	rm -rf outputs .pytest_cache scripts/__pycache__ src/galaxias_model/__pycache__ tests/__pycache__
