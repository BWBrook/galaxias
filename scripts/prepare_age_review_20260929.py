#!/usr/bin/env python3
"""Reproduce bounded figure digitisation and observation-information checks.

No demographic histories, fitted sources or historical compatibility results
are generated. Lake's source stencil must first be extracted with pdfimages.
"""
from pathlib import Path
import csv
import hashlib
import json
import math

import numpy as np

from galaxias_model.age_observation import conditional_capture_log_probability


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/age_structured_design_20260929"
STENCIL = ROOT / "outputs/age_structured_design_20260929/lake_figure6-000.pbm"


def table(name, rows):
    with (OUT / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def digitize():
    with STENCIL.open("rb") as f:
        assert f.readline() == b"P4\n"
        w, h = map(int, f.readline().split())
        raw = f.read()
    assert (w, h) == (2517, 1649)
    # Stencil is inverted and vertically reflected in the PDF. Work in native
    # pixel coordinates: plotted values increase down this extracted mask.
    ink = (1 - np.unpackbits(np.frombuffer(raw, np.uint8).reshape(h, (w + 7) // 8), axis=1)[:, :w]).astype(bool)
    baseline_x = np.array([690, 890, 1040, 1400, 1560, 1740, 1880, 2110, 2300, 2470])
    baseline_y = [np.median(np.flatnonzero(ink[315:340, x-3:x+4].mean(axis=1) > .7) + 315)
                  for x in baseline_x]
    slope, intercept = np.polyfit(baseline_x, baseline_y, 1)
    # Visually verified centre coordinates of y-axis tick marks 0,4,8,12,16.
    pixels_per_unit = float(np.polyfit([0, 4, 8, 12, 16], [330, 658, 986.5, 1314, 1643], 1)[0])
    rows = []
    for t, x in zip([0, .5, 1, 2, 3, 4, 5], [780, 955, 1125, 1295, 1465, 1630, 1800]):
        yy = np.flatnonzero(ink[310:, x-7:x+8].mean(axis=1) > .8) + 310
        runs = [r for r in np.split(yy, np.flatnonzero(np.diff(yy) > 1) + 1) if len(r) > 2]
        bar_end = float(runs[0][-1]) + .5
        error_end = float(np.mean(runs[1]))
        zero = float(slope * x + intercept)
        mean = (bar_end - zero) / pixels_per_unit
        rows.append(dict(time_label=t, proposed_year=1975 + int(t) if t != .5 else "unresolved",
                         mean_per_site_trip=mean, digitisation_halfwidth=.08,
                         error_bar_top_unclassified=(error_end-zero)/pixels_per_unit,
                         x_native=x, bar_end_y_native=bar_end, baseline_y_native=zero,
                         primary_count_block=t >= 1, status="digitised_mean_not_raw_count"))
    for t in (8, 11, 14):
        rows.append(dict(time_label=t, proposed_year=1975+t, mean_per_site_trip=0,
                         digitisation_halfwidth=0, error_bar_top_unclassified="",
                         x_native="", bar_end_y_native="", baseline_y_native="",
                         primary_count_block=True, status="zero_catch_verified_in_plot_and_prose"))
    table("lake_figure6_digitised.csv", rows)
    early = [r for r in rows if 1 <= r['time_label'] <= 5]
    catch = 12 * sum(r['mean_per_site_trip'] for r in early)
    uncertainty = 12 * len(early) * .08
    return dict(source_pdf_sha256=hashlib.sha256((ROOT / 'outputs/literature/lake_2001/h-lake-inverts-11_01.pdf').read_bytes()).hexdigest(),
                extracted_stencil_sha256=hashlib.sha256(STENCIL.read_bytes()).hexdigest(),
                figure_printed_page=94, methods_printed_page=89, native_width=w, native_height=h,
                pixels_per_unit=pixels_per_unit, baseline_slope=float(slope), baseline_intercept=float(intercept),
                digitisation_halfwidth=.08, halfwidth_kind="conservative reading band, not SE or SD",
                early_visits=[1976,1977,1978,1979,1980], late_visits=[1983,1986,1989],
                sites_per_visit_assumed=12, early_catch_equivalent=catch,
                early_catch_equivalent_interval=[catch-uncertainty,catch+uncertainty],
                raw_count_claim=False, exclude_ambiguous_time_labels=[0,.5])


def support_fraction(low, high):
    upper = min(high, .95)
    def antiderivative(p):
        z = 1-p
        return z-z*math.log(20*z)
    return (antiderivative(upper)-antiderivative(low))/((high-low)*math.log(20/1.2))


def information_controls():
    rows = []
    # Known parameter/known trajectory oracle. Counts are conditioned on 69;
    # this is not end-to-end simulation-based recovery or a fitted real result.
    for feb_effort in (2,4):
        for k in (2.5,5,10,20):
            for rho in (.25,1,4):
                for relative_abundance in (.005,.02,.1,.5,5):
                    early = 43.
                    february = feb_effort * .25
                    late = k * rho * relative_abundance
                    miss_probability = math.exp(-69*math.log1p(late/(early+february)))
                    rows.append(dict(feb_effort=feb_effort, K=k, rho=rho,
                        persistent_late_to_early_abundance=relative_abundance,
                        terminal_loss_template="extinct_before_all_late_visits",
                        survivor_detection_probability=1-miss_probability,
                        oracle_balanced_accuracy=1-.5*miss_probability,
                        oracle_balanced_error=.5*miss_probability))
    table("observation_oracle_controls.csv",rows)
    # Terminal labels differ but effort-weighted late sums are exactly equal.
    loss = [1.,1.,1.,1.,0.]
    persistence = [.8]*5
    a = conditional_capture_log_probability([68,1,0], [43.,.5,5*np.mean(loss)])
    b = conditional_capture_log_probability([68,1,0], [43.,.5,5*np.mean(persistence)])
    assert abs(a-b) < 1e-12
    return dict(kind="observation_templates_not_biologically_qualified_histories",
                loss_annual_late_abundance=loss,persistence_annual_late_abundance=persistence,
                early_and_february_identical=True, conditional_log_score_loss=a,
                conditional_log_score_persistence=b, whole_conditional_distribution_identical=True,
                oracle_balanced_accuracy=.5,
                interpretation="aggregate exposure cannot identify the final year's occupancy without demographic restrictions")


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result = dict(lake=digitize(),
                  isolated_refuge_proposal_fraction={"near_obligate":support_fraction(.9,.99),
                                                    "legacy_range":support_fraction(.35,.9)},
                  matched_exposure_control=information_controls(),
                  demographic_histories_run=0, model_advance_calls=0,
                  full_synthetic_recovery_gate_passed=False)
    (OUT/'observation_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
