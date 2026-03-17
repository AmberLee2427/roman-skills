#!/usr/bin/env python3
"""Minimal Roman plotting utility for microlensing-first workflows.

Usage example:
  python skills/plotting/plot-types/lightcurve-residuals/scripts/roman_plot.py \\
    --input data/lightcurve.csv \\
    --output out/event123_lightcurve \\
    --x-col time --y-col magnitude --err-col magnitude_err \\
    --model-x-col model_time \\
    --model-col model_magnitude --mode magnitude \\
    --posterior-model-col sample_model_001 --posterior-model-col sample_model_002
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

try:
    import matplotlib.pyplot as plt
    from matplotlib import transforms
    import numpy as np
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing dependencies. Install with: pip install matplotlib numpy pandas"
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
        "--residual-col",
        help="Optional residual column (required when model x-values do not match data x-values)",
    )
    parser.add_argument(
        "--model-x-col",
        help="Optional X-axis column for model/posterior/initial model curves",
    )
    parser.add_argument(
        "--model-color",
        default="#e69f00",
        help="Line color for best-fit model overlay",
    )
    parser.add_argument(
        "--initial-model-col",
        help="Optional initial/pre-optimization model column to overlay",
    )
    parser.add_argument(
        "--initial-model-style",
        default="--",
        help="Line style for initial model overlay",
    )
    parser.add_argument(
        "--initial-model-color",
        default="#000000",
        help="Line color for initial model overlay",
    )
    parser.add_argument(
        "--posterior-model-col",
        action="append",
        default=[],
        help="Posterior sample model column to overlay (repeat for multiple columns)",
    )
    parser.add_argument(
        "--posterior-alpha",
        type=float,
        default=0.5,
        help="Alpha for posterior sample overlays",
    )
    parser.add_argument(
        "--posterior-linewidth",
        type=float,
        default=1.4,
        help="Line width for posterior sample overlays",
    )
    parser.add_argument(
        "--posterior-style",
        default="-",
        help="Line style for posterior sample overlays",
    )
    parser.add_argument(
        "--posterior-color",
        default="#3a3a3a",
        help="Line color for posterior sample overlays",
    )
    parser.add_argument(
        "--mode",
        choices=["flux", "magnitude"],
        default="flux",
        help="Interpretation of y-axis values",
    )
    parser.add_argument(
        "--x-label",
        help="Explicit X-axis label override (disables auto x-label building)",
    )
    parser.add_argument(
        "--x-var",
        default="Time",
        help="X-axis variable name used for auto label (e.g., HJD)",
    )
    parser.add_argument(
        "--x-unit",
        default="",
        help="X-axis unit used for auto label (e.g., days)",
    )
    parser.add_argument(
        "--x-offset",
        type=float,
        help="Explicit x-offset to subtract before plotting (e.g., 2460000)",
    )
    parser.add_argument(
        "--x-offset-mod",
        type=float,
        default=10000.0,
        help="Auto-offset modulus for large dates (default: 10000)",
    )
    parser.add_argument("--y-label", default="Value", help="Y-axis label")
    parser.add_argument("--title", default="Roman Plot", help="Figure title")
    parser.add_argument(
        "--vline",
        action="append",
        default=[],
        help=(
            "Vertical annotation (repeatable). Format: "
            "'x,label' or 'x,label,color,linestyle'"
        ),
    )
    parser.add_argument(
        "--manifest-output",
        help="Optional JSON manifest path. Default: <output>.meta.json",
    )
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


def numeric_series(df: pd.DataFrame, col: str) -> np.ndarray:
    return pd.to_numeric(df[col], errors="coerce").to_numpy()


def finite_xy(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mask = np.isfinite(x) & np.isfinite(y)
    return x[mask], y[mask]


def extract_paired_series(
    x_all: np.ndarray, y_all: np.ndarray, series_name: str
) -> tuple[np.ndarray, np.ndarray]:
    x_finite = np.isfinite(x_all)
    y_finite = np.isfinite(y_all)
    if int(x_finite.sum()) != int(y_finite.sum()):
        raise SystemExit(
            f"{series_name} x/y valid-point counts do not match: "
            f"{int(x_finite.sum())} vs {int(y_finite.sum())}."
        )
    if not np.array_equal(x_finite, y_finite):
        raise SystemExit(
            f"{series_name} x/y must be paired on the same rows."
        )
    return x_all[x_finite], y_all[y_finite]


def parse_vline_specs(specs: list[str]) -> list[dict[str, str | float]]:
    parsed: list[dict[str, str | float]] = []

    def parse_x_token(token: str) -> list[float]:
        token = token.strip()
        if token.startswith("(") and token.endswith(")"):
            inner = token[1:-1].strip()
            inner = inner.replace(";", ",").replace("|", ",")
            values = [v.strip() for v in inner.split(",") if v.strip()]
            if len(values) < 2:
                raise SystemExit(
                    f"Invalid tuple x-value '{token}'. Expected at least two values."
                )
            try:
                return [float(v) for v in values]
            except ValueError:
                raise SystemExit(f"Invalid tuple x-value '{token}'.") from None
        if "|" in token:
            values = [v.strip() for v in token.split("|") if v.strip()]
            try:
                return [float(v) for v in values]
            except ValueError:
                raise SystemExit(f"Invalid multi-x value '{token}'.") from None
        try:
            return [float(token)]
        except ValueError:
            raise SystemExit(f"Invalid x-value '{token}'.") from None

    def normalize_label(raw_label: str) -> tuple[str, str | None]:
        cleaned = raw_label.strip()
        lower = cleaned.lower().replace(" ", "")
        if lower in {"t0", "t_0", "$t_0$"}:
            return r"$t_0$", "red"
        if lower in {"t*", "t_*", "tstar", "$t_*$"}:
            return r"$t_*$", "red"
        if lower == "ingress":
            return "Ingress", None
        if lower == "egress":
            return "Egress", None
        return cleaned, None

    for raw in specs:
        raw = raw.strip()
        if raw.startswith("("):
            close_idx = raw.find(")")
            if close_idx < 0:
                raise SystemExit(f"Invalid --vline spec '{raw}'. Missing ')'.")
            x_token = raw[: close_idx + 1]
            tail = raw[close_idx + 1 :].lstrip(",")
            parts = [x_token] + [p.strip() for p in tail.split(",")] if tail else [x_token]
        else:
            head = raw.split(",", 1)
            parts = [head[0].strip()]
            if len(head) > 1:
                parts.extend([p.strip() for p in head[1].split(",")])
        if len(parts) < 2 or not parts[1]:
            raise SystemExit(
                f"Invalid --vline spec '{raw}'. Expected at least 'x,label'."
            )
        x_vals = parse_x_token(parts[0])
        base_label, forced_color = normalize_label(parts[1])
        color = parts[2] if len(parts) >= 3 and parts[2] else "black"
        if forced_color is not None:
            color = forced_color
        linestyle = parts[3] if len(parts) >= 4 and parts[3] else "--"
        if len(x_vals) > 1 and base_label in {"Ingress", "Egress"}:
            suffixes = [" start", " end"]
        elif len(x_vals) > 1:
            suffixes = [f" {idx + 1}" for idx in range(len(x_vals))]
        else:
            suffixes = [""]
        for idx, x_val in enumerate(x_vals):
            parsed.append(
                {
                    "x": x_val,
                    "label": f"{base_label}{suffixes[idx]}",
                    "color": color,
                    "linestyle": linestyle,
                }
            )
    return parsed


def token_words(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z0-9_]+", text.lower())
    stop = {"the", "and", "or", "of", "to", "in", "on", "for", "with", "a", "an"}
    return {w for w in words if w not in stop}


def build_x_axis_context(
    x_raw: np.ndarray,
    x_label_override: str | None,
    x_var: str,
    x_unit: str,
    x_offset: float | None,
    x_offset_mod: float,
) -> tuple[np.ndarray, str, float]:
    def fmt_shift(value: float) -> str:
        rounded = round(value)
        if abs(value - rounded) < 1e-9:
            return str(int(rounded))
        return f"{value:g}"

    if x_offset is not None:
        shift = float(x_offset)
    else:
        finite = x_raw[np.isfinite(x_raw)]
        if finite.size == 0:
            shift = 0.0
        elif np.nanmax(np.abs(finite)) < x_offset_mod:
            shift = 0.0
        else:
            if x_offset_mod <= 0:
                raise SystemExit("--x-offset-mod must be > 0.")
            shift = float(np.floor(np.nanmedian(finite) / x_offset_mod) * x_offset_mod)

    x_plot = x_raw - shift
    if x_label_override:
        return x_plot, x_label_override, shift
    unit = f" ({x_unit})" if x_unit else ""
    if abs(shift) > 0:
        return x_plot, f"{x_var} - {fmt_shift(shift)}{unit}", shift
    return x_plot, f"{x_var}{unit}", shift


def values_for_x(
    query_x: np.ndarray, source_x: np.ndarray, source_y: np.ndarray, series_name: str
) -> np.ndarray:
    source = pd.DataFrame({"x": source_x, "y": source_y})
    if source["x"].duplicated().any():
        raise SystemExit(
            f"{series_name} has duplicate x-values; exact x lookup is ambiguous."
        )
    query = pd.DataFrame({"x": query_x})
    merged = query.merge(source, on="x", how="left", sort=False)
    missing = merged["y"].isna()
    if missing.any():
        missing_count = int(missing.sum())
        raise SystemExit(
            f"{series_name} is missing {missing_count} data x-value(s); "
            "provide --residual-col or pass matching x values."
        )
    return merged["y"].to_numpy()


def same_x_values(x_a: np.ndarray, x_b: np.ndarray) -> bool:
    if x_a.size != x_b.size:
        return False
    return np.array_equal(np.sort(x_a), np.sort(x_b))


def require_same_model_cadence(
    model_x: np.ndarray, other_x: np.ndarray, series_name: str
) -> None:
    if not same_x_values(model_x, other_x):
        raise SystemExit(
            f"{series_name} x-values must match model x-values (value-for-value)."
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
    has_initial_model = bool(
        args.initial_model_col and args.initial_model_col in df.columns
    )
    if args.initial_model_col and not has_initial_model:
        raise SystemExit(f"Initial model column not found: {args.initial_model_col}")
    posterior_cols = [c for c in args.posterior_model_col]
    missing_posterior = [c for c in posterior_cols if c not in df.columns]
    if missing_posterior:
        raise SystemExit(
            f"Posterior model column(s) not found: {', '.join(missing_posterior)}"
        )
    uses_model_series = bool(has_model or has_initial_model or posterior_cols)
    if uses_model_series and not args.model_x_col:
        raise SystemExit(
            "--model-x-col is required when plotting model, initial model, or posterior model columns."
        )
    if args.model_x_col and args.model_x_col not in df.columns:
        raise SystemExit(f"Model x column not found: {args.model_x_col}")
    vlines = parse_vline_specs(args.vline)

    if has_model or posterior_cols or has_initial_model:
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

    x_data_all = numeric_series(df, args.x_col)
    y_data_all = numeric_series(df, args.y_col)
    x_data_plot_all, x_axis_label, x_axis_shift = build_x_axis_context(
        x_data_all,
        args.x_label,
        args.x_var,
        args.x_unit,
        args.x_offset,
        args.x_offset_mod,
    )
    data_mask = np.isfinite(x_data_all) & np.isfinite(y_data_all)
    x_data = x_data_all[data_mask]
    x_data_plot = x_data_plot_all[data_mask]
    y_data = y_data_all[data_mask]

    err_data = None
    if args.err_col and args.err_col in df.columns:
        err_data_all = numeric_series(df, args.err_col)
        err_data = err_data_all[data_mask]
    residual_input = None
    if args.residual_col:
        if args.residual_col not in df.columns:
            raise SystemExit(f"Residual column not found: {args.residual_col}")
        residual_input = numeric_series(df, args.residual_col)[data_mask]

    model_x_all = numeric_series(df, args.model_x_col) if args.model_x_col else None
    model_x_plot_all = (model_x_all - x_axis_shift) if model_x_all is not None else None

    series = []
    if err_data is not None:
        container = ax.errorbar(
            x_data_plot,
            y_data,
            yerr=err_data,
            fmt="o",
            ms=3,
            alpha=0.8,
            label="Data",
            zorder=2,
        )
        data_line = container.lines[0]
    else:
        (data_line,) = ax.plot(
            x_data_plot, y_data, "o", ms=3, alpha=0.8, label="Data", zorder=2
        )

    series.append(
        {
            "name": "Data",
            "color": data_line.get_color(),
            "marker": data_line.get_marker(),
            "linestyle": data_line.get_linestyle(),
            "alpha": 0.8,
            "linewidth": float(data_line.get_linewidth()),
        }
    )

    if has_model:
        model_y_all = numeric_series(df, args.model_col)
        model_x, model_y = extract_paired_series(model_x_all, model_y_all, "Model")
        model_x_plot, _ = extract_paired_series(model_x_plot_all, model_y_all, "Model")
        (model_line,) = ax.plot(
            model_x_plot,
            model_y,
            "-",
            lw=1.8,
            color=args.model_color,
            label="Model",
            zorder=8,
        )
        series.append(
            {
                "name": "Model",
                "color": model_line.get_color(),
                "marker": model_line.get_marker(),
                "linestyle": model_line.get_linestyle(),
                "alpha": 1.0,
                "linewidth": float(model_line.get_linewidth()),
            }
        )
        if residual_input is None:
            try:
                model_on_data = values_for_x(x_data, model_x, model_y, "Model")
            except SystemExit:
                raise SystemExit(
                    "Model x-values do not cover data x-values; provide --residual-col."
                ) from None
            residuals = y_data - model_on_data
            residual_source = "computed"
        else:
            residuals = residual_input
            residual_source = "provided"
        resid_mask = np.isfinite(residuals)
        ax_resid.axhline(0.0, color="black", lw=1.0, alpha=0.7)
        if err_data is not None:
            resid_err_mask = resid_mask & np.isfinite(err_data)
            if np.any(resid_err_mask):
                ax_resid.errorbar(
                    x_data_plot[resid_err_mask],
                    residuals[resid_err_mask],
                    yerr=err_data[resid_err_mask],
                    fmt="o",
                    ms=2.5,
                    alpha=0.8,
                    zorder=4,
                )
            no_err_mask = resid_mask & ~np.isfinite(err_data)
            if np.any(no_err_mask):
                ax_resid.plot(
                    x_data_plot[no_err_mask],
                    residuals[no_err_mask],
                    "o",
                    ms=2.5,
                    alpha=0.8,
                    zorder=4,
                )
        else:
            ax_resid.plot(
                x_data_plot[resid_mask],
                residuals[resid_mask],
                "o",
                ms=2.5,
                alpha=0.8,
                zorder=4,
            )
        ax_resid.set_ylabel("Residual")
    elif posterior_cols or has_initial_model:
        ax_resid.axhline(0.0, color="black", lw=1.0, alpha=0.7)
        ax_resid.set_ylabel("Residual")

    posterior_count = 0
    posterior_base_color = args.posterior_color
    for idx, col in enumerate(posterior_cols):
        posterior_y_all = numeric_series(df, col)
        posterior_x, posterior_y = extract_paired_series(
            model_x_all, posterior_y_all, f"Posterior '{col}'"
        )
        posterior_x_plot, _ = extract_paired_series(
            model_x_plot_all, posterior_y_all, f"Posterior '{col}'"
        )
        label = "Posterior Samples" if idx == 0 else None
        (line,) = ax.plot(
            posterior_x_plot,
            posterior_y,
            args.posterior_style,
            lw=args.posterior_linewidth,
            alpha=args.posterior_alpha,
            color=posterior_base_color,
            label=label,
            zorder=7,
        )
        posterior_count += 1
        if has_model:
            require_same_model_cadence(model_x, posterior_x, f"Posterior '{col}'")
            posterior_on_data = values_for_x(
                x_data, posterior_x, posterior_y, f"Posterior '{col}'"
            )
            resid = y_data - posterior_on_data
            resid_mask = np.isfinite(resid)
            ax_resid.plot(
                x_data_plot[resid_mask],
                resid[resid_mask],
                args.posterior_style,
                lw=max(0.9, args.posterior_linewidth * 0.75),
                alpha=min(0.7, args.posterior_alpha * 1.2),
                color=posterior_base_color,
                zorder=3,
            )
        if idx == 0:
            series.append(
                {
                    "name": "Posterior Samples",
                    "color": line.get_color(),
                    "marker": line.get_marker(),
                    "linestyle": line.get_linestyle(),
                    "alpha": float(args.posterior_alpha),
                    "linewidth": float(args.posterior_linewidth),
                }
            )

    if has_initial_model:
        init_y_all = numeric_series(df, args.initial_model_col)
        init_x, init_y = extract_paired_series(
            model_x_all, init_y_all, "Initial model"
        )
        init_x_plot, _ = extract_paired_series(
            model_x_plot_all, init_y_all, "Initial model"
        )
        (init_line,) = ax.plot(
            init_x_plot,
            init_y,
            args.initial_model_style,
            lw=1.5,
            color=args.initial_model_color,
            alpha=0.95,
            label="Initial Model",
            zorder=7.5,
        )
        series.append(
            {
                "name": "Initial Model",
                "color": init_line.get_color(),
                "marker": init_line.get_marker(),
                "linestyle": init_line.get_linestyle(),
                "alpha": 0.95,
                "linewidth": float(init_line.get_linewidth()),
            }
        )
        if ax_resid is not None and has_model:
            require_same_model_cadence(model_x, init_x, "Initial model")
            init_on_data = values_for_x(x_data, init_x, init_y, "Initial model")
            init_resid = y_data - init_on_data
            init_resid_mask = np.isfinite(init_resid)
            ax_resid.plot(
                x_data_plot[init_resid_mask],
                init_resid[init_resid_mask],
                args.initial_model_style,
                lw=0.9,
                color=args.initial_model_color,
                alpha=0.6,
                zorder=3.5,
            )

    validation_warnings: list[str] = []
    if not args.tex:
        validation_warnings.append(
            "TeX rendering is disabled (--no-tex). For journal publication, TeX text rendering is recommended."
        )
    if args.title and args.title.strip():
        validation_warnings.append(
            "Title present. If title does not add clarifying information, prefer a detailed caption instead."
        )
        legend_labels = [str(item["name"]) for item in series]
        axis_words = token_words(x_axis_label) | token_words(args.y_label)
        legend_words = set()
        for label in legend_labels:
            legend_words |= token_words(label)
        title_words = token_words(args.title)
        overlap = sorted(title_words & (axis_words | legend_words))
        if overlap:
            raise SystemExit(
                "Style error: title repeats axis/legend words: "
                + ", ".join(overlap)
            )

    ax.set_title(args.title)
    ax.set_xlabel(x_axis_label if ax_resid is None else "")
    ax.set_ylabel(args.y_label)

    # Standard astronomy convention for magnitude-based plots.
    if args.mode == "magnitude":
        ax.invert_yaxis()

    ax.legend(loc="best", fontsize=9)
    if vlines:
        trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
        for entry in vlines:
            x_val = float(entry["x"])
            x_val_plot = x_val - x_axis_shift
            color = str(entry["color"])
            linestyle = str(entry["linestyle"])
            label = str(entry["label"])
            ax.axvline(
                x_val_plot, color=color, linestyle=linestyle, lw=1.1, alpha=0.9, zorder=9
            )
            ax.text(
                x_val_plot,
                0.98,
                label,
                transform=trans,
                rotation=90,
                va="top",
                ha="right",
                fontsize=8,
                color=color,
                zorder=10,
            )
            if ax_resid is not None:
                ax_resid.axvline(
                    x_val_plot,
                    color=color,
                    linestyle=linestyle,
                    lw=0.9,
                    alpha=0.7,
                    zorder=5,
                )

    if ax_resid is not None:
        ax_resid.set_xlabel(x_axis_label)

    fig.tight_layout()

    output_stem = Path(args.output)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = output_stem.with_suffix(".pdf")
    png_path = output_stem.with_suffix(".png")
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)

    manifest_path = (
        Path(args.manifest_output)
        if args.manifest_output
        else output_stem.with_suffix(".meta.json")
    )
    manifest = {
        "status": "ok",
        "summary": "Generated lightcurve figure",
        "artifacts": [
            str(pdf_path.resolve()),
            str(png_path.resolve()),
            str(manifest_path.resolve()),
        ],
        "figure": {
            "title": args.title,
            "mode": args.mode,
            "tex_enabled": bool(args.tex),
            "has_residual_panel": bool(has_model or posterior_cols or has_initial_model),
            "has_initial_model_overlay": bool(has_initial_model),
            "posterior_overlay": bool(posterior_count > 0),
            "posterior_sample_count": int(posterior_count),
            "model_x_column": args.model_x_col,
            "x_axis_shift": x_axis_shift,
            "residual_source": residual_source if has_model else "none",
            "vertical_annotations": vlines,
            "labels": {"x": x_axis_label, "y": args.y_label},
            "labels_include_units": ("(" in x_axis_label and ")" in x_axis_label)
            and ("(" in args.y_label and ")" in args.y_label),
        },
        "exports": [
            {"format": "pdf", "path": str(pdf_path.resolve())},
            {"format": "png", "path": str(png_path.resolve()), "dpi": 300},
        ],
        "series": series,
        "provenance": {"input": str(Path(args.input).resolve())},
        "validation": {"required_columns": True, "warnings": validation_warnings},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))

    for warning in validation_warnings:
        print(f"Warning: {warning}")
    print(f"Saved: {pdf_path}")
    print(f"Saved: {png_path}")
    print(f"Saved: {manifest_path}")


if __name__ == "__main__":
    main()
