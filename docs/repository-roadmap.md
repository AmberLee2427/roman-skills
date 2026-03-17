# Roman Skills Repository Roadmap

## Mission
Build a focused, reusable skill library that helps coding agents perform reliable, publication-grade analysis on Nancy Grace Roman Space Telescope data, with microlensing as the first-class science case.

## Design Principles
- Microlensing-first defaults, Roman-general architecture.
- Small composable skills, not one mega-skill.
- Deterministic outputs: explicit schemas, units, coordinate frames, and provenance.
- Reproducibility: script-backed operations and clear quality gates.
- Safe automation: read-only by default, explicit confirmation for destructive actions.

## Repository Layout
- `skills/`: installable skill packages.
- `docs/`: roadmap, conventions, and governance.
- `research/`: source research and background material.

Per-skill layout:
- `SKILL.md`: trigger conditions, workflow, constraints.
- `references/`: targeted domain guidance loaded on-demand.
- `scripts/`: executable helpers used by the skill.
- `assets/`: templates and style files.

## Planned Skill Collection

### Phase 1: Core analysis foundation
1. `roman-plotting` (first skill)
- Generate publication-quality figures for Roman and microlensing workflows.
- Enforce style conventions, panel structure, metadata, and export standards.

2. `roman-timeseries-qc`
- Validate time-series columns, cadence gaps, error model sanity, and outliers.
- Emit machine-readable QC report before fitting/plotting.

3. `roman-event-summary`
- Produce standardized event summary tables with units and uncertainties.
- Include provenance and reproducible source query references.

### Phase 2: Microlensing modeling support
4. `roman-microlensing-model-compare`
- Compare 1L1S vs 2L1S (and optional parallax/finite-source variants).
- Output fit diagnostics and model-selection summary.

5. `roman-caustic-visualization`
- Plot caustics, source trajectories, and annotated anomaly epochs.

6. `roman-posterior-diagnostics`
- Generate corner plots, trace diagnostics, and parameter covariance summaries.

### Phase 3: Physical inference and publication prep
7. `roman-physical-inference`
- Build mass-distance and related physical-parameter visualizations.

8. `roman-paper-figures`
- Convert analysis outputs into journal-ready figure packages and manifests.

## Cross-Skill Contracts
Every skill should return:
- `status`: `ok | warning | error`
- `summary`: short human-readable result
- `artifacts`: produced files (paths + format)
- `provenance`: input dataset identifiers, source paths, timestamp
- `validation`: key checks performed and pass/fail outcomes

## First Milestone (Now)
- Scaffold repository architecture.
- Implement `roman-plotting` skill package with microlensing-first playbook.
- Add reusable plotting script entrypoint and style template.
