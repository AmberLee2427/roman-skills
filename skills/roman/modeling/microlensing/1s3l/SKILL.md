---
name: "roman-modeling-microlensing-1s3l"
description: "Microlensing modeling rung: 1S3L with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: 1S3L

## Purpose
Final escalation for persistent structured residuals or known triple-lens degeneracy.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- Inherit 1S2L priors
- Third-body mass ratio: strongly regularized log-uniform
- Third-body separation: broad log-uniform
- Orientation terms: uniform angular priors

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
