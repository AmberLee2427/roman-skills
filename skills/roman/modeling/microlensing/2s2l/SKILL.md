---
name: "roman-modeling-microlensing-2s2l"
description: "Microlensing modeling rung: 2S2L with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: 2S2L

## Purpose
Escalate only when dual-complexity structure remains required.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- Inherit 1S2L and 2S1L priors
- Additional source/lens coupling terms with weakly informative priors
- Strong regularization to avoid unconstrained multimodal blow-up

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
