---
name: "roman-modeling-microlensing-parallax"
description: "Microlensing modeling rung: PARALLAX with escalation guidance, evidence-gate checkpoints, and default priors."
---

# Roman Modeling Microlensing: PARALLAX

## Purpose
Escalate when long-timescale asymmetry suggests annual parallax.

## Use This Skill When
- Current lower-complexity rung leaves structured residual anomalies.
- Known degeneracies indicate this rung should be tested.

## Escalation Gate
- Run this rung only after the previous rung fails anomaly or degeneracy checks.
- Keep added complexity only if evidence improves enough (use skills/modeling/model-selection/evidence-bic).

## Default Priors
- Inherit FSPL/PSPL priors
- piE_N, piE_E: zero-centered broad normal priors
- Weak regularization against unphysically large parallax amplitudes

## Output Contract
Return:
- status: ok | warning | error
- summary: fit/evidence verdict
- artifacts: fit products and diagnostics
- validation: convergence and residual checks
- provenance: data paths, seed/config, timestamp
