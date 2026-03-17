#!/usr/bin/env python3
"""Validate plot metadata against journal-style profile rules."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path


PROFILES = {"apj", "mnras", "aanda"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check figure metadata style profile")
    p.add_argument("--metadata", required=True, help="Input metadata JSON path")
    p.add_argument("--profile", required=True, choices=sorted(PROFILES))
    p.add_argument("--output", required=True, help="Output report JSON path")
    return p.parse_args()


def has_vector_export(exports: list[dict]) -> bool:
    return any(e.get("format") in {"pdf", "svg"} for e in exports)


def has_png_300(exports: list[dict]) -> bool:
    return any(e.get("format") == "png" and int(e.get("dpi", 0)) >= 300 for e in exports)


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
    colors = [parse_hex_color(s.get("color")) for s in series]
    colors = [c for c in colors if c is not None]
    if len(colors) < 2:
        return True
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            if math.fabs(luminance(colors[i]) - luminance(colors[j])) < min_lum_distance:
                return False
    return True


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
        "vector_export": has_vector_export(exports),
        "png_dpi_ge_300": has_png_300(exports),
        "labels_include_units": labels_have_units(labels),
    }

    if args.profile in {"apj", "mnras"}:
        checks["tex_enabled"] = bool(figure.get("tex_enabled", False))
    if args.profile == "mnras":
        checks["grayscale_distinguishable"] = grayscale_distinguishable(series)

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
