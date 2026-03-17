---
name: "roman-microlensing-model-compare"
description: "Compare microlensing fit models (for example 1L1S vs 2L1S) on a shared Roman time-series dataset using deterministic metrics (chi-square, reduced chi-square, AIC, BIC), and return ranked model diagnostics with explicit evidence deltas."
---

# Roman Microlensing Model Compare Skill

## Purpose
Provide a reproducible model-comparison step for microlensing fits before interpretation and figure generation.

## Use This Skill When
- Competing fit outputs exist for one event.
- You need quantitative support for choosing a baseline model.
- Downstream reporting requires explicit model-ranking metrics.

## Inputs To Confirm
- Input CSV path with observed values and uncertainties.
- Observed value/uncertainty column names.
- Model specifications (`name:model_column:n_params`).
- Output JSON path.

## Workflow
1. Validate required observed columns and each model column.
2. Compute residuals and weighted chi-square per model.
3. Compute reduced chi-square, AIC, and BIC using provided parameter counts.
4. Rank models by BIC (primary), report deltas vs best model.
5. Emit structured comparison result with caveats.

## Output Contract
Return:
- `status`: `ok | warning | error`
- `summary`: preferred model and key deltas
- `artifacts`: comparison JSON path
- `validation`: parse and finite-value checks
- `provenance`: input path and timestamp

## Constraints
- Use identical data rows across all compared models.
- Do not claim physical interpretation from metric differences alone.
- If model columns are missing, return `error` and stop.

## References
- `references/metrics.md`
- `references/interpretation.md`

## Scripts
- `scripts/compare_models.py`
