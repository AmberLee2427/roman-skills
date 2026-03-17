# roman-skills

Skill repository for autonomous, high-quality Roman Space Telescope analysis workflows, with a microlensing-first focus.

## Current Status
- Repository plan: `docs/repository-roadmap.md`
- Implemented skills:
  - `skills/roman-plotting/`
  - `skills/roman-timeseries-qc/`
  - `skills/roman-event-summary/`
  - `skills/roman-microlensing-model-compare/`

## Repository Structure
- `skills/`: skill packages (`SKILL.md`, references, scripts, assets)
- `docs/`: roadmap and repository-level conventions
- `research/`: source research notes

## Core Skills
- `roman-plotting` at `skills/roman-plotting/`
- `roman-timeseries-qc` at `skills/roman-timeseries-qc/`
- `roman-event-summary` at `skills/roman-event-summary/`
- `roman-microlensing-model-compare` at `skills/roman-microlensing-model-compare/`

`roman-plotting` provides:
- Microlensing-first plotting workflow
- Publication-oriented style and QA checklists
- Script scaffold for lightcurve + residual plotting
- TeX text rendering enabled by default (`--no-tex` opt-out)

Key files:
- `skills/roman-plotting/SKILL.md`
- `skills/roman-plotting/references/plot-types.md`
- `skills/roman-plotting/references/style-rules.md`
- `skills/roman-plotting/references/qa-checklist.md`
- `skills/roman-plotting/scripts/roman_plot.py`

## Next Skills (Planned)
1. `roman-caustic-visualization`
2. `roman-posterior-diagnostics`
3. `roman-physical-inference`
4. `roman-paper-figures`

## Environment
- Install dependencies: `pip install -r requirements.txt`
