# Style Rules

## Global
- Use readable font sizes suitable for paper figures.
- Use colorblind-safe palettes.
- Keep legends compact and non-overlapping.
- Ensure all axes include units when available.
- Use inward ticks for publication mode.
- Use TeX rendering by default for publication-facing figures; disable only when dependencies are unavailable or for fast drafts.

## Astrophysics Conventions
- Invert y-axis for magnitude plots.
- Explicitly state any time offset in x-axis labels.
- Use log scaling only when it improves interpretability and note it in axis label.
- Distinguish data sources (observatory/instrument) by both color and marker.

## Export Standards
- Preferred final formats: `pdf` (vector) plus `png` (>=300 dpi).
- Keep source editable format when possible (`svg` or script + config).
- Avoid jpeg for scientific final figures.

## Labels and Notation
- Use concise labels and standard symbols (for example, `t_E`, `u_0`, `q`, `s`) when those parameters are present.
- Keep significant figures consistent with uncertainties.
