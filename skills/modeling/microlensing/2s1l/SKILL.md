---
name: "roman-modeling-microlensing-2s1l"
description: "Microlensing modeling rung: 2S1L with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: 2S1L

## Purpose
Escalate for binary-source signatures with single lens.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- Inherit baseline priors
- q: log-uniform over plausible companion range
- s: log-uniform around close/resonant/wide regimes
- alpha: uniform in [0, 2pi]

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
