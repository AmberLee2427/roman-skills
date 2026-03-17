# Roman Skills Repository Roadmap

## Mission
Build a focused, reusable skill library that helps coding agents perform reliable, publication-grade analysis on Nancy Grace Roman Space Telescope data.

## Design Principles
- Domain-first hierarchy, science-case-specific leaves.
- Small composable skills, not one mega-skill.
- Deterministic outputs: explicit schemas, units, coordinate frames, and provenance.
- Reproducibility: script-backed operations and clear quality gates.
- Agent-platform-neutral automation: no vendor-locked hook layout.

## Repository Layout
- `skills/`: installable skill packages.
- `docs/`: roadmap, conventions, and governance.
- `research/`: source research and background material.
- `automation/`: generic hook templates and gate runners.

Per-skill layout:
- `SKILL.md`: trigger conditions, workflow, constraints.
- `references/`: targeted domain guidance loaded on-demand.
- `scripts/`: executable helpers used by the skill.
- `assets/`: templates and style files.

## Skill Hierarchy

### `qc/`
1. `qc/timeseries`
- Validate time-series columns, cadence gaps, uncertainty sanity, and outliers.

### `photometry/`
2. `photometry/aperture` (scaffold)
- Aperture-photometry extraction and table generation branch.

3. `photometry/difference-imaging` (scaffold)
- Difference-imaging photometry branch for variable/transient extraction.

### `modeling/`
4. `modeling/summary-statistics/event-summary`
- Standardized event summary metrics and provenance.

5. `modeling/summary-statistics/convergence-tests`
- Convergence diagnostics from chain outputs (`R-hat`, ESS proxy, threshold flags).

6. `modeling/model-compare/microlensing`
- Deterministic model ranking (chi-square, reduced chi-square, AIC, BIC).
- Microlensing implemented first as a branch, not the top-level taxonomy.

### `plotting/`
7. `plotting/plot-types/lightcurve-residuals`
- Lightcurve plus residual panel figure generation and export.

8. `plotting/style-profiles`
- Journal-oriented style profile checks (`apj`, `mnras`, `aanda`).

9. `plotting/accessibility-checks`
- Color/marker/grayscale distinguishability checks for figures.

## Prioritization
Implementation order can still be microlensing-first, but taxonomy remains domain-first.

Current implementation priority:
1. `qc/timeseries`
2. `modeling/model-compare/microlensing`
3. `plotting/plot-types/lightcurve-residuals`
4. `plotting/style-profiles`
5. `plotting/accessibility-checks`

## Cross-Skill Contracts
Every skill should return:
- `status`: `ok | warning | error`
- `summary`: short human-readable result
- `artifacts`: produced files (paths + format)
- `provenance`: input dataset identifiers, source paths, timestamp
- `validation`: key checks performed and pass/fail outcomes

## Automation and Hooks
Hook orchestration is intentionally platform-neutral:
- Hook templates live in `automation/hooks/`.
- Quality gates live in `automation/gates/`.
- Agents can map local runner events (for example `post-plot`) to these scripts.

## Current Milestone
- Refactor from flat skill list to hierarchical domain structure.
- Keep microlensing as the first implemented modeling branch.
- Add generic plotting quality gates for style and accessibility.
