#!/usr/bin/env python3
"""Run QC checks for Roman time-series CSV data."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing dependencies. Install with: pip install numpy pandas"
    ) from exc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Roman time-series QC")
    p.add_argument("--input", required=True, help="Input CSV path")
    p.add_argument("--time-col", default="time")
    p.add_argument("--value-col", required=True)
    p.add_argument("--err-col", required=True)
    p.add_argument("--obs-col", default="observatory")
    p.add_argument("--output", required=True, help="Output JSON path")
    p.add_argument("--large-gap-multiplier", type=float, default=5.0)
    p.add_argument("--robust-z-outlier", type=float, default=5.0)
    return p.parse_args()


def robust_z(values: np.ndarray) -> np.ndarray:
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    if mad == 0:
        return np.zeros_like(values)
    return 0.6745 * (values - med) / mad


def main() -> None:
    args = parse_args()
    out = Path(args.output)
    df = pd.read_csv(args.input)

    required = [args.time_col, args.value_col, args.err_col]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        report = {
            "status": "error",
            "summary": f"Missing required columns: {', '.join(missing_cols)}",
            "artifacts": [str(Path(args.output).resolve())],
            "validation": {"required_columns": False},
            "provenance": {
                "input": str(Path(args.input).resolve()),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    n_rows = len(df)
    missing_fraction = {
        col: float(df[col].isna().mean()) for col in required
    }

    numeric = df[required].apply(pd.to_numeric, errors="coerce")
    non_finite = {
        col: int((~np.isfinite(numeric[col])).sum()) for col in required
    }

    time_vals = numeric[args.time_col].to_numpy()
    value_vals = numeric[args.value_col].to_numpy()
    err_vals = numeric[args.err_col].to_numpy()

    finite_mask = np.isfinite(time_vals) & np.isfinite(value_vals) & np.isfinite(err_vals)
    valid = numeric.loc[finite_mask].copy()

    sorted_time = np.sort(valid[args.time_col].to_numpy())
    diffs = np.diff(sorted_time) if len(sorted_time) > 1 else np.array([])

    cadence = {
        "median": float(np.median(diffs)) if diffs.size else None,
        "p05": float(np.percentile(diffs, 5)) if diffs.size else None,
        "p95": float(np.percentile(diffs, 95)) if diffs.size else None,
    }

    large_gap_threshold = None
    large_gap_count = 0
    if diffs.size:
        med = np.median(diffs)
        large_gap_threshold = float(args.large_gap_multiplier * med)
        large_gap_count = int((diffs > large_gap_threshold).sum())

    duplicate_timestamps = int(valid[args.time_col].duplicated().sum())
    non_positive_err = int((valid[args.err_col] <= 0).sum())

    rz = robust_z(valid[args.value_col].to_numpy()) if len(valid) else np.array([])
    outlier_count = int((np.abs(rz) > args.robust_z_outlier).sum())

    by_observatory = {}
    if args.obs_col in df.columns and len(valid):
        working = valid.copy()
        working[args.obs_col] = df.loc[finite_mask, args.obs_col].fillna("UNKNOWN").astype(str)
        for obs, sub in working.groupby(args.obs_col):
            z = robust_z(sub[args.value_col].to_numpy())
            by_observatory[obs] = {
                "rows": int(len(sub)),
                "outliers": int((np.abs(z) > args.robust_z_outlier).sum()),
            }

    checks = {
        "required_columns": len(missing_cols) == 0,
        "has_rows": n_rows > 0,
        "finite_numeric_required": all(v == 0 for v in non_finite.values()),
        "positive_uncertainties": non_positive_err == 0,
    }

    status = "ok"
    warnings = []
    if not checks["has_rows"]:
        status = "error"
        warnings.append("No rows found")
    if not checks["finite_numeric_required"]:
        status = "warning"
        warnings.append("Non-finite numeric values found")
    if not checks["positive_uncertainties"]:
        status = "warning"
        warnings.append("Non-positive uncertainties found")
    if large_gap_count > 0:
        status = "warning"
        warnings.append("Large cadence gaps detected")
    if outlier_count > 0:
        status = "warning"
        warnings.append("Outliers detected")

    summary = "QC checks passed" if status == "ok" else "; ".join(warnings)

    report = {
        "status": status,
        "summary": summary,
        "artifacts": [str(out.resolve())],
        "validation": checks,
        "metrics": {
            "rows": int(n_rows),
            "missing_fraction": missing_fraction,
            "non_finite_counts": non_finite,
            "duplicate_timestamps": duplicate_timestamps,
            "cadence": cadence,
            "large_gap_threshold": large_gap_threshold,
            "large_gap_count": large_gap_count,
            "non_positive_uncertainty_count": non_positive_err,
            "outlier_count": outlier_count,
            "outlier_threshold": args.robust_z_outlier,
            "by_observatory": by_observatory,
        },
        "provenance": {
            "input": str(Path(args.input).resolve()),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved QC report: {out}")


if __name__ == "__main__":
    main()
