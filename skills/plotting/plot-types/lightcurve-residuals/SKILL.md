---
name: "roman-plotting-plot-types-lightcurve-residuals"
description: "Generate Roman lightcurve figures with optional model residual panels from local analysis outputs, with publication-ready labels and export conventions."
---

# Roman Plotting Plot Type: Lightcurve + Residuals

## Purpose
Provide a repeatable plotting workflow for Roman data analysis, prioritizing microlensing diagnostics and publication-grade figure quality.

## Use This Skill When
- The user requests a Roman lightcurve figure, with or without residual panel.
- Existing lightcurve plots need standardized axes, labels, units, legends, and exports.
- You need a deterministic plotting entrypoint for publication figures.
- Optional: posterior sample trajectories should be overlaid as transparent model curves.
- Optional: multiband lightcurves must be aligned to a declared reference band.

## Inputs You Should Confirm
- Data source path(s).
- Output directory and filename stem.
- Target use: exploratory notebook vs publication-ready export.
- Optional posterior sample model columns (only for posterior-sampling workflows).

## Workflow
1. Inspect data schema and verify required columns.
2. Confirm lightcurve/residual layout expectations from `references/plot-types.md`.
3. Apply style and labeling rules from `references/style-rules.md`.
4. Generate figure via `scripts/roman_plot.py` (or equivalent local script).
5. Export both editable and publication formats where applicable.
6. Validate with checklist in `references/qa-checklist.md`.

## Microlensing Defaults
- Time axis: use HJD/BJD offset labeling when appropriate (e.g., `HJD - 2450000`).
- Magnitude plots: invert y-axis.
- TeX text rendering: enabled by default (`--no-tex` to disable).
- Include residual panel for model-fit plots.
- Distinguish observatories by marker shape + color.
- Overlay baseline model (e.g., 1L1S dashed) when comparing to planetary model.
- Include anomaly zoom inset for short-timescale perturbations when present.
- For long baselines, allow model-driven head/tail baseline trimming with explicit threshold metadata.

## Output Contract
Return:
- `status`: `ok | warning | error`
- `summary`: one-sentence description of produced figure(s)
- `artifacts`: absolute output paths
- `validation`: checklist results with any caveats
- `provenance`: input file paths and run timestamp

## Constraints
- Do not fabricate data points or uncertainties.
- Do not drop units/frames in labels when known.
- Avoid lossy formats for final publication exports.
- In TeX mode, fail fast with actionable dependency errors rather than raw tracebacks.
- If required columns are missing, stop and report exactly what is missing.

## References
- `references/plot-types.md`
- `references/style-rules.md`
- `references/qa-checklist.md`

## Scripts
- `scripts/roman_plot.py`
