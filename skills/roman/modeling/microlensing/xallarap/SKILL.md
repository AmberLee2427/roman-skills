---
name: "roman-modeling-microlensing-xallarap"
description: "Microlensing modeling rung: XALLARAP with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: XALLARAP

## Purpose
Escalate for source-orbital signatures that can mimic parallax.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- Inherit parent-model priors
- Orbital period: log-uniform over cadence-supported range
- Phase: uniform in [0, 2pi]
- Inclination: isotropic prior (cos i uniform)
- Amplitude terms: zero-centered broad priors

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
