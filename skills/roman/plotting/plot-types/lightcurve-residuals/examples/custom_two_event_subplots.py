#!/usr/bin/env python3
"""Example: build a two-lightcurve subplot figure from strict renders.

Workflow:
1) Generate two synthetic event CSVs.
2) Render each event into a shared Matplotlib figure.
3) Apply per-event custom styling.
4) Save each customized event output.
5) Save a vector-native 2-row subplot figure.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
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


def build_event(csv_path: Path, center: float, depth: float, width: float) -> None:
    t = np.linspace(0.0, 140.0, 620)
    main = depth * np.exp(-((t - center) ** 2) / (2.0 * width**2))
    bump = 0.18 * np.exp(-((t - (center + 20.0)) ** 2) / (2.0 * 3.5**2))
    model = 18.3 - main - bump
    y = model + 0.012 * np.sin(t / 2.1)
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


def render_custom_event(
    mod,
    csv_path: Path,
    out_stem: Path,
    title: str,
    target_axes=None,
    apply_layout: bool = True,
    save_outputs: bool = True,
):
    argv = [
        "--input",
        str(csv_path),
        "--output",
        str(out_stem),
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
        "--title",
        title,
    ]
    args = mod.parse_args(argv)
    fig, manifest = mod.render_lightcurve(
        args,
        target_axes=target_axes,
        apply_layout=apply_layout,
    )

    for axis in fig.axes:
        axis.grid(True, which="major", alpha=0.24, linestyle="--")
        axis.minorticks_on()
        axis.grid(True, which="minor", alpha=0.1, linestyle=":")

    manifest["figure"]["postprocess_customized"] = True
    manifest["figure"]["policy_profile"] = "customized-from-strict"
    manifest["figure"]["gridlines_enabled"] = True
    manifest["figure"]["minor_ticks_enabled"] = True
    manifest["validation"]["warnings"].append(
        "Post-processing customization applied: gridlines."
    )

    if save_outputs:
        mod.write_outputs(fig, manifest, args)
    return fig, manifest


def main() -> None:
    mod = load_roman_plot_module()
    out_dir = Path("tmp/examples")
    out_dir.mkdir(parents=True, exist_ok=True)

    event_a_csv = out_dir / "event_a.csv"
    event_b_csv = out_dir / "event_b.csv"
    build_event(event_a_csv, center=52.0, depth=0.85, width=7.5)
    build_event(event_b_csv, center=80.0, depth=0.55, width=10.0)

    render_custom_event(
        mod=mod,
        csv_path=event_a_csv,
        out_stem=out_dir / "event_a_custom",
        title="Event A",
    )
    render_custom_event(
        mod=mod,
        csv_path=event_b_csv,
        out_stem=out_dir / "event_b_custom",
        title="Event B",
    )

    combo_fig = plt.figure(figsize=(6.8, 8.6))
    gs = combo_fig.add_gridspec(
        4,
        1,
        height_ratios=[3, 1, 3, 1],
        hspace=0.08,
    )
    ax_a = combo_fig.add_subplot(gs[0])
    ax_a_resid = combo_fig.add_subplot(gs[1], sharex=ax_a)
    ax_b = combo_fig.add_subplot(gs[2])
    ax_b_resid = combo_fig.add_subplot(gs[3], sharex=ax_b)

    render_custom_event(
        mod=mod,
        csv_path=event_a_csv,
        out_stem=out_dir / "two_events_subplots_event_a",
        title="Event A",
        target_axes=(ax_a, ax_a_resid),
        apply_layout=False,
        save_outputs=False,
    )
    render_custom_event(
        mod=mod,
        csv_path=event_b_csv,
        out_stem=out_dir / "two_events_subplots_event_b",
        title="Event B",
        target_axes=(ax_b, ax_b_resid),
        apply_layout=False,
        save_outputs=False,
    )

    for axis in (ax_a, ax_b):
        axis.tick_params(labelbottom=False)

    combo_fig.align_ylabels((ax_a, ax_a_resid, ax_b, ax_b_resid))
    combo_fig.subplots_adjust(
        left=0.12,
        right=0.97,
        top=0.97,
        bottom=0.08,
        hspace=0.12,
    )
    combo_pdf = out_dir / "two_events_subplots.pdf"
    combo_png = out_dir / "two_events_subplots.png"
    combo_fig.savefig(combo_pdf)
    combo_fig.savefig(combo_png, dpi=300)
    plt.close(combo_fig)

    print(f"Saved: {combo_pdf}")
    print(f"Saved: {combo_png}")


if __name__ == "__main__":
    main()
