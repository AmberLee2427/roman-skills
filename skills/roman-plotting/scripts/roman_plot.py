#!/usr/bin/env python3
"""Minimal Roman plotting utility for microlensing-first workflows.

Usage example:
  python skills/roman-plotting/scripts/roman_plot.py \\
    --input data/lightcurve.csv \\
    --output out/event123_lightcurve \\
    --x-col time --y-col magnitude --err-col magnitude_err \\
    --model-col model_magnitude --mode magnitude
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

try:
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing dependencies. Install with: pip install matplotlib pandas"
    ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Roman analysis plot")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output file stem (no extension)")
    parser.add_argument("--x-col", required=True, help="X-axis column name")
    parser.add_argument("--y-col", required=True, help="Y-axis column name")
    parser.add_argument("--err-col", help="Error column name")
    parser.add_argument("--model-col", help="Model column name for residual panel")
    parser.add_argument(
        "--mode",
        choices=["flux", "magnitude"],
        default="flux",
        help="Interpretation of y-axis values",
    )
    parser.add_argument(
        "--x-label",
        default="Time",
        help="X-axis label (include explicit offset if used)",
    )
    parser.add_argument("--y-label", default="Value", help="Y-axis label")
    parser.add_argument("--title", default="Roman Plot", help="Figure title")
    parser.add_argument(
        "--tex",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable LaTeX text rendering (default: on). Use --no-tex to disable.",
    )
    return parser.parse_args()


def check_tex_dependencies() -> None:
    if shutil.which("latex") is None:
        raise SystemExit(
            "LaTeX binary not found. Install TeX or run with --no-tex."
        )
    if shutil.which("dvipng") is None:
        raise SystemExit(
            "dvipng not found. Install dvipng for TeX-rendered PNG output or run with --no-tex."
        )
    if shutil.which("kpsewhich") is None:
        raise SystemExit(
            "kpsewhich not found. Install TeX tooling or run with --no-tex."
        )

    probe = subprocess.run(
        ["kpsewhich", "type1ec.sty"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0 or not probe.stdout.strip():
        raise SystemExit(
            "Missing TeX font package (type1ec.sty). Install TeX font extras or run with --no-tex."
        )


def main() -> None:
    args = parse_args()
    if args.tex:
        check_tex_dependencies()
        plt.rcParams["text.usetex"] = True
        plt.rcParams["font.family"] = "serif"
    df = pd.read_csv(args.input)

    for col in [args.x_col, args.y_col]:
        if col not in df.columns:
            raise SystemExit(f"Missing required column: {col}")

    has_model = bool(args.model_col and args.model_col in df.columns)
    if args.model_col and not has_model:
        raise SystemExit(f"Model column not found: {args.model_col}")

    if has_model:
        fig, (ax, ax_resid) = plt.subplots(
            2,
            1,
            figsize=(9, 6),
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]},
        )
    else:
        fig, ax = plt.subplots(figsize=(9, 5))
        ax_resid = None

    x = df[args.x_col]
    y = df[args.y_col]

    if args.err_col and args.err_col in df.columns:
        ax.errorbar(x, y, yerr=df[args.err_col], fmt="o", ms=3, alpha=0.8, label="Data")
    else:
        ax.plot(x, y, "o", ms=3, alpha=0.8, label="Data")

    if has_model:
        model_y = df[args.model_col]
        ax.plot(x, model_y, "-", lw=1.6, label="Model")
        residuals = y - model_y
        ax_resid.axhline(0.0, color="black", lw=1.0, alpha=0.7)
        ax_resid.plot(x, residuals, "o", ms=2.5, alpha=0.8)
        ax_resid.set_ylabel("Residual")

    ax.set_title(args.title)
    ax.set_xlabel(args.x_label if not has_model else "")
    ax.set_ylabel(args.y_label)

    # Standard astronomy convention for magnitude-based plots.
    if args.mode == "magnitude":
        ax.invert_yaxis()

    ax.legend(loc="best", fontsize=9)

    if has_model:
        ax_resid.set_xlabel(args.x_label)

    fig.tight_layout()

    output_stem = Path(args.output)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(f"{output_stem}.pdf")
    fig.savefig(f"{output_stem}.png", dpi=300)
    print(f"Saved: {output_stem}.pdf")
    print(f"Saved: {output_stem}.png")


if __name__ == "__main__":
    main()
