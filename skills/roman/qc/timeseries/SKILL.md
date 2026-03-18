---
name: "roman-qc-timeseries"
description: "Validate Roman time-series data before modeling or plotting. Use when checking required columns, missing data, cadence gaps, uncertainty sanity, outliers, and per-observatory consistency."
---

# Roman Time-Series QC Skill

## Purpose
Run deterministic quality-control checks on time-series inputs used for Roman microlensing analysis.

## Use This Skill When
- A dataset is newly ingested and not yet validated.
- Plotting or fitting fails and data integrity is suspected.
- You need a machine-readable QC report before downstream analysis.

## Inputs To Confirm
- Input table path (CSV).
- Required columns (`time`, value column, uncertainty column; optional observatory column).
- Value mode (`flux` or `magnitude`).
- Expected cadence range (optional).

## Workflow
1. Load CSV and verify required columns exist.
2. Validate missingness and finite numeric values.
3. Check time monotonicity and duplicate timestamps.
4. Estimate cadence and flag large gaps.
5. Validate uncertainties (`> 0`, finite).
6. Flag high-sigma outliers using robust statistics (MAD-based).
7. Emit JSON QC report and concise pass/warn/fail summary.

## Output Contract
Return:
- `status`: `ok | warning | error`
- `summary`: short QC verdict
- `artifacts`: report path(s)
- `validation`: individual checks with pass/fail counts
- `provenance`: input path and timestamp

## Constraints
- No row deletion or imputation by default.
- If critical columns are missing, stop with `error`.
- Keep threshold values explicit in output.

## References
- `references/checks.md`
- `references/thresholds.md`

## Scripts
- `scripts/run_qc.py`
