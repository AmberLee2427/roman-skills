#!/usr/bin/env python3
"""Compute basic convergence diagnostics from MCMC chain CSV data."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:
    raise SystemExit("Missing dependencies. Install with: pip install numpy pandas") from exc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check chain convergence diagnostics")
    p.add_argument("--input", required=True, help="Input CSV path")
    p.add_argument("--chain-col", default="chain", help="Chain id column")
    p.add_argument(
        "--param-col",
        action="append",
        required=True,
        help="Parameter column to evaluate (repeat flag)",
    )
    p.add_argument("--rhat-threshold", type=float, default=1.01)
    p.add_argument("--ess-threshold", type=float, default=400.0)
    p.add_argument("--output", required=True, help="Output JSON path")
    return p.parse_args()


def compute_rhat_and_ess_proxy(chain_arrays: list[np.ndarray]) -> tuple[float, float, int, int]:
    m = len(chain_arrays)
    n = min(len(a) for a in chain_arrays)
    aligned = [a[:n] for a in chain_arrays]

    means = np.array([float(np.mean(a)) for a in aligned])
    variances = np.array([float(np.var(a, ddof=1)) for a in aligned])

    w = float(np.mean(variances))
    b = float(n * np.var(means, ddof=1))

    if w <= 0:
        rhat = 1.0 if b == 0 else float("inf")
    else:
        var_hat = ((n - 1) / n) * w + (b / n)
        rhat = float(math.sqrt(var_hat / w))
        if np.isfinite(rhat):
            rhat = max(1.0, rhat)

    total_draws = int(m * n)
    ess_proxy = float(total_draws / (rhat * rhat)) if np.isfinite(rhat) and rhat > 0 else 0.0
    return rhat, ess_proxy, m, n


def main() -> None:
    args = parse_args()
    out = Path(args.output)

    df = pd.read_csv(args.input)
    required = [args.chain_col] + args.param_col
    missing = [c for c in required if c not in df.columns]

    if missing:
        report = {
            "status": "error",
            "summary": f"Missing required columns: {', '.join(missing)}",
            "artifacts": [str(out.resolve())],
            "validation": {"required_columns": False},
            "provenance": {
                "input": str(Path(args.input).resolve()),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    chain_ids = df[args.chain_col].dropna().unique().tolist()
    if len(chain_ids) < 2:
        report = {
            "status": "error",
            "summary": "Need at least two chains for convergence diagnostics",
            "artifacts": [str(out.resolve())],
            "validation": {"required_columns": True, "enough_chains": False},
            "provenance": {
                "input": str(Path(args.input).resolve()),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    by_param = {}
    warnings = []

    for param in args.param_col:
        numeric = pd.to_numeric(df[param], errors="coerce")
        working = pd.DataFrame({args.chain_col: df[args.chain_col], param: numeric}).dropna()

        chain_arrays = []
        for chain_id, sub in working.groupby(args.chain_col):
            vals = sub[param].to_numpy()
            if len(vals) > 1:
                chain_arrays.append(vals)

        if len(chain_arrays) < 2:
            by_param[param] = {
                "status": "error",
                "summary": "Insufficient valid chain samples",
            }
            warnings.append(f"{param}: insufficient valid chain samples")
            continue

        rhat, ess_proxy, m, n = compute_rhat_and_ess_proxy(chain_arrays)
        rhat_ok = bool(np.isfinite(rhat) and rhat <= args.rhat_threshold)
        ess_ok = bool(ess_proxy >= args.ess_threshold)

        if not rhat_ok:
            warnings.append(f"{param}: rhat={rhat:.5g} exceeds threshold {args.rhat_threshold}")
        if not ess_ok:
            warnings.append(f"{param}: ess_proxy={ess_proxy:.5g} below threshold {args.ess_threshold}")

        by_param[param] = {
            "status": "ok" if (rhat_ok and ess_ok) else "warning",
            "rhat": rhat,
            "rhat_threshold": args.rhat_threshold,
            "rhat_pass": rhat_ok,
            "ess_proxy": ess_proxy,
            "ess_threshold": args.ess_threshold,
            "ess_pass": ess_ok,
            "n_chains": m,
            "aligned_draws_per_chain": n,
            "total_aligned_draws": int(m * n),
        }

    status = "ok" if not warnings else "warning"
    summary = "Convergence checks passed" if status == "ok" else "; ".join(warnings)

    report = {
        "status": status,
        "summary": summary,
        "artifacts": [str(out.resolve())],
        "validation": {
            "required_columns": True,
            "enough_chains": True,
            "all_parameters_evaluated": all(v.get("status") != "error" for v in by_param.values()),
        },
        "metrics": {"parameters": by_param},
        "warnings": warnings,
        "provenance": {
            "input": str(Path(args.input).resolve()),
            "chain_col": args.chain_col,
            "param_cols": args.param_col,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved convergence report: {out}")


if __name__ == "__main__":
    main()
