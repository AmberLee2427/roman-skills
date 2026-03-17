#!/usr/bin/env python3
"""Example: strict render + controlled post-processing customization.

This script demonstrates how to:
1) Generate a synthetic event dataset.
2) Render with strict skill defaults via render_lightcurve().
3) Apply local style customizations (grid lines, annotation).
4) Mark manifest policy as customized.
5) Save outputs with write_outputs().
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


def load_roman_plot_module():
    repo_root = Path(__file__).resolve().parents[5]
    module_path = (
        repo_root
        / "skills"
        / "plotting"
        / "plot-types"
        / "lightcurve-residuals"
        / "scripts"
        / "roman_plot.py"
    )
    spec = importlib.util.spec_from_file_location("roman_plot_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_synthetic_event(csv_path: Path) -> None:
    t = np.linspace(0.0, 120.0, 500)
    model = 18.2 - 0.75 * np.exp(-((t - 58.0) ** 2) / (2.0 * 8.0**2))
    noise = 0.015 * np.sin(t / 2.4)
    y = model + noise
    yerr = np.full_like(t, 0.02)
    df = pd.DataFrame(
        {
            "time": t,
            "magnitude": y,
            "magnitude_err": yerr,
            "model_magnitude": model,
        }
    )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)


def main() -> None:
    mod = load_roman_plot_module()
    out_dir = Path("tmp/examples")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "single_event.csv"
    build_synthetic_event(csv_path)

    argv = [
        "--input",
        str(csv_path),
        "--output",
        str(out_dir / "custom_single_event"),
        "--x-col",
        "time",
        "--y-col",
        "magnitude",
        "--band-label",
        "W146",
        "--err-col",
        "magnitude_err",
        "--model-x-col",
        "time",
        "--model-col",
        "model_magnitude",
        "--y-kind",
        "magnitude",
        "--auto-x-zoom",
        "trim-baseline",
        "--y-band",
        "W146",
        "--y-unit",
        "mag",
        "--x-var",
        "Time",
        "--x-unit",
        "days",
    ]
    args = mod.parse_args(argv)
    fig, manifest = mod.render_lightcurve(args)

    # Customization layer (example): enable major/minor grids.
    for axis in fig.axes:
        axis.grid(True, which="major", alpha=0.28, linestyle=":")
        axis.grid(True, which="minor", alpha=0.12, linestyle=":")
        axis.minorticks_on()

    # Mark manifest as customized so downstream users know strict style was altered.
    manifest["figure"]["postprocess_customized"] = True
    manifest["figure"]["policy_profile"] = "customized-from-strict"
    manifest["validation"]["warnings"].append(
        "Post-processing customization applied: gridlines."
    )

    mod.write_outputs(fig, manifest, args)


if __name__ == "__main__":
    main()
