---
name: "roman-modeling-microlensing-lom"
description: "Microlensing modeling rung: LOM with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: LOM

## Purpose
Escalate for evolving-caustic or trajectory-drift residuals.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- Inherit parent-model priors
- ds/dt, dalpha/dt: zero-centered normal priors
- Constrain rates to physically plausible ranges for event timescale

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
