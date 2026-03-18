#!/usr/bin/env python3
"""Evaluate model-complexity retention based on BIC deltas."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit("Missing dependency. Install with: pip install pandas") from exc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate BIC evidence for complexity retention")
    p.add_argument("--input", required=True, help="Input CSV with model metrics")
    p.add_argument("--name-col", default="model_name")
    p.add_argument("--chi2-col", default="chi2")
    p.add_argument("--nparams-col", default="n_params")
    p.add_argument("--npoints-col", default="n_points")
    p.add_argument("--baseline", required=True, help="Baseline model name")
    p.add_argument("--candidate", action="append", required=True, help="Candidate model name (repeat)")
    p.add_argument("--keep-threshold", type=float, default=-6.0, help="Keep complexity when delta_bic <= threshold")
    p.add_argument("--output", required=True)
    return p.parse_args()


def label(delta_bic: float) -> str:
    if delta_bic <= -10:
        return "very_strong_candidate"
    if delta_bic <= -6:
        return "strong_candidate"
    if delta_bic <= -2:
        return "positive_candidate"
    if delta_bic < 2:
        return "weak_or_inconclusive"
    return "baseline_preferred"


def main() -> None:
    args = parse_args()
    out = Path(args.output)

    df = pd.read_csv(args.input)
    required = [args.name_col, args.chi2_col, args.nparams_col, args.npoints_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        report = {
            "status": "error",
            "summary": f"Missing required columns: {', '.join(missing)}",
            "artifacts": [str(out.resolve())],
            "validation": {"required_columns": False},
            "provenance": {"input": str(Path(args.input).resolve()), "timestamp_utc": datetime.now(timezone.utc).isoformat()},
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    rows = []
    for _, r in df.iterrows():
        try:
            n = float(r[args.npoints_col])
            chi2 = float(r[args.chi2_col])
            k = float(r[args.nparams_col])
            bic = chi2 + k * math.log(n)
        except (TypeError, ValueError):
            continue
        rows.append({
            "name": str(r[args.name_col]),
            "chi2": chi2,
            "n_params": int(k),
            "n_points": int(n),
            "bic": bic,
        })

    by_name = {r["name"]: r for r in rows}
    if args.baseline not in by_name:
        report = {
            "status": "error",
            "summary": f"Baseline model not found: {args.baseline}",
            "artifacts": [str(out.resolve())],
            "validation": {"required_columns": True, "baseline_found": False},
            "provenance": {"input": str(Path(args.input).resolve()), "timestamp_utc": datetime.now(timezone.utc).isoformat()},
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    baseline = by_name[args.baseline]
    decisions = []
    warnings = []

    for name in args.candidate:
        if name not in by_name:
            warnings.append(f"Candidate model not found: {name}")
            continue
        candidate = by_name[name]
        delta = float(candidate["bic"] - baseline["bic"])
        keep = bool(delta <= args.keep_threshold)
        decisions.append(
            {
                "baseline": args.baseline,
                "candidate": name,
                "bic_baseline": baseline["bic"],
                "bic_candidate": candidate["bic"],
                "delta_bic": delta,
                "evidence_label": label(delta),
                "keep_complexity": keep,
                "keep_threshold": args.keep_threshold,
            }
        )

    status = "warning" if warnings else "ok"
    summary = "BIC evidence evaluated" if not warnings else "BIC evidence evaluated with warnings"

    report = {
        "status": status,
        "summary": summary,
        "artifacts": [str(out.resolve())],
        "baseline": baseline,
        "decisions": decisions,
        "warnings": warnings,
        "validation": {
            "required_columns": True,
            "baseline_found": True,
            "candidate_count": len(args.candidate),
            "evaluated_count": len(decisions),
        },
        "provenance": {
            "input": str(Path(args.input).resolve()),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved BIC evidence report: {out}")


if __name__ == "__main__":
    main()
