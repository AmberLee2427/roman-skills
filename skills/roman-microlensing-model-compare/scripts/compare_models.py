#!/usr/bin/env python3
"""Compare microlensing models on a shared time-series dataset."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing dependencies. Install with: pip install numpy pandas"
    ) from exc


@dataclass
class ModelSpec:
    name: str
    column: str
    n_params: int


def parse_model_spec(raw: str) -> ModelSpec:
    parts = raw.split(":")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid --model spec '{raw}'. Expected format name:column:n_params"
        )
    name, column, n_params_raw = parts
    if not name or not column:
        raise ValueError(f"Invalid --model spec '{raw}'. Empty name/column")
    try:
        n_params = int(n_params_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid n_params in --model spec '{raw}'") from exc
    if n_params < 0:
        raise ValueError(f"n_params must be >= 0 in --model spec '{raw}'")
    return ModelSpec(name=name, column=column, n_params=n_params)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare microlensing models")
    p.add_argument("--input", required=True, help="Input CSV path")
    p.add_argument("--value-col", required=True, help="Observed value column")
    p.add_argument("--err-col", required=True, help="Observed uncertainty column")
    p.add_argument(
        "--model",
        action="append",
        required=True,
        help="Model spec name:column:n_params (repeat for multiple models)",
    )
    p.add_argument("--output", required=True, help="Output JSON path")
    return p.parse_args()


def evidence_label(delta_bic: float) -> str:
    if delta_bic < 2:
        return "weak"
    if delta_bic < 6:
        return "positive"
    if delta_bic < 10:
        return "strong"
    return "very_strong"


def main() -> None:
    args = parse_args()
    model_specs = [parse_model_spec(raw) for raw in args.model]

    if len(model_specs) < 2:
        raise SystemExit("Provide at least two --model specifications")

    df = pd.read_csv(args.input)
    required_cols = [args.value_col, args.err_col] + [m.column for m in model_specs]
    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        report = {
            "status": "error",
            "summary": f"Missing required columns: {', '.join(missing_cols)}",
            "validation": {"required_columns": False},
            "provenance": {
                "input": str(Path(args.input).resolve()),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    numeric = df[required_cols].apply(pd.to_numeric, errors="coerce")

    finite_mask = np.isfinite(numeric[args.value_col]) & np.isfinite(numeric[args.err_col])
    for m in model_specs:
        finite_mask &= np.isfinite(numeric[m.column])

    valid = numeric.loc[finite_mask].copy()
    valid = valid[valid[args.err_col] > 0]

    if valid.empty:
        raise SystemExit("No valid rows after finite-value and uncertainty filtering")

    n = len(valid)
    y = valid[args.value_col].to_numpy()
    sigma = valid[args.err_col].to_numpy()

    rows = []
    warnings = []
    for m in model_specs:
        pred = valid[m.column].to_numpy()
        resid = y - pred
        chi2 = float(np.sum((resid / sigma) ** 2))
        dof = n - m.n_params
        if dof <= 0:
            warnings.append(
                f"Model {m.name} has non-positive dof ({dof}); chi2_reduced is undefined"
            )
        chi2_red = float(chi2 / dof) if dof > 0 else None
        aic = float(chi2 + 2 * m.n_params)
        bic = float(chi2 + m.n_params * math.log(n))
        rows.append(
            {
                "name": m.name,
                "model_column": m.column,
                "n_params": int(m.n_params),
                "n_points": int(n),
                "dof": int(dof),
                "chi2": chi2,
                "chi2_reduced": chi2_red,
                "aic": aic,
                "bic": bic,
                "rmse": float(np.sqrt(np.mean(resid**2))),
            }
        )

    rows.sort(key=lambda r: r["bic"])
    best_bic = rows[0]["bic"]
    best_name = rows[0]["name"]

    for r in rows:
        delta = float(r["bic"] - best_bic)
        r["delta_bic"] = delta
        r["bic_evidence_vs_best"] = evidence_label(delta)

    summary = (
        f"Preferred model by BIC: {best_name}; "
        f"next-best delta_bic={rows[1]['delta_bic']:.3g}"
    )

    status = "warning" if warnings else "ok"

    report = {
        "status": status,
        "summary": summary if not warnings else f"{summary}; " + "; ".join(warnings),
        "preferred_model": best_name,
        "ranking_metric": "bic",
        "models": rows,
        "warnings": warnings,
        "validation": {
            "required_columns": True,
            "finite_required_values": True,
            "positive_uncertainties": True,
            "common_row_count": int(n),
        },
        "provenance": {
            "input": str(Path(args.input).resolve()),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model_specs": [
                {"name": m.name, "column": m.column, "n_params": m.n_params}
                for m in model_specs
            ],
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved model comparison: {out}")


if __name__ == "__main__":
    main()
