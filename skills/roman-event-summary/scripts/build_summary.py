#!/usr/bin/env python3
"""Build a normalized Roman event summary JSON from CSV input."""

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
    p = argparse.ArgumentParser(description="Build Roman event summary")
    p.add_argument("--input", required=True, help="Input CSV path")
    p.add_argument("--output", required=True, help="Output JSON path")
    p.add_argument("--event-id", help="Optional event identifier")
    p.add_argument("--time-col", default="time")
    p.add_argument("--value-col", required=True)
    p.add_argument("--err-col", required=True)
    p.add_argument("--value-mode", choices=["flux", "magnitude"], required=True)
    p.add_argument("--time-unit", default="days")
    p.add_argument("--value-unit", default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)

    required = [args.time_col, args.value_col, args.err_col]
    missing = [c for c in required if c not in df.columns]

    event_id = args.event_id or Path(args.input).stem

    if missing:
        report = {
            "status": "error",
            "summary": f"Missing required columns: {', '.join(missing)}",
            "event": {"event_id": event_id, "value_mode": args.value_mode},
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

    numeric = df[required].apply(pd.to_numeric, errors="coerce")
    valid = numeric[np.isfinite(numeric[args.time_col]) & np.isfinite(numeric[args.value_col]) & np.isfinite(numeric[args.err_col])]

    if valid.empty:
        report = {
            "status": "error",
            "summary": "No valid numeric rows after parsing",
            "event": {"event_id": event_id, "value_mode": args.value_mode},
            "validation": {"required_columns": True, "has_valid_rows": False},
            "provenance": {
                "input": str(Path(args.input).resolve()),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    t = valid[args.time_col].to_numpy()
    y = valid[args.value_col].to_numpy()

    value_median = float(np.median(y))

    if args.value_mode == "flux":
        peak_idx = int(np.argmax(y))
        value_peak = float(y[peak_idx])
        amplitude_proxy = float(np.max(y) - value_median)
    else:
        peak_idx = int(np.argmin(y))
        value_peak = float(y[peak_idx])
        amplitude_proxy = float(value_median - np.min(y))

    duration_proxy_90 = float(np.percentile(t, 95) - np.percentile(t, 5))

    report = {
        "status": "ok",
        "summary": f"Event {event_id}: {len(valid)} valid points, peak at t={t[peak_idx]:.6g}",
        "event": {
            "event_id": event_id,
            "value_mode": args.value_mode,
            "units": {
                "time": args.time_unit,
                "value": args.value_unit,
            },
        },
        "metrics": {
            "n_points": int(len(valid)),
            "time_min": float(np.min(t)),
            "time_max": float(np.max(t)),
            "value_median": value_median,
            "value_peak": value_peak,
            "time_at_peak": float(t[peak_idx]),
            "value_amplitude_proxy": amplitude_proxy,
            "duration_proxy_90pct": duration_proxy_90,
        },
        "validation": {
            "required_columns": True,
            "has_valid_rows": True,
            "finite_required_values": True,
        },
        "provenance": {
            "input": str(Path(args.input).resolve()),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved event summary: {out}")


if __name__ == "__main__":
    main()
