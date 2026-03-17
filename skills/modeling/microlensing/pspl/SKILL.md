---
name: "roman-modeling-microlensing-pspl"
description: "Microlensing modeling rung: PSPL with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: PSPL

## Purpose
First-line baseline model for single-lens/single-source events.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- t0: uniform around detected event window
- u0: uniform in [0, 1.5]
- tE: log-uniform over cadence-supported range
- fs (source flux): broad positive prior
- fb (blend flux): broad prior with optional weak negative tail only when instrument model allows it

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
