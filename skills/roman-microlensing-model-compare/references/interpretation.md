# Interpretation Guidance

- Prefer model with smallest BIC.
- Report `delta_bic = BIC_model - BIC_best`.
- Heuristic evidence scale:
  - `delta_bic < 2`: weak
  - `2 <= delta_bic < 6`: positive
  - `6 <= delta_bic < 10`: strong
  - `>= 10`: very strong

Caution:
- These are model-selection diagnostics, not direct physical proof.
- Always cross-check with residual structure and domain plausibility.
