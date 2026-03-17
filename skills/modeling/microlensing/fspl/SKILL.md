---
name: "roman-modeling-microlensing-fspl"
description: "Microlensing modeling rung: FSPL with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: FSPL

## Purpose
Escalate when peak morphology suggests finite-source effects.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- Inherit PSPL priors
- rho: log-uniform over finite-source-sensitive range
- Narrower u0 prior when finite-source morphology is present

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
