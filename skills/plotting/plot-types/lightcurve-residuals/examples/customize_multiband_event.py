#!/usr/bin/env python3
"""Example: multiband strict render + controlled post-processing customization."""

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


def gaussian_event(t: np.ndarray, center: float, width: float) -> np.ndarray:
    return np.exp(-((t - center) ** 2) / (2.0 * width**2))


def build_multiband_event(csv_path: Path) -> None:
    t = np.linspace(0.0, 140.0, 620)
    event = gaussian_event(t, center=72.0, width=10.0)
    shoulder = gaussian_event(t, center=92.0, width=4.0)

    w146_model = 19.10 - 0.92 * event - 0.10 * shoulder
    z087_model = 19.95 - 0.66 * event - 0.06 * shoulder
    f184_model = 18.55 - 0.48 * event - 0.14 * shoulder

    w146_mag = w146_model + 0.010 * np.sin(t / 2.3)
    z087_mag = z087_model + 0.014 * np.sin(t / 2.9 + 0.6)
    f184_mag = f184_model + 0.012 * np.cos(t / 2.6 - 0.4)

    df = pd.DataFrame(
        {
            "time": t,
            "w146_mag": w146_mag,
            "w146_err": np.full_like(t, 0.018),
            "w146_model": w146_model,
            "z087_mag": z087_mag,
            "z087_err": np.full_like(t, 0.022),
            "z087_model": z087_model,
            "f184_mag": f184_mag,
            "f184_err": np.full_like(t, 0.020),
            "f184_model": f184_model,
        }
    )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)


def main() -> None:
    mod = load_roman_plot_module()
    out_dir = Path("tmp/examples")
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "multiband_event.csv"
    build_multiband_event(csv_path)

    argv = [
        "--input",
        str(csv_path),
        "--output",
        str(out_dir / "custom_multiband_event"),
        "--x-col",
        "time",
        "--y-col",
        "w146_mag",
        "--band-label",
        "W146",
        "--err-col",
        "w146_err",
        "--model-x-col",
        "time",
        "--model-col",
        "w146_model",
        "--band-spec",
        "Z087,z087_mag,z087_err,time,z087_model,magnitude",
        "--band-spec",
        "F184,f184_mag,f184_err,time,f184_model,magnitude",
        "--y-kind",
        "magnitude",
        "--normalize-mode",
        "additive",
        "--normalize-reference-band",
        "W146",
        "--normalize-source",
        "model",
        "--auto-x-zoom",
        "trim-baseline",
        "--journal-profile",
        "science",
        "--paper-span",
        "double",
        "--y-scale",
        "Normalized",
        "--y-unit",
        "mag",
        "--x-var",
        "Time",
        "--x-unit",
        "days",
    ]
    args = mod.parse_args(argv)
    fig, manifest = mod.render_lightcurve(args)

    for axis in fig.axes:
        axis.grid(True, which="major", alpha=0.24, linestyle="--")
        axis.minorticks_on()
        axis.grid(True, which="minor", alpha=0.10, linestyle=":")

    manifest["figure"]["postprocess_customized"] = True
    manifest["figure"]["policy_profile"] = "customized-from-strict"
    manifest["validation"]["warnings"].append(
        "Post-processing customization applied: gridlines."
    )

    mod.write_outputs(fig, manifest, args)


if __name__ == "__main__":
    main()
