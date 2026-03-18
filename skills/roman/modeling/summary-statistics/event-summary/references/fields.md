# Field Guidance

- `event_id`: user-provided or derived from input filename stem.
- `value_peak`:
  - for `flux`: max(value)
  - for `magnitude`: min(value)
- `value_amplitude_proxy`:
  - for `flux`: max(value) - median(value)
  - for `magnitude`: median(value) - min(value)
- `duration_proxy_90pct`: `p95(time) - p05(time)` on valid rows.

These are descriptive statistics, not full model-fit parameters.
