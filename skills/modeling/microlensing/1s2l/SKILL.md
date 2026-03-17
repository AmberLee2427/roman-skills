---
name: "roman-modeling-microlensing-1s2l"
description: "Microlensing modeling rung: 1S2L with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: 1S2L

## Purpose
Escalate for binary-lens anomalies.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- Inherit baseline priors
- q: log-uniform over binary-lens mass ratios
- s: log-uniform spanning close/resonant/wide
- alpha: uniform in [0, 2pi]
- Optional caustic-crossing timing priors from anomaly window

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
