#!/usr/bin/env python3
"""Render the same multiband event under multiple journal profiles."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


def load_example_module():
    repo_root = Path(__file__).resolve().parents[5]
    module_path = (
        repo_root
        / "skills"
        / "plotting"
        / "plot-types"
        / "lightcurve-residuals"
        / "examples"
        / "customize_multiband_event.py"
    )
    spec = importlib.util.spec_from_file_location("customize_multiband_event", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_profile(mod, profile: str, paper_span: str, out_stem: Path) -> None:
    csv_path = out_stem.parent / "journal_profile_gallery.csv"
    mod.build_multiband_event(csv_path)
    roman = mod.load_roman_plot_module()
    argv = [
        "--input",
        str(csv_path),
        "--output",
        str(out_stem),
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
        profile,
        "--paper-span",
        paper_span,
        "--y-scale",
        "Normalized",
        "--y-unit",
        "mag",
        "--x-var",
        "Time",
        "--x-unit",
        "days",
    ]
    args = roman.parse_args(argv)
    fig, manifest = roman.render_lightcurve(args)
    journal_profiles = roman.load_journal_profiles()
    profile_spec = journal_profiles.get(profile, {})
    avoid_gridlines = bool(profile_spec.get("avoid_gridlines", False))
    avoid_minor_ticks = bool(profile_spec.get("avoid_minor_ticks", False))
    for axis in fig.axes:
        if avoid_gridlines:
            axis.grid(False, which="both")
        else:
            axis.grid(True, which="major", alpha=0.24, linestyle="--")
        if avoid_minor_ticks:
            axis.minorticks_off()
        else:
            axis.minorticks_on()
        if not avoid_gridlines and not avoid_minor_ticks:
            axis.grid(True, which="minor", alpha=0.10, linestyle=":")
    manifest["figure"]["postprocess_customized"] = True
    manifest["figure"]["policy_profile"] = "customized-from-strict"
    manifest["figure"]["gridlines_enabled"] = not avoid_gridlines
    manifest["figure"]["minor_ticks_enabled"] = not avoid_minor_ticks
    customizations: list[str] = []
    if not avoid_gridlines:
        customizations.append("gridlines")
    if not avoid_minor_ticks:
        customizations.append("minor ticks")
    if customizations:
        manifest["validation"]["warnings"].append(
            "Post-processing customization applied: " + ", ".join(customizations) + "."
        )
    roman.write_outputs(fig, manifest, args)


def run_style_check(repo_root: Path, profile: str, metadata_path: Path, output_path: Path) -> None:
    script = (
        repo_root
        / "skills"
        / "plotting"
        / "style-profiles"
        / "scripts"
        / "check_style_profile.py"
    )
    subprocess.run(
        [
            "python",
            str(script),
            "--metadata",
            str(metadata_path),
            "--profile",
            profile,
            "--output",
            str(output_path),
        ],
        check=True,
        cwd=repo_root,
    )


def main() -> None:
    mod = load_example_module()
    repo_root = Path(__file__).resolve().parents[5]
    out_dir = repo_root / "tmp" / "examples" / "journal-profile-gallery"
    out_dir.mkdir(parents=True, exist_ok=True)

    profiles = [
        ("apj", "single"),
        ("apj", "double"),
        ("nature-initial", "single"),
        ("nature-initial", "double"),
        ("nature-revised", "single"),
        ("nature-revised", "double"),
        ("science", "single"),
        ("science", "double"),
        ("mnras", "single"),
        ("mnras", "double"),
    ]

    for profile, span in profiles:
        stem = out_dir / f"multiband_{profile}_{span}"
        run_profile(mod, profile, span, stem)
        run_style_check(
            repo_root=repo_root,
            profile=profile,
            metadata_path=stem.with_suffix(".meta.json"),
            output_path=stem.with_suffix(".style.json"),
        )


if __name__ == "__main__":
    main()
