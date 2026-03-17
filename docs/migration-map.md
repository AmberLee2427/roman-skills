# Migration Map

## Path Moves
- `skills/roman-timeseries-qc` -> `skills/qc/timeseries`
- `skills/roman-event-summary` -> `skills/modeling/summary-statistics/event-summary`
- `skills/roman-microlensing-model-compare` -> `skills/modeling/model-compare/microlensing`
- `skills/roman-plotting` -> `skills/plotting/plot-types/lightcurve-residuals`

## New Additions
- `skills/plotting/style-profiles`
- `skills/plotting/accessibility-checks`
- `skills/photometry/aperture` (scaffold)
- `skills/photometry/difference-imaging` (scaffold)
- `automation/hooks/*` for generic hook templates
- `automation/gates/run_plot_gates.sh` for reusable style+accessibility checks

## Compatibility Note
Any tooling that referenced old flat paths must be updated to the new nested paths.
