---
name: "roman-modeling-summary-statistics-convergence-tests"
description: "Compute deterministic MCMC convergence diagnostics (R-hat and effective-sample-size proxy) from chain tables and emit machine-readable pass/warn/fail summaries."
---

# Roman Modeling Summary Statistics: Convergence Tests Skill

## Purpose
Add convergence diagnostics to the summary-statistics branch so model outputs can be quality-gated before interpretation.

## Use This Skill When
- You have posterior samples from multiple chains.
- You need convergence evidence in reports/manuscripts.
- Downstream ranking or plotting should consume convergence flags.

## Inputs To Confirm
- Input CSV path with per-draw samples.
- Chain identifier column.
- Parameter columns to evaluate.
- Optional R-hat threshold and ESS threshold.
- Output JSON path.

## Workflow
1. Validate presence of chain and parameter columns.
2. Compute per-parameter split-chain diagnostics by aligned draw count.
3. Emit R-hat and ESS proxy values with threshold-based flags.
4. Return machine-readable validation status and provenance.

## Output Contract
Return:
- `status`: `ok | warning | error`
- `summary`: short convergence verdict
- `artifacts`: report path(s)
- `validation`: per-parameter checks
- `provenance`: input path and timestamp

## Constraints
- Requires at least two non-empty chains.
- Uses aligned minimum chain length across chains.
- Reports proxy ESS estimate explicitly as proxy.

## References
- `references/diagnostics.md`

## Scripts
- `scripts/check_convergence.py`
