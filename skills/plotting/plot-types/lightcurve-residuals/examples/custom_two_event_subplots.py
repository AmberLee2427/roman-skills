#!/usr/bin/env python3
"""Example: build a two-lightcurve subplot figure from strict renders.

Workflow:
1) Generate two synthetic event CSVs.
2) Render each event with strict renderer.
3) Apply per-event custom styling.
4) Save each customized event output.
5) Compose a 2-row subplot figure by embedding each rendered figure image.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import numpy as np
import pandas as pd
from PIL import Image


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


def render_custom_event(mod, csv_path: Path, out_stem: Path, title: str):
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
    fig, manifest = mod.render_lightcurve(args)

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

    mod.write_outputs(fig, manifest, args)
    return out_stem.with_suffix(".png")


def compose_vertical_png(
    image_paths: list[Path],
    out_png: Path,
    out_pdf: Path,
    dpi: int = 300,
) -> None:
    images = [Image.open(p).convert("RGB") for p in image_paths]
    widths = [img.width for img in images]
    heights = [img.height for img in images]
    max_width = max(widths)
    total_height = sum(heights)

    canvas = Image.new("RGB", (max_width, total_height), color=(255, 255, 255))
    y = 0
    for img in images:
        x = (max_width - img.width) // 2
        canvas.paste(img, (x, y))
        y += img.height

    out_png.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_png, dpi=(dpi, dpi))
    canvas.save(out_pdf, resolution=dpi)


def main() -> None:
    mod = load_roman_plot_module()
    out_dir = Path("tmp/examples")
    out_dir.mkdir(parents=True, exist_ok=True)

    event_a_csv = out_dir / "event_a.csv"
    event_b_csv = out_dir / "event_b.csv"
    build_event(event_a_csv, center=52.0, depth=0.85, width=7.5)
    build_event(event_b_csv, center=80.0, depth=0.55, width=10.0)

    png_a = render_custom_event(
        mod=mod,
        csv_path=event_a_csv,
        out_stem=out_dir / "event_a_custom",
        title="Event A",
    )
    png_b = render_custom_event(
        mod=mod,
        csv_path=event_b_csv,
        out_stem=out_dir / "event_b_custom",
        title="Event B",
    )

    combo_pdf = out_dir / "two_events_subplots.pdf"
    combo_png = out_dir / "two_events_subplots.png"
    compose_vertical_png(
        [png_a, png_b],
        combo_png,
        combo_pdf,
        dpi=300,
    )

    print(f"Saved: {combo_pdf}")
    print(f"Saved: {combo_png}")


if __name__ == "__main__":
    main()
