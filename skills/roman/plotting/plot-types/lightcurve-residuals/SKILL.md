---
name: "roman-plotting-plot-types-lightcurve-residuals"
description: "Generate Roman lightcurve figures with optional model residual panels from local analysis outputs, with publication-ready labels and export conventions."
---

<essential_principles>
Default to the strict renderer for Roman lightcurve work.

Only use customization guidance when the user explicitly asks for post-processing, composite layouts, talk-specific styling, or another output that the strict path cannot satisfy cleanly.

Preserve scientific semantics over aesthetics:
- Do not fabricate data points or uncertainties.
- Do not drop units or time-frame conventions when known.
- If required columns are missing, stop and report exactly what is missing.
- In TeX mode, fail fast with actionable dependency errors rather than raw tracebacks.
</essential_principles>

<workflow>
For the normal path, do this:

1. Confirm input paths, output stem, and whether the figure is exploratory or publication-facing.
2. Read `references/plot-types.md` for the required lightcurve-plus-residual layout.
3. Read `references/style-rules.md` for labels, axis semantics, export rules, and microlensing conventions.
4. Generate the figure with `scripts/roman_plot.py`.
5. Read `references/qa-checklist.md` and validate the result before returning it.

Use this strict path by default for:
- standard lightcurve plots
- model-fit plots with residuals
- posterior overlay plots
- multiband plots that still fit the built-in normalization workflow
- publication-ready exports
</workflow>

<exception_path>
Read `examples/README.md` only if one of these is true:

- The user explicitly asks to customize styling beyond strict defaults.
- The user needs a composite figure such as multiple lightcurves in shared subplots.
- The user asks for a gallery or side-by-side style comparison.
- The strict renderer cannot satisfy the requested layout without controlled post-processing.

When you enter this exception path:
- Render strictly first.
- Apply the smallest necessary customization afterward.
- Preserve manifest traceability indicating the figure was customized from strict output.
</exception_path>

<microlensing_defaults>
Apply these defaults unless the data or user request requires otherwise:
- Use HJD/BJD offset labeling when appropriate, such as `HJD - 2450000`.
- Invert the y-axis for magnitude plots.
- Enable TeX text rendering by default; use `--no-tex` only when needed.
- Include a residual panel for model-fit diagnostics.
- Distinguish observatories by both marker shape and color.
- Overlay a baseline model such as 1L1S when that comparison is scientifically relevant.
- Include an anomaly zoom inset when a short-timescale perturbation is present.
- For long baselines, allow model-driven head/tail trimming only with explicit threshold metadata.
</microlensing_defaults>

<output_contract>
Return:
- `status`: `ok | warning | error`
- `summary`: one-sentence description of produced figure(s)
- `artifacts`: absolute output paths
- `validation`: checklist results with any caveats
- `provenance`: input file paths and run timestamp
</output_contract>

<references>
Read as needed:
- `references/plot-types.md` for required layout and allowed variants
- `references/style-rules.md` for style and export policy
- `references/qa-checklist.md` for final validation
- `examples/README.md` only for exception-path customization or composition
</references>

<scripts>
Primary executable entrypoint:
- `scripts/roman_plot.py`
</scripts>
