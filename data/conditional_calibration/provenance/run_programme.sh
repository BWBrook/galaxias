#!/usr/bin/env bash
set -uo pipefail
run_dir=/data/codex/scratch/galaxias/conditional_calibration_20260912T034910Z
source_dir=/data/codex/repos/galaxias-conditional-20260912T034910Z
cd "$source_dir" || exit 1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
python_bin="$source_dir/.venv/bin/python"
trap 'exit_code=$?; date -u +%FT%TZ > "$run_dir/finished_utc.txt"; printf "%s\n" "$exit_code" > "$run_dir/exit_code.txt"' EXIT
date -u +%FT%TZ > "$run_dir/started_utc.txt"
run_step() {
  local phase_name="$1"
  shift
  printf '%s\n' "$phase_name" > "$run_dir/current_step.txt"
  date -u +%FT%TZ > "$run_dir/${phase_name}_started_utc.txt"
  "$@" > "$run_dir/${phase_name}.log" 2>&1
  local result=$?
  printf '%s\n' "$result" > "$run_dir/${phase_name}_exit_code.txt"
  date -u +%FT%TZ > "$run_dir/${phase_name}_finished_utc.txt"
  return "$result"
}
run_step prior "$python_bin" scripts/run_conditional_calibration.py --phase prior --output-dir "$run_dir/prior" --workers 32 || exit $?
old_pilot=/data/codex/scratch/galaxias/observation_repair_pilot_20260908T004649Z/pilot
old_screen=/data/codex/scratch/galaxias/terminal_history_screen_20260908T012648Z
run_step screen "$python_bin" scripts/run_conditional_calibration.py --phase screen --prior-dir "$run_dir/prior" --output-dir "$run_dir/screen" --workers 32 --old-seed-file "$old_pilot/stage_b_replicates.csv.gz" --old-seed-file "$old_pilot/validation_replicates.csv.gz" --old-seed-file "$old_screen/screen/raw_replicates.csv.gz" --old-seed-file "$old_screen/confirm/raw_replicates.csv.gz" --old-seed-file "$old_screen/extend/raw_replicates.csv.gz" --old-seed-file "$run_dir/parameter_seed_preflight.csv" || exit $?
run_step screen_analysis "$python_bin" scripts/analyze_conditional_calibration.py --phase-dir "$run_dir/screen" --output-dir "$run_dir/screen_analysis" || exit $?
run_step refine "$python_bin" scripts/run_conditional_calibration.py --phase refine --prior-dir "$run_dir/prior" --output-dir "$run_dir/refine" --source-ids "$run_dir/screen_analysis/candidates.csv" --workers 32 --previous-phase-dir "$run_dir/screen" || exit $?
run_step refine_analysis "$python_bin" scripts/analyze_conditional_calibration.py --phase-dir "$run_dir/refine" --output-dir "$run_dir/refine_analysis" --previous-membership "$run_dir/screen_analysis/selection_membership.csv" || exit $?
run_step validate "$python_bin" scripts/run_conditional_calibration.py --phase validate --prior-dir "$run_dir/prior" --output-dir "$run_dir/validate" --source-ids "$run_dir/refine_analysis/candidates.csv" --workers 32 --previous-phase-dir "$run_dir/screen" --previous-phase-dir "$run_dir/refine" || exit $?
run_step validate_analysis "$python_bin" scripts/analyze_conditional_calibration.py --phase-dir "$run_dir/validate" --output-dir "$run_dir/validate_analysis" --final-membership "$run_dir/refine_analysis/selection_membership.csv" || exit $?
run_step summary "$python_bin" scripts/summarize_conditional_calibration.py --screen-dir "$run_dir/screen_analysis" --refine-dir "$run_dir/refine_analysis" --validate-dir "$run_dir/validate_analysis" --prior-dir "$run_dir/prior" --output-dir "$run_dir/summary" || exit $?
printf 'complete\n' > "$run_dir/current_step.txt"
