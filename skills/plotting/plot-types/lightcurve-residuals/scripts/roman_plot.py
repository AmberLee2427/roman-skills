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


JOURNAL_PROFILES_PATH = (
    Path(__file__).resolve().parents[3]
    / "style-profiles"
    / "assets"
    / "journal_profiles.json"
)


def load_journal_profiles() -> dict[str, dict[str, object]]:
    if not JOURNAL_PROFILES_PATH.exists():
        raise SystemExit(f"Journal profiles file not found: {JOURNAL_PROFILES_PATH}")
    return json.loads(JOURNAL_PROFILES_PATH.read_text())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Roman analysis plot")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output file stem (no extension)")
    parser.add_argument("--x-col", required=True, help="X-axis column name")
    parser.add_argument("--y-col", required=True, help="Y-axis column name")
    parser.add_argument(
        "--band-label",
        default="Data",
        help="Legend label for the primary dataset (x/y/err/model columns).",
    )
    parser.add_argument(
        "--band-spec",
        action="append",
        default=[],
        help=(
            "Additional band definition (repeatable): "
            "'label,y_col[,err_col[,x_col[,model_col[,y_kind]]]]'. "
            "Use empty fields to inherit defaults."
        ),
    )
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
        "--best-fit-label",
        choices=["mle", "map", "model"],
        default="mle",
        help=(
            "Legend label semantics for --model-col. Use 'mle' for maximum "
            "likelihood, 'map' for maximum a posteriori, or 'model' if the "
            "estimator is unknown."
        ),
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
        "--y-kind",
        choices=["magnification", "flux", "magnitude", "delta_flux"],
        help=(
            "Physical meaning of y-values. Required for strict scientific semantics; "
            "if omitted, inferred from --mode for backward compatibility."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["flux", "magnitude"],
        default="flux",
        help=(
            "Deprecated shorthand for y-axis interpretation. "
            "Prefer --y-kind."
        ),
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
    parser.add_argument(
        "--y-label",
        default="",
        help=(
            "Manual y-axis label override. Prefer structured label inputs "
            "(--y-band/--y-scale/--y-unit)."
        ),
    )
    parser.add_argument(
        "--y-band",
        default="",
        help="Band/filter tag for y-axis label construction (for example: W146).",
    )
    parser.add_argument(
        "--y-scale",
        default="",
        help="Scale descriptor for y-axis label construction (for example: normalized).",
    )
    parser.add_argument(
        "--y-unit",
        default="",
        help="Y-axis unit for label construction (for example: mag).",
    )
    parser.add_argument("--title", default="", help="Figure title")
    parser.add_argument(
        "--paper-span",
        choices=["single", "double"],
        default="single",
        help="Publication width preset: single-column or double-column span.",
    )
    parser.add_argument(
        "--figure-width-in",
        type=float,
        help="Exact figure width in inches. Overrides --paper-span width preset.",
    )
    parser.add_argument(
        "--figure-height-in",
        type=float,
        help="Exact figure height in inches. Overrides automatic height selection.",
    )
    parser.add_argument(
        "--journal-profile",
        help=(
            "Journal rendering profile (for example: apj, nature, science, mnras). "
            "When set, paper width and typography defaults come from the shared profile."
        ),
    )
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
        "--baseline-mode",
        choices=["scalar", "column"],
        default="scalar",
        help=(
            "How to define baseline for model-driven x-zoom. "
            "'scalar' uses --baseline-level or inferred scalar baseline; "
            "'column' uses --baseline-col."
        ),
    )
    parser.add_argument(
        "--baseline-level",
        type=float,
        help="Explicit scalar baseline level.",
    )
    parser.add_argument(
        "--baseline-col",
        help=(
            "Column containing time-dependent baseline values (same cadence as model x/y)."
        ),
    )
    parser.add_argument(
        "--baseline-method",
        choices=["tail-median", "global-median", "quantile-high", "quantile-low"],
        default="tail-median",
        help="Method to infer scalar baseline when --baseline-level is not provided.",
    )
    parser.add_argument(
        "--baseline-tail-frac",
        type=float,
        default=0.2,
        help=(
            "Fraction from each time edge used by tail-median baseline inference "
            "(0 < frac <= 0.5)."
        ),
    )
    parser.add_argument(
        "--baseline-quantile",
        type=float,
        default=0.9,
        help=(
            "Quantile used for quantile-high/quantile-low scalar baseline inference "
            "(0 < q < 1)."
        ),
    )
    parser.add_argument(
        "--baseline-consistency-frac",
        type=float,
        default=0.2,
        help=(
            "For tail-median inference, fail if head vs tail baseline medians differ "
            "by more than this fraction of model dynamic range."
        ),
    )
    parser.add_argument(
        "--auto-x-zoom",
        choices=["none", "trim-baseline"],
        default="none",
        help=(
            "Automatic x-windowing mode. 'trim-baseline' crops only leading/trailing "
            "baseline using model-baseline deltas."
        ),
    )
    parser.add_argument(
        "--auto-x-zoom-frac",
        type=float,
        default=0.01,
        help=(
            "Baseline threshold fraction for trim-baseline mode: "
            "|model-baseline| < frac * (model_max-model_min)."
        ),
    )
    parser.add_argument(
        "--auto-x-zoom-pad",
        type=float,
        default=0.0,
        help="Optional x-padding added to auto-trimmed bounds (x units).",
    )
    parser.add_argument(
        "--x-zoom-range",
        help="Manual x-window override as 'xmin,xmax'.",
    )
    parser.add_argument(
        "--normalize-mode",
        choices=["none", "additive", "affine"],
        default="none",
        help=(
            "Cross-band normalization mode to match a reference band. "
            "'additive' fits y'=y+b; 'affine' fits y'=a*y+b."
        ),
    )
    parser.add_argument(
        "--normalize-reference-band",
        help="Reference band label used for cross-band normalization.",
    )
    parser.add_argument(
        "--normalize-source",
        choices=["model", "data"],
        default="model",
        help=(
            "Series used to estimate normalization coefficients. "
            "'model' requires model columns on all normalized bands."
        ),
    )
    parser.add_argument(
        "--normalize-min-overlap",
        type=int,
        default=8,
        help="Minimum exact x-overlap points required for normalization fit.",
    )
    parser.add_argument(
        "--tex",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Enable LaTeX text rendering. If omitted, the selected journal profile "
            "controls the default. Use --no-tex to disable explicitly."
        ),
    )
    args = parser.parse_args(argv)
    if args.journal_profile:
        profiles = load_journal_profiles()
        if args.journal_profile not in profiles:
            available = ", ".join(sorted(profiles))
            raise SystemExit(
                f"Unknown --journal-profile '{args.journal_profile}'. "
                f"Available profiles: {available}"
            )
    return args


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


def format_numeric_label_value(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 1e-9:
        return str(int(rounded))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def math_band_label(band_label: str, reference: bool = False) -> str:
    suffix = "^*" if reference else ""
    return f"$\\mathrm{{{band_label}}}{suffix}$"


def normalization_suffix(meta: dict[str, float | str], band_label: str) -> str:
    mode = str(meta.get("mode", "none"))
    if mode == "none":
        return ""

    ref = str(meta.get("reference_band", "")).strip()
    if ref == band_label:
        return ""

    scale = float(meta.get("scale", 1.0))
    offset = float(meta.get("offset", 0.0))
    parts: list[str] = []
    if mode == "additive":
        sign = "+" if offset >= 0 else "-"
        parts.append(f"{sign} {format_numeric_label_value(abs(offset))}")
    elif mode == "affine":
        parts.append(f"x {format_numeric_label_value(scale)}")
        sign = "+" if offset >= 0 else "-"
        parts.append(f"{sign} {format_numeric_label_value(abs(offset))}")
    return " " + " ".join(parts) if parts else ""


def data_series_label(meta: dict[str, float | str], band_label: str) -> str:
    ref = str(meta.get("reference_band", "")).strip()
    mode = str(meta.get("mode", "none"))
    if mode != "none" and ref == band_label:
        return f"{math_band_label(band_label, reference=True)} Data"
    if mode != "none":
        return f"{math_band_label(band_label)} Data{normalization_suffix(meta, band_label)}"
    return f"{band_label} Data"


def best_fit_series_label(
    estimator: str,
    band_label: str,
    multi_band: bool,
) -> str:
    estimator_text = {
        "mle": "MLE",
        "map": "MAP",
        "model": "Model",
    }[estimator]
    if estimator_text == "Model":
        return (
            f"{math_band_label(band_label)} Model"
            if multi_band or band_label.lower() != "data"
            else "Model"
        )
    return (
        f"{math_band_label(band_label)} {estimator_text} Model"
        if multi_band or band_label.lower() != "data"
        else f"{estimator_text} Model"
    )


def publication_figure_geometry(
    paper_span: str,
    has_residual_panel: bool,
    figure_width_in: float | None,
    figure_height_in: float | None,
    journal_profile: dict[str, object] | None,
) -> tuple[tuple[float, float], dict[str, float | str]]:
    span_widths = {"single": 3.4, "double": 7.0}
    if journal_profile:
        profile_widths = journal_profile.get("paper_width_in", {})
        if isinstance(profile_widths, dict):
            span_widths = {
                **span_widths,
                **{
                    str(k): float(v)
                    for k, v in profile_widths.items()
                    if str(k) in {"single", "double"}
                },
            }
    width = float(figure_width_in) if figure_width_in is not None else span_widths[paper_span]
    if width <= 0:
        raise SystemExit("--figure-width-in must be positive.")

    if figure_height_in is not None:
        height = float(figure_height_in)
    elif has_residual_panel:
        height = width * (1.12 if paper_span == "single" else 0.78)
    else:
        height = width * (0.82 if paper_span == "single" else 0.62)
    if height <= 0:
        raise SystemExit("--figure-height-in must be positive.")

    geometry = {
        "paper_span": paper_span,
        "width_in": width,
        "height_in": height,
        "has_residual_panel": bool(has_residual_panel),
    }
    return (width, height), geometry


def publication_font_sizes(paper_span: str) -> dict[str, float]:
    if paper_span == "double":
        return {
            "base": 10.0,
            "title": 10.5,
            "label": 10.0,
            "tick": 9.0,
            "legend": 9.0,
            "annotation": 8.5,
        }
    return {
        "base": 8.5,
        "title": 9.0,
        "label": 8.5,
        "tick": 7.5,
        "legend": 7.5,
        "annotation": 7.0,
    }


def resolved_font_sizes(
    paper_span: str,
    journal_profile: dict[str, object] | None,
) -> dict[str, float]:
    defaults = publication_font_sizes(paper_span)
    if not journal_profile:
        return defaults
    profile_sizes = journal_profile.get("font_sizes_pt", {})
    if not isinstance(profile_sizes, dict):
        return defaults
    span_sizes = profile_sizes.get(paper_span, {})
    if not isinstance(span_sizes, dict):
        return defaults
    merged = dict(defaults)
    for key, value in span_sizes.items():
        merged[str(key)] = float(value)
    return merged


def apply_publication_rcparams(
    font_sizes: dict[str, float],
    tex_enabled: bool,
    journal_profile: dict[str, object] | None,
) -> str:
    plt.rcdefaults()
    plt.rcParams["text.usetex"] = bool(tex_enabled)

    font_family = "serif"
    if journal_profile:
        font_family = str(journal_profile.get("font_family", font_family))
        candidates = journal_profile.get("font_family_candidates", [])
        if isinstance(candidates, list) and candidates:
            rc_key = "font.serif" if font_family == "serif" else "font.sans-serif"
            plt.rcParams[rc_key] = [str(item) for item in candidates]
    plt.rcParams["font.family"] = font_family
    plt.rcParams["font.size"] = font_sizes["base"]
    plt.rcParams["axes.titlesize"] = font_sizes["title"]
    plt.rcParams["axes.labelsize"] = font_sizes["label"]
    plt.rcParams["xtick.labelsize"] = font_sizes["tick"]
    plt.rcParams["ytick.labelsize"] = font_sizes["tick"]
    plt.rcParams["legend.fontsize"] = font_sizes["legend"]
    return font_family


def resolved_graphics_style(
    paper_span: str,
    journal_profile: dict[str, object] | None,
) -> dict[str, float]:
    defaults = {
        "data_linewidth": 0.7 if paper_span == "single" else 0.9,
        "model_linewidth": 0.9 if paper_span == "single" else 1.1,
        "residual_linewidth": 0.6 if paper_span == "single" else 0.75,
        "reference_linewidth": 0.7 if paper_span == "single" else 0.8,
        "vline_linewidth": 0.8 if paper_span == "single" else 0.9,
        "marker_size": 2.4 if paper_span == "single" else 2.8,
        "residual_marker_size": 1.9 if paper_span == "single" else 2.2,
    }
    if not journal_profile:
        return defaults
    profile_styles = journal_profile.get("graphics_style_pt", {})
    if not isinstance(profile_styles, dict):
        return defaults
    span_styles = profile_styles.get(paper_span, {})
    if not isinstance(span_styles, dict):
        return defaults
    merged = dict(defaults)
    for key, value in span_styles.items():
        merged[str(key)] = float(value)
    return merged


def infer_band_wavelength_key(band_label: str) -> tuple[int, float, str]:
    normalized = band_label.strip().lower()
    explicit_wavelengths = {
        "r062": 0.62,
        "z087": 0.87,
        "y106": 1.06,
        "j129": 1.29,
        "h158": 1.58,
        "f184": 1.84,
        "k213": 2.13,
        "w146": 1.46,
        "u": 0.36,
        "g": 0.48,
        "r": 0.62,
        "i": 0.75,
        "z": 0.87,
        "y": 0.97,
        "j": 1.25,
        "h": 1.65,
        "k": 2.20,
    }
    if normalized in explicit_wavelengths:
        return (0, explicit_wavelengths[normalized], normalized)

    match = re.search(r"(\d+(?:\.\d+)?)", normalized)
    if match:
        raw = float(match.group(1))
        wavelength = raw / 100.0 if raw >= 10 else raw
        return (1, wavelength, normalized)

    return (2, float("inf"), normalized)


def color_for_band_order(label: str, labels: list[str]) -> str:
    spectral_palette = [
        "#3B4CC0",
        "#5E81F4",
        "#2FB7C8",
        "#2E8B57",
        "#A4C73C",
        "#F3C64D",
        "#F28E2B",
        "#D1495B",
    ]
    ordered = sorted(labels, key=infer_band_wavelength_key)
    idx = ordered.index(label)
    if len(ordered) == 1:
        return spectral_palette[0]
    scaled_idx = round(idx * (len(spectral_palette) - 1) / (len(ordered) - 1))
    return spectral_palette[scaled_idx]


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


def parse_x_zoom_range(spec: str | None) -> tuple[float, float] | None:
    if not spec:
        return None
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise SystemExit(
            "--x-zoom-range must be provided as 'xmin,xmax'."
        )
    try:
        xmin = float(parts[0])
        xmax = float(parts[1])
    except ValueError:
        raise SystemExit(
            "--x-zoom-range contains non-numeric values."
        ) from None
    if not np.isfinite(xmin) or not np.isfinite(xmax):
        raise SystemExit("--x-zoom-range values must be finite.")
    if xmin >= xmax:
        raise SystemExit("--x-zoom-range requires xmin < xmax.")
    return (xmin, xmax)


def infer_scalar_baseline(
    x_model: np.ndarray,
    y_model: np.ndarray,
    method: str,
    tail_frac: float,
    quantile: float,
    consistency_frac: float,
) -> tuple[float, dict[str, float | str]]:
    if y_model.size == 0:
        raise SystemExit("Cannot infer baseline from empty model series.")
    if not (0.0 < quantile < 1.0):
        raise SystemExit("--baseline-quantile must satisfy 0 < q < 1.")
    if not (0.0 < tail_frac <= 0.5):
        raise SystemExit("--baseline-tail-frac must satisfy 0 < frac <= 0.5.")
    if consistency_frac < 0:
        raise SystemExit("--baseline-consistency-frac must be >= 0.")

    amp = float(np.nanmax(y_model) - np.nanmin(y_model))
    if method == "global-median":
        baseline = float(np.nanmedian(y_model))
        return baseline, {"method": method}
    if method == "quantile-high":
        baseline = float(np.nanquantile(y_model, quantile))
        return baseline, {"method": method, "quantile": quantile}
    if method == "quantile-low":
        baseline = float(np.nanquantile(y_model, 1.0 - quantile))
        return baseline, {"method": method, "quantile": 1.0 - quantile}
    order = np.argsort(x_model)
    y_sorted = y_model[order]
    n = y_sorted.size
    n_tail = max(1, int(np.floor(n * tail_frac)))
    head = y_sorted[:n_tail]
    tail = y_sorted[-n_tail:]
    head_med = float(np.nanmedian(head))
    tail_med = float(np.nanmedian(tail))
    if amp > 0:
        diff = abs(head_med - tail_med)
        if diff > consistency_frac * amp:
            raise SystemExit(
                "Tail-median baseline inference is unstable: head/tail medians "
                "differ too much relative to model range. Provide --baseline-level "
                "or use --baseline-mode column with --baseline-col."
            )
    baseline = float(np.nanmedian(np.concatenate([head, tail])))
    return baseline, {
        "method": method,
        "tail_frac": tail_frac,
        "head_median": head_med,
        "tail_median": tail_med,
    }


def resolve_baseline_series(
    args: argparse.Namespace,
    model_x: np.ndarray,
    model_y: np.ndarray,
    model_x_all: np.ndarray,
    df: pd.DataFrame,
) -> tuple[np.ndarray, dict[str, float | str]]:
    if args.baseline_mode == "column":
        if not args.baseline_col:
            raise SystemExit(
                "--baseline-mode column requires --baseline-col."
            )
        if args.baseline_col not in df.columns:
            raise SystemExit(f"Baseline column not found: {args.baseline_col}")
        baseline_all = numeric_series(df, args.baseline_col)
        base_x, baseline = extract_paired_series(
            model_x_all, baseline_all, f"Baseline '{args.baseline_col}'"
        )
        require_same_model_cadence(model_x, base_x, f"Baseline '{args.baseline_col}'")
        return baseline, {"mode": "column", "column": args.baseline_col}

    if args.baseline_col:
        raise SystemExit(
            "--baseline-col is only valid with --baseline-mode column."
        )

    if args.baseline_level is not None:
        baseline_level = float(args.baseline_level)
        return np.full_like(model_y, baseline_level, dtype=float), {
            "mode": "scalar",
            "source": "explicit",
            "level": baseline_level,
        }

    baseline_level, details = infer_scalar_baseline(
        x_model=model_x,
        y_model=model_y,
        method=args.baseline_method,
        tail_frac=args.baseline_tail_frac,
        quantile=args.baseline_quantile,
        consistency_frac=args.baseline_consistency_frac,
    )
    metadata: dict[str, float | str] = {
        "mode": "scalar",
        "source": "inferred",
        "level": baseline_level,
    }
    metadata.update(details)
    return np.full_like(model_y, baseline_level, dtype=float), metadata


def compute_trim_baseline_window(
    model_x: np.ndarray,
    model_y: np.ndarray,
    baseline: np.ndarray,
    frac: float,
    pad: float,
) -> tuple[float, float]:
    if model_x.size == 0:
        raise SystemExit("Cannot compute auto x-zoom from empty model series.")
    if frac <= 0:
        raise SystemExit("--auto-x-zoom-frac must be > 0.")
    if pad < 0:
        raise SystemExit("--auto-x-zoom-pad must be >= 0.")
    amp = float(np.nanmax(model_y) - np.nanmin(model_y))
    if not np.isfinite(amp) or amp <= 0:
        raise SystemExit(
            "Model dynamic range is zero; cannot determine baseline trim window."
        )
    threshold = frac * amp
    delta = np.abs(model_y - baseline)
    event_mask = np.isfinite(delta) & (delta >= threshold)
    if not np.any(event_mask):
        raise SystemExit(
            "No non-baseline model region detected for auto x-zoom. "
            "Adjust --auto-x-zoom-frac or provide --x-zoom-range."
        )
    x_event = model_x[event_mask]
    xmin = float(np.nanmin(x_event) - pad)
    xmax = float(np.nanmax(x_event) + pad)
    if xmin >= xmax:
        raise SystemExit(
            "Auto x-zoom produced invalid bounds."
        )
    return xmin, xmax


def parse_band_specs(
    args: argparse.Namespace, df: pd.DataFrame, default_y_kind: str
) -> list[dict[str, str | None]]:
    bands: list[dict[str, str | None]] = [
        {
            "label": args.band_label,
            "x_col": args.x_col,
            "y_col": args.y_col,
            "err_col": args.err_col,
            "model_col": args.model_col,
            "y_kind": default_y_kind,
        }
    ]
    for raw in args.band_spec:
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise SystemExit(
                "Invalid --band-spec. Expected "
                "'label,y_col[,err_col[,x_col[,model_col[,y_kind]]]]'."
            )
        label = parts[0]
        y_col = parts[1]
        err_col = parts[2] if len(parts) >= 3 and parts[2] else None
        x_col = parts[3] if len(parts) >= 4 and parts[3] else args.x_col
        model_col = parts[4] if len(parts) >= 5 and parts[4] else None
        y_kind = parts[5] if len(parts) >= 6 and parts[5] else default_y_kind
        if y_kind not in {"magnification", "flux", "magnitude", "delta_flux"}:
            raise SystemExit(
                f"Invalid y_kind in --band-spec '{label}': {y_kind}"
            )
        bands.append(
            {
                "label": label,
                "x_col": x_col,
                "y_col": y_col,
                "err_col": err_col,
                "model_col": model_col,
                "y_kind": y_kind,
            }
        )

    labels = [str(b["label"]) for b in bands]
    if len(set(labels)) != len(labels):
        raise SystemExit("Band labels must be unique.")

    for band in bands:
        x_col = str(band["x_col"])
        y_col = str(band["y_col"])
        if x_col not in df.columns:
            raise SystemExit(f"Band '{band['label']}' x column not found: {x_col}")
        if y_col not in df.columns:
            raise SystemExit(f"Band '{band['label']}' y column not found: {y_col}")
        if band["err_col"] and str(band["err_col"]) not in df.columns:
            raise SystemExit(
                f"Band '{band['label']}' error column not found: {band['err_col']}"
            )
        if band["model_col"] and str(band["model_col"]) not in df.columns:
            raise SystemExit(
                f"Band '{band['label']}' model column not found: {band['model_col']}"
            )
    return bands


def overlap_pairs(
    ref_x: np.ndarray,
    ref_y: np.ndarray,
    target_x: np.ndarray,
    target_y: np.ndarray,
    ref_name: str,
    target_name: str,
) -> tuple[np.ndarray, np.ndarray]:
    ref_df = pd.DataFrame({"x": ref_x, "y": ref_y})
    tgt_df = pd.DataFrame({"x": target_x, "y": target_y})
    if ref_df["x"].duplicated().any():
        raise SystemExit(
            f"{ref_name} has duplicate x-values; normalization mapping is ambiguous."
        )
    if tgt_df["x"].duplicated().any():
        raise SystemExit(
            f"{target_name} has duplicate x-values; normalization mapping is ambiguous."
        )
    merged = ref_df.merge(tgt_df, on="x", how="inner", suffixes=("_ref", "_target"))
    if merged.empty:
        raise SystemExit(
            f"No exact x-overlap between {ref_name} and {target_name} for normalization."
        )
    return merged["y_target"].to_numpy(), merged["y_ref"].to_numpy()


def fit_normalization(
    mode: str, target: np.ndarray, ref: np.ndarray
) -> tuple[float, float]:
    if mode == "additive":
        offset = float(np.nanmedian(ref - target))
        return 1.0, offset
    if mode == "affine":
        design = np.column_stack([target, np.ones_like(target)])
        coeff, *_ = np.linalg.lstsq(design, ref, rcond=None)
        scale = float(coeff[0])
        offset = float(coeff[1])
        return scale, offset
    return 1.0, 0.0


def residual_axis_label(y_kind: str, y_label: str) -> str:
    unit_match = re.search(r"\(([^)]+)\)", y_label)
    if unit_match:
        unit = unit_match.group(1).strip()
        if unit:
            return f"Residual ({unit})"
    unit_by_kind = {
        "magnitude": "mag",
        "flux": "flux",
        "magnification": "magnification",
        "delta_flux": "delta flux",
    }
    unit = unit_by_kind.get(y_kind, "")
    return f"Residual ({unit})" if unit else "Residual"


def build_y_axis_label(
    y_kind: str,
    y_label_override: str,
    y_band: str,
    y_scale: str,
    y_unit: str,
) -> tuple[str, bool]:
    override = y_label_override.strip()
    if override:
        return override, True

    if y_kind == "magnitude":
        base = f"{y_band.strip()} Magnitude".strip() if y_band.strip() else "Magnitude"
        default_unit = "mag"
    elif y_kind == "flux":
        base = f"{y_band.strip()} Flux".strip() if y_band.strip() else "Flux"
        default_unit = ""
    elif y_kind == "delta_flux":
        base = f"{y_band.strip()} Delta Flux".strip() if y_band.strip() else "Delta Flux"
        default_unit = ""
    else:
        base = "Magnification"
        default_unit = ""

    if y_scale.strip():
        base = f"{y_scale.strip()} {base}"
    unit = y_unit.strip() if y_unit.strip() else default_unit
    if unit:
        return f"{base} ({unit})", False
    return base, False


def render_lightcurve(
    args: argparse.Namespace, df: pd.DataFrame | None = None
) -> tuple[plt.Figure, dict]:
    journal_profiles = load_journal_profiles()
    journal_profile = (
        journal_profiles.get(args.journal_profile) if args.journal_profile else None
    )
    y_kind = args.y_kind if args.y_kind else args.mode
    if args.y_kind and args.mode != "flux":
        mode_kind = args.mode
        if mode_kind != args.y_kind:
            raise SystemExit(
                "Conflicting y semantics: --mode and --y-kind disagree. "
                "Use one convention."
            )
    if y_kind == "magnitude":
        mode_for_render = "magnitude"
    else:
        mode_for_render = "flux"

    uses_model_series = False
    resolved_tex = (
        bool(args.tex)
        if args.tex is not None
        else bool(journal_profile.get("tex_default", True) if journal_profile else True)
    )
    if resolved_tex:
        check_tex_dependencies()
    if df is None:
        df = pd.read_csv(args.input)
    y_axis_label, used_manual_y_label = build_y_axis_label(
        y_kind=y_kind,
        y_label_override=args.y_label,
        y_band=args.y_band,
        y_scale=args.y_scale,
        y_unit=args.y_unit,
    )
    bands = parse_band_specs(args, df, y_kind)
    band_y_kinds = sorted({str(b["y_kind"]) for b in bands})
    if len(band_y_kinds) != 1:
        raise SystemExit(
            "Mixed y-kind values are not supported in a single panel. "
            "Split by physical quantity or convert first."
        )
    y_kind = band_y_kinds[0]
    mode_for_render = "magnitude" if y_kind == "magnitude" else "flux"
    multi_band = len(bands) > 1

    has_model = any(bool(b["model_col"]) for b in bands)
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
    if multi_band and (posterior_cols or has_initial_model):
        raise SystemExit(
            "Multiband mode does not support --posterior-model-col or --initial-model-col yet."
        )
    if multi_band and args.residual_col:
        raise SystemExit(
            "--residual-col is not supported in multiband mode."
        )

    if args.normalize_mode != "none":
        if not args.normalize_reference_band:
            raise SystemExit(
                "--normalize-reference-band is required when --normalize-mode is not 'none'."
            )
        band_names = {str(b["label"]) for b in bands}
        if args.normalize_reference_band not in band_names:
            raise SystemExit(
                f"Normalization reference band not found: {args.normalize_reference_band}"
            )
        if y_kind == "magnification":
            raise SystemExit(
                "Normalization is invalid for y-kind='magnification'. Use raw magnification."
            )
        if args.normalize_mode == "affine" and y_kind == "magnitude":
            raise SystemExit(
                "Normalization mode 'affine' is invalid for y-kind='magnitude' "
                "(use additive offset)."
            )
    elif args.normalize_reference_band:
        raise SystemExit(
            "--normalize-reference-band requires --normalize-mode additive|affine."
        )
    if args.normalize_min_overlap < 2:
        raise SystemExit("--normalize-min-overlap must be >= 2.")

    uses_model_series = bool(has_model or has_initial_model or posterior_cols)
    if uses_model_series and not args.model_x_col:
        raise SystemExit(
            "--model-x-col is required when plotting model, initial model, or posterior model columns."
        )
    if args.model_x_col and args.model_x_col not in df.columns:
        raise SystemExit(f"Model x column not found: {args.model_x_col}")
    vlines = parse_vline_specs(args.vline)
    has_residual_panel = bool(has_model or posterior_cols or has_initial_model)
    figure_size, figure_geometry = publication_figure_geometry(
        paper_span=args.paper_span,
        has_residual_panel=has_residual_panel,
        figure_width_in=args.figure_width_in,
        figure_height_in=args.figure_height_in,
        journal_profile=journal_profile,
    )
    font_sizes = resolved_font_sizes(args.paper_span, journal_profile)
    graphics_style = resolved_graphics_style(args.paper_span, journal_profile)
    resolved_font_family = apply_publication_rcparams(
        font_sizes=font_sizes,
        tex_enabled=resolved_tex,
        journal_profile=journal_profile,
    )

    if has_residual_panel:
        fig, (ax, ax_resid) = plt.subplots(
            2,
            1,
            figsize=figure_size,
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]},
        )
    else:
        fig, ax = plt.subplots(figsize=figure_size)
        ax_resid = None

    x_anchor_all = numeric_series(df, args.x_col)
    x_anchor_plot_all, x_axis_label, x_axis_shift = build_x_axis_context(
        x_anchor_all,
        args.x_label,
        args.x_var,
        args.x_unit,
        args.x_offset,
        args.x_offset_mod,
    )
    x_zoom_manual = parse_x_zoom_range(args.x_zoom_range)
    x_zoom_auto: tuple[float, float] | None = None
    baseline_metadata: dict[str, float | str] | None = None
    residual_source: str | dict[str, str] = "none"
    residual_source_by_band: dict[str, str] = {}
    normalization_meta: dict[str, dict[str, float | str]] = {}

    model_x_all = numeric_series(df, args.model_x_col) if args.model_x_col else None
    model_x_plot_all = (model_x_all - x_axis_shift) if model_x_all is not None else None

    markers = ["o", "s", "^", "D", "v", "P"]
    band_labels = [str(b["label"]) for b in bands]

    band_states: list[dict[str, object]] = []
    for band in bands:
        label = str(band["label"])
        x_all = numeric_series(df, str(band["x_col"]))
        y_all = numeric_series(df, str(band["y_col"]))
        data_mask = np.isfinite(x_all) & np.isfinite(y_all)
        x_data = x_all[data_mask]
        x_data_plot = x_data - x_axis_shift
        y_data = y_all[data_mask]

        err_data = None
        if band["err_col"]:
            err_all = numeric_series(df, str(band["err_col"]))
            err_data = err_all[data_mask]

        model_x = None
        model_x_plot = None
        model_y = None
        model_col = str(band["model_col"]) if band["model_col"] else None
        if model_col:
            model_y_all = numeric_series(df, model_col)
            model_x, model_y = extract_paired_series(
                model_x_all, model_y_all, f"Model ({label})"
            )
            model_x_plot, _ = extract_paired_series(
                model_x_plot_all, model_y_all, f"Model ({label})"
            )

        band_states.append(
            {
                "label": label,
                "x_data": x_data,
                "x_data_plot": x_data_plot,
                "y_data": y_data,
                "err_data": err_data,
                "model_x": model_x,
                "model_x_plot": model_x_plot,
                "model_y": model_y,
                "model_col": model_col,
            }
        )

    if args.normalize_mode == "none":
        for state in band_states:
            normalization_meta[str(state["label"])] = {
                "mode": "none",
                "scale": 1.0,
                "offset": 0.0,
            }
            state["norm_scale"] = 1.0
            state["norm_offset"] = 0.0
    else:
        ref_label = str(args.normalize_reference_band)
        ref_state = next((s for s in band_states if s["label"] == ref_label), None)
        if ref_state is None:
            raise SystemExit(f"Normalization reference band not found: {ref_label}")
        for state in band_states:
            label = str(state["label"])
            if label == ref_label:
                state["norm_scale"] = 1.0
                state["norm_offset"] = 0.0
                normalization_meta[label] = {
                    "mode": args.normalize_mode,
                    "source": args.normalize_source,
                    "reference_band": ref_label,
                    "scale": 1.0,
                    "offset": 0.0,
                    "overlap_points": int(np.asarray(state["x_data"]).size),
                }
                continue
            if args.normalize_source == "model":
                if ref_state["model_y"] is None or state["model_y"] is None:
                    raise SystemExit(
                        "Normalization source 'model' requires model columns "
                        "for all normalized bands."
                    )
                target_y, ref_y = overlap_pairs(
                    ref_x=np.asarray(ref_state["model_x"]),
                    ref_y=np.asarray(ref_state["model_y"]),
                    target_x=np.asarray(state["model_x"]),
                    target_y=np.asarray(state["model_y"]),
                    ref_name=f"{ref_label} model",
                    target_name=f"{label} model",
                )
            else:
                target_y, ref_y = overlap_pairs(
                    ref_x=np.asarray(ref_state["x_data"]),
                    ref_y=np.asarray(ref_state["y_data"]),
                    target_x=np.asarray(state["x_data"]),
                    target_y=np.asarray(state["y_data"]),
                    ref_name=f"{ref_label} data",
                    target_name=f"{label} data",
                )
            overlap_n = int(target_y.size)
            if overlap_n < args.normalize_min_overlap:
                raise SystemExit(
                    f"Insufficient overlap for normalization: {label} vs {ref_label} "
                    f"has {overlap_n} points; require >= {args.normalize_min_overlap}."
                )
            scale, offset = fit_normalization(args.normalize_mode, target_y, ref_y)
            state["norm_scale"] = scale
            state["norm_offset"] = offset
            normalization_meta[label] = {
                "mode": args.normalize_mode,
                "source": args.normalize_source,
                "reference_band": ref_label,
                "scale": float(scale),
                "offset": float(offset),
                "overlap_points": overlap_n,
            }

    series = []
    residual_y_label = residual_axis_label(y_kind, y_axis_label)
    if ax_resid is not None:
        ax_resid.axhline(
            0.0,
            color="black",
            lw=graphics_style["reference_linewidth"],
            alpha=0.7,
        )
        ax_resid.set_ylabel(residual_y_label)
        ax_resid.tick_params(direction="in")

    zoom_model_x = None
    zoom_model_y = None
    for idx, state in enumerate(band_states):
        label = str(state["label"])
        norm_meta = normalization_meta[label]
        plotted_data_label = data_series_label(norm_meta, label)
        plotted_model_label = best_fit_series_label(
            args.best_fit_label, label, multi_band
        )
        color = color_for_band_order(label, band_labels)
        marker = markers[idx % len(markers)]
        scale = float(state["norm_scale"])
        offset = float(state["norm_offset"])
        y_data_norm = scale * np.asarray(state["y_data"]) + offset
        state["y_data_norm"] = y_data_norm
        err_data = state["err_data"]
        err_norm = None
        if err_data is not None:
            err_norm = np.abs(scale) * np.asarray(err_data)
            state["err_norm"] = err_norm
        x_data_plot = np.asarray(state["x_data_plot"])

        if err_norm is not None:
            container = ax.errorbar(
                x_data_plot,
                y_data_norm,
                yerr=err_norm,
                fmt=marker,
                ms=graphics_style["marker_size"],
                lw=graphics_style["data_linewidth"],
                elinewidth=graphics_style["data_linewidth"],
                markeredgewidth=graphics_style["data_linewidth"],
                alpha=0.82,
                color=color,
                label=plotted_data_label,
                zorder=2,
            )
            data_line = container.lines[0]
        else:
            (data_line,) = ax.plot(
                x_data_plot,
                y_data_norm,
                marker,
                ms=graphics_style["marker_size"],
                lw=graphics_style["data_linewidth"],
                markeredgewidth=graphics_style["data_linewidth"],
                alpha=0.82,
                color=color,
                label=plotted_data_label,
                zorder=2,
            )
        series.append(
            {
                "name": plotted_data_label,
                "color": data_line.get_color(),
                "marker": data_line.get_marker(),
                "linestyle": data_line.get_linestyle(),
                "alpha": 0.82,
                "linewidth": float(data_line.get_linewidth()),
            }
        )

        if state["model_y"] is not None:
            model_y_norm = scale * np.asarray(state["model_y"]) + offset
            state["model_y_norm"] = model_y_norm
            model_linestyle = "-" if not multi_band else ["-", "--", "-.", ":"][idx % 4]
            model_color = args.model_color if not multi_band else "#1f1f1f"
            (model_line,) = ax.plot(
                np.asarray(state["model_x_plot"]),
                model_y_norm,
                model_linestyle,
                lw=graphics_style["model_linewidth"],
                color=model_color,
                alpha=0.95,
                label=plotted_model_label,
                zorder=8,
            )
            series.append(
                {
                    "name": plotted_model_label,
                    "color": model_line.get_color(),
                    "marker": model_line.get_marker(),
                    "linestyle": model_line.get_linestyle(),
                    "alpha": 0.95,
                    "linewidth": float(model_line.get_linewidth()),
                }
            )
            if ax_resid is not None:
                model_on_data = values_for_x(
                    np.asarray(state["x_data"]),
                    np.asarray(state["model_x"]),
                    model_y_norm,
                    f"Model ({label})",
                )
                residuals = y_data_norm - model_on_data
                resid_mask = np.isfinite(residuals)
                residual_source_by_band[label] = "computed"
                if err_norm is not None:
                    resid_err_mask = resid_mask & np.isfinite(err_norm)
                    if np.any(resid_err_mask):
                        ax_resid.errorbar(
                            x_data_plot[resid_err_mask],
                            residuals[resid_err_mask],
                            yerr=err_norm[resid_err_mask],
                            fmt=marker,
                            ms=graphics_style["residual_marker_size"],
                            lw=graphics_style["residual_linewidth"],
                            elinewidth=graphics_style["residual_linewidth"],
                            markeredgewidth=graphics_style["residual_linewidth"],
                            alpha=0.72,
                            color=color,
                            zorder=4,
                        )
                    no_err_mask = resid_mask & ~np.isfinite(err_norm)
                    if np.any(no_err_mask):
                        ax_resid.plot(
                            x_data_plot[no_err_mask],
                            residuals[no_err_mask],
                            marker,
                            ms=graphics_style["residual_marker_size"],
                            lw=graphics_style["residual_linewidth"],
                            markeredgewidth=graphics_style["residual_linewidth"],
                            alpha=0.72,
                            color=color,
                            zorder=4,
                        )
                else:
                    ax_resid.plot(
                        x_data_plot[resid_mask],
                        residuals[resid_mask],
                        marker,
                        ms=graphics_style["residual_marker_size"],
                        lw=graphics_style["residual_linewidth"],
                        markeredgewidth=graphics_style["residual_linewidth"],
                        alpha=0.72,
                        color=color,
                        zorder=4,
                    )

            ref_ok = (
                args.normalize_reference_band is None
                or label == args.normalize_reference_band
            )
            if zoom_model_x is None and ref_ok:
                zoom_model_x = np.asarray(state["model_x"])
                zoom_model_y = model_y_norm

    if residual_source_by_band:
        if len(residual_source_by_band) == 1 and not multi_band:
            residual_source = next(iter(residual_source_by_band.values()))
        else:
            residual_source = residual_source_by_band

    if args.auto_x_zoom == "trim-baseline":
        if zoom_model_x is None or zoom_model_y is None:
            raise SystemExit("--auto-x-zoom requires at least one model series.")
        baseline_series, baseline_metadata = resolve_baseline_series(
            args=args,
            model_x=zoom_model_x,
            model_y=zoom_model_y,
            model_x_all=model_x_all,
            df=df,
        )
        x_zoom_auto = compute_trim_baseline_window(
            model_x=zoom_model_x,
            model_y=zoom_model_y,
            baseline=baseline_series,
            frac=args.auto_x_zoom_frac,
            pad=args.auto_x_zoom_pad,
        )
    elif args.auto_x_zoom != "none":
        raise SystemExit("--auto-x-zoom requires --model-col.")

    posterior_count = 0
    if not multi_band:
        base_state = band_states[0]
        x_data = np.asarray(base_state["x_data"])
        x_data_plot = np.asarray(base_state["x_data_plot"])
        y_data = np.asarray(base_state["y_data_norm"])
        err_data = (
            np.asarray(base_state["err_norm"])
            if base_state.get("err_norm") is not None
            else None
        )
        model_x = (
            np.asarray(base_state["model_x"])
            if base_state.get("model_x") is not None
            else None
        )

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
                lw=min(args.posterior_linewidth, graphics_style["model_linewidth"]),
                alpha=args.posterior_alpha,
                color=posterior_base_color,
                label=label,
                zorder=7,
            )
            posterior_count += 1
            if has_model and model_x is not None:
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
                    lw=max(
                        graphics_style["residual_linewidth"],
                        min(args.posterior_linewidth, graphics_style["model_linewidth"]) * 0.75,
                    ),
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
                lw=graphics_style["model_linewidth"],
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
            if ax_resid is not None and has_model and model_x is not None:
                require_same_model_cadence(model_x, init_x, "Initial model")
                init_on_data = values_for_x(x_data, init_x, init_y, "Initial model")
                init_resid = y_data - init_on_data
                init_resid_mask = np.isfinite(init_resid)
                ax_resid.plot(
                    x_data_plot[init_resid_mask],
                    init_resid[init_resid_mask],
                    args.initial_model_style,
                    lw=graphics_style["residual_linewidth"],
                    color=args.initial_model_color,
                    alpha=0.6,
                    zorder=3.5,
                )

    validation_warnings: list[str] = []
    tex_policy = str(journal_profile.get("tex_policy", "preferred")) if journal_profile else "preferred"
    if not resolved_tex and tex_policy == "preferred":
        validation_warnings.append(
            "TeX rendering is disabled (--no-tex). For journal publication, TeX text rendering is recommended."
        )
    if resolved_tex and tex_policy == "discouraged":
        validation_warnings.append(
            f"TeX rendering is enabled, but journal profile '{args.journal_profile}' prefers plain text rendering."
        )
    if args.title and args.title.strip():
        validation_warnings.append(
            "Title present. If title does not add clarifying information, prefer a detailed caption instead."
        )
        if journal_profile and bool(journal_profile.get("forbid_figure_title", False)):
            validation_warnings.append(
                f"Title present, but journal profile '{args.journal_profile}' prefers titles in the caption, not the figure."
            )
        legend_labels = [str(item["name"]) for item in series]
        axis_words = token_words(x_axis_label) | token_words(y_axis_label)
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
    if y_kind == "magnitude" and not multi_band:
        y_lower = y_axis_label.lower()
        band_name = str(bands[0]["label"]).strip().lower()
        has_band = bool(band_name and band_name != "data" and band_name in y_lower)
        if not has_band:
            validation_warnings.append(
                "Magnitude y-axis label does not include a filter/band tag "
                "(for example, 'W146 Magnitude (mag)')."
            )
    if used_manual_y_label:
        validation_warnings.append(
            "Manual y-label override used. Prefer structured label inputs: "
            "--y-band, --y-scale, --y-unit."
        )

    ax.set_title(args.title)
    ax.set_xlabel(x_axis_label if ax_resid is None else "")
    ax.set_ylabel(y_axis_label)
    ax.tick_params(direction="in")

    # Standard astronomy convention for magnitude-based plots.
    if mode_for_render == "magnitude":
        ax.invert_yaxis()

    ax.legend(loc="best", fontsize=font_sizes["legend"])
    if vlines:
        trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
        annotation_text_color = "black"
        if not (journal_profile and bool(journal_profile.get("avoid_colored_text", False))):
            annotation_text_color = None
        for entry in vlines:
            entry["text_color"] = annotation_text_color or str(entry["color"])
        for entry in vlines:
            x_val = float(entry["x"])
            x_val_plot = x_val - x_axis_shift
            color = str(entry["color"])
            linestyle = str(entry["linestyle"])
            label = str(entry["label"])
            ax.axvline(
                x_val_plot,
                color=color,
                linestyle=linestyle,
                lw=graphics_style["vline_linewidth"],
                alpha=0.9,
                zorder=9,
            )
            ax.text(
                x_val_plot,
                0.98,
                label,
                transform=trans,
                rotation=90,
                va="top",
                ha="right",
                fontsize=font_sizes["annotation"],
                color=annotation_text_color or color,
                zorder=10,
            )
            if ax_resid is not None:
                ax_resid.axvline(
                    x_val_plot,
                    color=color,
                    linestyle=linestyle,
                    lw=graphics_style["residual_linewidth"],
                    alpha=0.7,
                    zorder=5,
                )

    if ax_resid is not None:
        ax_resid.set_xlabel(x_axis_label)

    x_zoom_source = "none"
    x_zoom_active = None
    if x_zoom_manual is not None:
        x_zoom_active = x_zoom_manual
        x_zoom_source = "manual"
    elif x_zoom_auto is not None:
        x_zoom_active = x_zoom_auto
        x_zoom_source = "auto-trim-baseline"
    if x_zoom_active is not None:
        x_min, x_max = x_zoom_active
        x_min_plot = x_min - x_axis_shift
        x_max_plot = x_max - x_axis_shift
        ax.set_xlim(x_min_plot, x_max_plot)
        if ax_resid is not None:
            ax_resid.set_xlim(x_min_plot, x_max_plot)

    fig.tight_layout()

    output_stem = Path(args.output)
    pdf_path = output_stem.with_suffix(".pdf")
    png_path = output_stem.with_suffix(".png")

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
            "journal_profile": args.journal_profile,
            "paper_span": args.paper_span,
            "figure_width_in": figure_geometry["width_in"],
            "figure_height_in": figure_geometry["height_in"],
            "font_family": resolved_font_family,
            "font_sizes_pt": font_sizes,
            "graphics_style_pt": graphics_style,
            "mode": mode_for_render,
            "y_kind": y_kind,
            "policy_profile": "strict",
            "postprocess_customized": False,
            "multi_band": bool(multi_band),
            "band_labels": [str(b["label"]) for b in bands],
            "normalization_mode": args.normalize_mode,
            "normalization_reference_band": args.normalize_reference_band,
            "normalization_source": args.normalize_source,
            "normalization": normalization_meta,
            "tex_enabled": bool(resolved_tex),
            "has_residual_panel": bool(has_model or posterior_cols or has_initial_model),
            "has_initial_model_overlay": bool(has_initial_model),
            "posterior_overlay": bool(posterior_count > 0),
            "posterior_sample_count": int(posterior_count),
            "model_x_column": args.model_x_col,
            "x_axis_shift": x_axis_shift,
            "x_zoom_source": x_zoom_source,
            "x_zoom_range": list(x_zoom_active) if x_zoom_active else None,
            "auto_x_zoom": args.auto_x_zoom,
            "auto_x_zoom_frac": args.auto_x_zoom_frac,
            "auto_x_zoom_pad": args.auto_x_zoom_pad,
            "baseline": baseline_metadata,
            "residual_source": residual_source if has_model else "none",
            "vertical_annotations": vlines,
            "labels": {"x": x_axis_label, "y": y_axis_label},
            "residual_y_label": residual_y_label,
            "labels_include_units": ("(" in x_axis_label and ")" in x_axis_label)
            and ("(" in y_axis_label and ")" in y_axis_label),
        },
        "exports": [
            {"format": "pdf", "path": str(pdf_path.resolve())},
            {"format": "png", "path": str(png_path.resolve()), "dpi": 300},
        ],
        "series": series,
        "provenance": {"input": str(Path(args.input).resolve())},
        "validation": {"required_columns": True, "warnings": validation_warnings},
    }
    return fig, manifest


def write_outputs(fig: plt.Figure, manifest: dict, args: argparse.Namespace) -> None:
    output_stem = Path(args.output)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = output_stem.with_suffix(".pdf")
    png_path = output_stem.with_suffix(".png")
    manifest_path = (
        Path(args.manifest_output)
        if args.manifest_output
        else output_stem.with_suffix(".meta.json")
    )
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))

    for warning in manifest.get("validation", {}).get("warnings", []):
        print(f"Warning: {warning}")
    print(f"Saved: {pdf_path}")
    print(f"Saved: {png_path}")
    print(f"Saved: {manifest_path}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    fig, manifest = render_lightcurve(args)
    write_outputs(fig, manifest, args)


if __name__ == "__main__":
    main()
