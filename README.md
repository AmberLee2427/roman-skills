# roman-skills

Skill repository for autonomous Roman Space Telescope analysis workflows.

## Current Status
- Repository plan: `docs/repository-roadmap.md`
- Hierarchy and migration map: `docs/skill-hierarchy.md`, `docs/migration-map.md`

## Repository Structure
- `skills/`: skill packages (`SKILL.md`, `references/`, `scripts/`, `assets/`)
- `docs/`: roadmap and repository-level conventions
- `research/`: source research notes
- `automation/`: platform-neutral hook templates and gate runners

## Skill Hierarchy
- `skills/qc/timeseries`
- `skills/photometry/aperture` (scaffold)
- `skills/photometry/difference-imaging` (scaffold)
- `skills/modeling/summary-statistics/event-summary`
- `skills/modeling/summary-statistics/convergence-tests`
- `skills/modeling/model-selection/evidence-bic`
- `skills/modeling/model-compare/microlensing`
- `skills/modeling/retrieval` (scaffold)
- `skills/modeling/microlensing/pspl`
- `skills/modeling/microlensing/fspl`
- `skills/modeling/microlensing/parallax`
- `skills/modeling/microlensing/2s1l`
- `skills/modeling/microlensing/1s2l`
- `skills/modeling/microlensing/lom`
- `skills/modeling/microlensing/xallarap`
- `skills/modeling/microlensing/2s2l`
- `skills/modeling/microlensing/1s3l`
- `skills/plotting/plot-types/lightcurve-residuals`
- `skills/plotting/style-profiles`
- `skills/plotting/accessibility-checks`

## Plotting and Accessibility
`skills/plotting/plot-types/lightcurve-residuals/scripts/roman_plot.py` supports:
- Data + best-fit model + optional initial model
- Optional transparent posterior sample overlays
- Residual panel generation
- Explicit y-quantity semantics via `--y-kind` (`magnification|flux|magnitude|delta_flux`)
- Multiband overlays via repeatable `--band-spec` with per-band columns and labels
- Cross-band normalization to a reference band via `--normalize-mode` + `--normalize-reference-band`
- Optional `--model-x-col` for higher-resolution model/posterior/initial curves
- Residual-panel error bars when `--err-col` is provided
- If model/data x-cadence differs, provide residuals explicitly via `--residual-col`
- Manual x-windowing via `--x-zoom-range xmin,xmax`
- Model-driven head/tail baseline trimming via `--auto-x-zoom trim-baseline`
- Baseline definition for auto-zoom via scalar inference/override or `--baseline-col`
- Manifest output for downstream quality gates
- Importable API for controlled customization: `render_lightcurve(args)` returns `(fig, manifest)` before file write

`skills/plotting/accessibility-checks/scripts/check_accessibility.py` uses:
- `accessiplot.detection.color_detection` for CVD-aware color checks
- Supplemental marker/style and line-visibility checks from manifest metadata

## Automation
- Generic hook templates: `automation/hooks/`
- Gate runner: `automation/gates/run_plot_gates.sh`

## Environment
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `python -m unittest discover -s tests -p 'test_*.py'`
