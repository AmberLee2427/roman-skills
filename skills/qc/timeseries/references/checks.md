# QC Checks

## Required
- Required columns present.
- Numeric columns parse successfully.
- No non-finite values in required numeric columns.
- Uncertainties are positive and finite.

## Temporal
- Time values are sortable and finite.
- Duplicate timestamps count reported.
- Cadence statistics computed (median, p05, p95).
- Large cadence gaps reported.

## Statistical
- Robust center/scale estimated using median and MAD.
- Outliers flagged for |z_robust| > threshold.
- Outlier counts reported globally and by observatory (if provided).
