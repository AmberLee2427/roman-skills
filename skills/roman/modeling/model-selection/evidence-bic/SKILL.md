---
name: "roman-modeling-model-selection-evidence-bic"
description: "Compute BIC evidence deltas between baseline and candidate models and emit a keep-complexity decision for model-selection workflows."
---

# Roman Modeling Model Selection: Evidence BIC Skill

## Purpose
Provide a deterministic BIC-based decision gate for whether additional model complexity is justified.

## Use This Skill When
- Comparing a baseline model against one or more more-complex alternatives.
- You need an explicit, machine-readable keep/reject complexity decision.
- You want consistent evidence thresholds across workflows.

## Inputs To Confirm
- Input CSV path with per-model chi-square and parameter count.
- Common sample size (`n_points`) used for BIC.
- Candidate and baseline model identifiers.
- Delta-BIC threshold for keeping complexity.
- Output JSON path.

## Workflow
1. Parse model metrics and compute BIC for each model.
2. Compute `delta_bic = bic_candidate - bic_baseline`.
3. Mark `keep_complexity=true` when delta passes threshold.
4. Emit decision report with ranked evidence summary.

## Output Contract
Return:
- `status`: `ok | warning | error`
- `summary`: short evidence verdict
- `artifacts`: report path(s)
- `validation`: checks performed
- `provenance`: input path and timestamp

## References
- `references/evidence-thresholds.md`

## Scripts
- `scripts/evaluate_bic.py`
