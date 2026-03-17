---
name: "roman-plotting"
description: "Generate publication-quality Roman and microlensing figures from local analysis outputs. Use when the task requires time-series/event plotting, residual panels, caustic geometry views, posterior/corner visualizations, or journal-ready export settings with consistent scientific conventions."
---

# Roman Plotting Skill

## Purpose
Provide a repeatable plotting workflow for Roman data analysis, prioritizing microlensing diagnostics and publication-grade figure quality.

## Use This Skill When
- The user requests any Roman/microlensing figure.
- Existing plots need standardization (axes, labels, units, legend, export format).
- You need residual panels, anomaly zooms, or posterior diagnostic figures.

## Inputs You Should Confirm
- Data source path(s).
- Plot type (lightcurve, residuals, caustic, corner, mass-distance, CMD, astrometry).
- Output directory and filename stem.
- Target use: exploratory notebook vs publication-ready export.

## Workflow
1. Inspect data schema and verify required columns.
2. Select template from `references/plot-types.md`.
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
