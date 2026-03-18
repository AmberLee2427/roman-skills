# BIC Evidence Thresholds

Lower BIC is preferred.

Define:
- `delta_bic = bic_candidate - bic_baseline`

Interpretation guide:
- `delta_bic <= -10`: very strong support for candidate complexity.
- `-10 < delta_bic <= -6`: strong support.
- `-6 < delta_bic <= -2`: positive support.
- `-2 < delta_bic < 2`: weak/inconclusive.
- `delta_bic >= 2`: baseline preferred.

Suggested default keep-complexity threshold:
- `delta_bic <= -6`.
