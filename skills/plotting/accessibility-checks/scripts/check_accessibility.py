#!/usr/bin/env python3
"""Check plotting metadata for accessibility signals."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check figure accessibility")
    p.add_argument("--metadata", required=True, help="Input metadata JSON path")
    p.add_argument("--output", required=True, help="Output report JSON path")
    p.add_argument("--min-rgb-distance", type=float, default=60.0)
    p.add_argument("--min-luminance-distance", type=float, default=30.0)
    return p.parse_args()


def parse_hex_color(raw: str) -> tuple[int, int, int] | None:
    text = str(raw).strip()
    if text.startswith("#") and len(text) == 7:
        try:
            return int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16)
        except ValueError:
            return None
    return None


def rgb_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def main() -> None:
    args = parse_args()
    out = Path(args.output)
    meta_path = Path(args.metadata)

    if not meta_path.exists():
        report = {
            "status": "error",
            "summary": f"Metadata file not found: {meta_path}",
            "artifacts": [str(out.resolve())],
            "validation": {"metadata_exists": False},
            "provenance": {"metadata": str(meta_path.resolve())},
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        raise SystemExit(2)

    metadata = json.loads(meta_path.read_text())
    series = metadata.get("series", [])

    if len(series) < 2:
        report = {
            "status": "warning",
            "summary": "Fewer than two series; distinguishability checks are not informative",
            "artifacts": [str(out.resolve())],
            "validation": {
                "metadata_exists": True,
                "enough_series_for_pairwise_checks": False,
            },
            "provenance": {
                "metadata": str(meta_path.resolve()),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        print(f"Saved accessibility report: {out}")
        return

    pair_results = []
    marker_or_style_distinguishable = True
    color_distinguishable = True
    grayscale_distinguishable = True

    for i in range(len(series)):
        for j in range(i + 1, len(series)):
            a = series[i]
            b = series[j]

            a_marker = str(a.get("marker", ""))
            b_marker = str(b.get("marker", ""))
            a_style = str(a.get("linestyle", ""))
            b_style = str(b.get("linestyle", ""))
            marker_style_ok = (a_marker != b_marker) or (a_style != b_style)
            marker_or_style_distinguishable &= marker_style_ok

            a_rgb = parse_hex_color(a.get("color"))
            b_rgb = parse_hex_color(b.get("color"))
            rgb_ok = False
            lum_ok = False
            rgb_dist = None
            lum_dist = None
            if a_rgb is not None and b_rgb is not None:
                rgb_dist = rgb_distance(a_rgb, b_rgb)
                rgb_ok = rgb_dist >= args.min_rgb_distance
                color_distinguishable &= rgb_ok

                lum_dist = abs(luminance(a_rgb) - luminance(b_rgb))
                lum_ok = lum_dist >= args.min_luminance_distance
                grayscale_distinguishable &= lum_ok

            pair_results.append(
                {
                    "series_a": a.get("name", f"series_{i}"),
                    "series_b": b.get("name", f"series_{j}"),
                    "marker_or_style_distinguishable": marker_style_ok,
                    "rgb_distance": rgb_dist,
                    "rgb_distinguishable": rgb_ok,
                    "luminance_distance": lum_dist,
                    "grayscale_distinguishable": lum_ok,
                }
            )

    checks = {
        "metadata_exists": True,
        "enough_series_for_pairwise_checks": True,
        "marker_or_style_distinguishable": marker_or_style_distinguishable,
        "color_distinguishable": color_distinguishable,
        "grayscale_distinguishable": grayscale_distinguishable,
    }
    failing = [k for k, ok in checks.items() if not ok]
    status = "ok" if not failing else "warning"

    report = {
        "status": status,
        "summary": "Accessibility checks passed" if status == "ok" else "Accessibility checks reported warnings",
        "artifacts": [str(out.resolve())],
        "validation": checks,
        "pairwise": pair_results,
        "provenance": {
            "metadata": str(meta_path.resolve()),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"Saved accessibility report: {out}")


if __name__ == "__main__":
    main()
