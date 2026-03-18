#!/usr/bin/env python3
"""Validate plot metadata against journal-style profile rules."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

PROFILES_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "journal_profiles.json"
)


def load_profiles() -> dict[str, dict[str, object]]:
    if not PROFILES_PATH.exists():
        raise SystemExit(f"Style profiles file not found: {PROFILES_PATH}")
    return json.loads(PROFILES_PATH.read_text())


def parse_args() -> argparse.Namespace:
    profiles = load_profiles()
    p = argparse.ArgumentParser(description="Check figure metadata style profile")
    p.add_argument("--metadata", required=True, help="Input metadata JSON path")
    p.add_argument("--profile", required=True, choices=sorted(profiles))
    p.add_argument("--output", required=True, help="Output report JSON path")
    return p.parse_args()


def has_vector_export(exports: list[dict]) -> bool:
    return any(e.get("format") in {"pdf", "eps", "svg"} for e in exports)


def has_preferred_vector_format(exports: list[dict], preferred_formats: list[str]) -> bool:
    preferred = {fmt.lower() for fmt in preferred_formats}
    return any(str(e.get("format", "")).lower() in preferred for e in exports)


def has_png_min_dpi(exports: list[dict], min_dpi: int) -> bool:
    return any(e.get("format") == "png" and int(e.get("dpi", 0)) >= min_dpi for e in exports)


def labels_have_units(labels: dict) -> bool:
    x = str(labels.get("x", ""))
    y = str(labels.get("y", ""))
    return ("(" in x and ")" in x) and ("(" in y and ")" in y)


def parse_hex_color(raw: str) -> tuple[int, int, int] | None:
    text = str(raw).strip()
    if text.startswith("#") and len(text) == 7:
        try:
            return int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16)
        except ValueError:
            return None
    return None


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def grayscale_distinguishable(series: list[dict], min_lum_distance: float = 30.0) -> bool:
    parsed = []
    for item in series:
        color = parse_hex_color(item.get("color"))
        if color is None:
            continue
        parsed.append(
            {
                "color": color,
                "marker": str(item.get("marker", "")),
                "linestyle": str(item.get("linestyle", "")),
            }
        )
    if len(parsed) < 2:
        return True
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            lum_close = (
                math.fabs(luminance(parsed[i]["color"]) - luminance(parsed[j]["color"]))
                < min_lum_distance
            )
            if not lum_close:
                continue
            if (
                parsed[i]["marker"] != parsed[j]["marker"]
                or parsed[i]["linestyle"] != parsed[j]["linestyle"]
            ):
                continue
            return False
    return True


def width_matches_profile(
    figure: dict,
    profile: dict[str, object],
    tolerance_in: float = 0.12,
) -> bool | None:
    paper_span = figure.get("paper_span")
    width = figure.get("figure_width_in")
    profile_widths = profile.get("paper_width_in", {})
    if not isinstance(profile_widths, dict) or paper_span not in profile_widths or width is None:
        return None
    expected = float(profile_widths[str(paper_span)])
    return abs(float(width) - expected) <= tolerance_in


def font_sizes_within_profile(figure: dict, profile: dict[str, object]) -> bool | None:
    font_sizes = figure.get("font_sizes_pt")
    if not isinstance(font_sizes, dict):
        return None
    min_font = profile.get("min_font_pt")
    max_font = profile.get("max_font_pt")
    values = [float(v) for v in font_sizes.values()]
    if not values:
        return None
    if min_font is not None and min(values) < float(min_font):
        return False
    if max_font is not None and max(values) > float(max_font):
        return False
    return True


def series_linewidths_within_profile(
    series: list[dict],
    profile: dict[str, object],
) -> bool | None:
    min_width = profile.get("min_line_width_pt")
    max_width = profile.get("max_line_width_pt")
    widths = [float(s.get("linewidth")) for s in series if s.get("linewidth") is not None]
    if not widths:
        return None
    if min_width is not None and min(widths) < float(min_width):
        return False
    if max_width is not None and max(widths) > float(max_width):
        return False
    return True


def title_allowed(figure: dict, profile: dict[str, object]) -> bool:
    if not bool(profile.get("forbid_figure_title", False)):
        return True
    return not bool(str(figure.get("title", "")).strip())


def no_colored_annotation_text(figure: dict) -> bool:
    annotations = figure.get("vertical_annotations", [])
    if not isinstance(annotations, list):
        return True
    for item in annotations:
        if not isinstance(item, dict):
            continue
        text_color = str(item.get("text_color", "")).strip().lower()
        if text_color and text_color not in {"black", "#000000"}:
            return False
    return True


def marker_or_style_distinguishable(series: list[dict]) -> bool:
    for i in range(len(series)):
        for j in range(i + 1, len(series)):
            a = series[i]
            b = series[j]
            if str(a.get("marker", "")) == str(b.get("marker", "")) and str(a.get("linestyle", "")) == str(b.get("linestyle", "")):
                return False
    return True


def gridlines_disabled(figure: dict) -> bool:
    return not bool(figure.get("gridlines_enabled", False))


def minor_ticks_disabled(figure: dict) -> bool:
    return not bool(figure.get("minor_ticks_enabled", False))


def main() -> None:
    args = parse_args()
    profiles = load_profiles()
    profile = profiles[args.profile]
    out = Path(args.output)

    meta_path = Path(args.metadata)
    if not meta_path.exists():
        report = {
            "status": "error",
            "summary": f"Metadata file not found: {meta_path}",
            "artifacts": [str(out.resolve())],
            "validation": {"metadata_exists": False},
            "provenance": {"metadata": str(meta_path.resolve()), "profile": args.profile},
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    metadata = json.loads(meta_path.read_text())
    exports = metadata.get("exports", [])
    figure = metadata.get("figure", {})
    labels = figure.get("labels", {})
    series = metadata.get("series", [])

    checks = {
        "metadata_exists": True,
        "vector_export": has_vector_export(exports)
        if bool(profile.get("require_vector_export", True))
        else True,
        "png_dpi_min": has_png_min_dpi(exports, int(profile.get("min_png_dpi", 300))),
        "labels_include_units": labels_have_units(labels)
        if bool(profile.get("require_units", True))
        else True,
    }
    preferred_vector_formats = profile.get("preferred_vector_formats", [])
    if isinstance(preferred_vector_formats, list) and preferred_vector_formats:
        checks["preferred_vector_format_present"] = has_preferred_vector_format(
            exports, [str(item) for item in preferred_vector_formats]
        )

    tex_policy = str(profile.get("tex_policy", "none"))
    if tex_policy == "preferred":
        checks["tex_enabled"] = bool(figure.get("tex_enabled", False))
    elif tex_policy == "discouraged":
        checks["tex_disabled"] = not bool(figure.get("tex_enabled", False))

    font_family = str(figure.get("font_family", "")).strip().lower()
    expected_family = str(profile.get("font_family", "")).strip().lower()
    if expected_family:
        checks["font_family_matches"] = font_family == expected_family

    width_ok = width_matches_profile(figure, profile)
    if width_ok is not None:
        checks["paper_width_matches_profile"] = width_ok

    font_ok = font_sizes_within_profile(figure, profile)
    if font_ok is not None:
        checks["font_sizes_within_profile"] = font_ok

    linewidth_ok = series_linewidths_within_profile(series, profile)
    if linewidth_ok is not None:
        checks["line_widths_within_profile"] = linewidth_ok

    if bool(profile.get("grayscale_distinguishable", False)):
        checks["grayscale_distinguishable"] = grayscale_distinguishable(series)
    if bool(profile.get("avoid_colored_text", False)):
        checks["annotation_text_neutral"] = no_colored_annotation_text(figure)
    if bool(profile.get("avoid_gridlines", False)):
        checks["gridlines_disabled"] = gridlines_disabled(figure)
    if bool(profile.get("avoid_minor_ticks", False)):
        checks["minor_ticks_disabled"] = minor_ticks_disabled(figure)
    if bool(profile.get("require_marker_or_style_redundancy", False)):
        checks["marker_or_style_redundancy"] = marker_or_style_distinguishable(series)
    if bool(profile.get("forbid_figure_title", False)):
        checks["figure_title_absent"] = title_allowed(figure, profile)

    failing = [k for k, ok in checks.items() if not ok]
    status = "ok" if not failing else "warning"

    report = {
        "status": status,
        "summary": "Style profile checks passed" if status == "ok" else "Style profile checks reported warnings",
        "artifacts": [str(out.resolve())],
        "profile": args.profile,
        "validation": checks,
        "warnings": failing,
        "provenance": {
            "metadata": str(meta_path.resolve()),
            "profile": args.profile,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved style report: {out}")


if __name__ == "__main__":
    main()
