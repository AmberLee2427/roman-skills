# Metrics

Given observations `y_i`, model `m_i`, and uncertainty `sigma_i`:

- Residual: `r_i = y_i - m_i`
- Chi-square: `chi2 = sum((r_i / sigma_i)^2)`
- Reduced chi-square: `chi2_red = chi2 / (N - k)`
  - `N`: number of valid rows
  - `k`: number of free model parameters
- AIC: `chi2 + 2k`
- BIC: `chi2 + k * ln(N)`

Primary ranking in this skill uses minimum BIC.
