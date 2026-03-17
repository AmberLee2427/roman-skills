# Lightcurve Residuals Customization Examples

This folder shows how to:

1. Keep the strict `roman_plot.py` rendering path for scientific defaults.
2. Apply controlled post-processing customizations in your own script.
3. Explicitly mark customized figures in manifest metadata.
4. Build a composite figure containing two lightcurves as subplots.

These examples use the importable API added to:

- `skills/plotting/plot-types/lightcurve-residuals/scripts/roman_plot.py`
- `render_lightcurve(args, df=None) -> (fig, manifest)`
- `write_outputs(fig, manifest, args) -> None`

## Why this split exists

The strict skill path is meant to prevent bad defaults and ambiguous scientific plots.

Sometimes you still need local overrides (for example, enabling gridlines for a talk, internal note, or debugging cadence/systematics).

The pattern used in these examples is:

1. Render strictly first (`render_lightcurve`).
2. Apply custom styling in your script.
3. Set manifest flags:
   - `figure.postprocess_customized = true`
   - `figure.policy_profile = "customized-from-strict"`
4. Save outputs via `write_outputs`.

This preserves traceability: anyone reading the manifest can see the figure is derived from strict policy output but modified.

## Example 1: Single event with grid customization

Script:

- `customize_single_event.py`

What it does:

1. Creates a synthetic microlensing-like event CSV.
2. Calls strict rendering via `render_lightcurve`.
3. Turns on major/minor grid lines in both panels.
4. Adds a custom annotation.
5. Marks manifest as customized.
6. Writes PDF/PNG/manifest.

Run:

```bash
python skills/plotting/plot-types/lightcurve-residuals/examples/customize_single_event.py
```

Outputs:

- `tmp/examples/custom_single_event.pdf`
- `tmp/examples/custom_single_event.png`
- `tmp/examples/custom_single_event.meta.json`

## Example 2: Two lightcurves as subplots

Script:

- `custom_two_event_subplots.py`

What it does:

1. Creates two synthetic event CSV files with different anomaly timing/shape.
2. Renders each event with strict defaults via `render_lightcurve`.
3. Applies per-event customization (grid + in-panel labels).
4. Marks each manifest as customized.
5. Saves each customized event output.
6. Builds a combined two-row subplot figure by embedding each rendered panel as an image.
7. Saves the combined figure.

Run:

```bash
python skills/plotting/plot-types/lightcurve-residuals/examples/custom_two_event_subplots.py
```

Outputs:

- Individual customized plots:
  - `tmp/examples/event_a_custom.pdf`
  - `tmp/examples/event_a_custom.png`
  - `tmp/examples/event_a_custom.meta.json`
  - `tmp/examples/event_b_custom.pdf`
  - `tmp/examples/event_b_custom.png`
  - `tmp/examples/event_b_custom.meta.json`
- Combined 2-row subplot figure:
  - `tmp/examples/two_events_subplots.pdf`
  - `tmp/examples/two_events_subplots.png`

## Notes and caveats

1. The strict renderer still enforces scientific guardrails before customization runs.
2. If your customizations violate house style, that is intentional and explicit in manifest metadata.
3. These examples use TeX-rendered text when TeX dependencies are available.
4. For publication plots, keep strict mode output unless there is a documented reason to customize.
