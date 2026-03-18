#!/usr/bin/env python3
"""Check plotting accessibility using accessiplot plus visibility checks."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

try:
    from accessiplot.detection import color_detection
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'accessiplot'. Install with: pip install -r requirements.txt"
    ) from exc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check figure accessibility")
    p.add_argument("--metadata", required=True, help="Input metadata JSON path")
    p.add_argument("--output", required=True, help="Output report JSON path")
    p.add_argument("--min-alpha", type=float, default=0.2)
    p.add_argument("--min-linewidth", type=float, default=0.8)
    return p.parse_args()


def find_png_export(metadata: dict) -> str | None:
    exports = metadata.get("exports", [])
    for item in exports:
        if item.get("format") == "png":
            path = item.get("path")
            if path and Path(path).exists():
                return str(path)
    return None


def normalize_compare_result(result: object) -> tuple[bool | None, str]:
    if isinstance(result, bool):
        # compare_colors checks whether colors are too similar.
        # True is interpreted as conflict found.
        return (not result), str(result)
    if isinstance(result, (list, tuple, set)):
        return (len(result) == 0), repr(result)
    if isinstance(result, dict):
        for key in ["too_similar", "has_conflict", "conflict", "accessible", "pass"]:
            if key in result and isinstance(result[key], bool):
                if key in {"accessible", "pass"}:
                    return result[key], repr(result)
                return (not result[key]), repr(result)
        return None, repr(result)
    if isinstance(result, (int, float)):
        return (result == 0), str(result)
    return None, repr(result)


def compare_with_accessiplot(
    colors: object, deficiency: str
) -> tuple[bool | None, str]:
    attempts = [
        lambda: color_detection.compare_colors(colors, deficiency),
        lambda: color_detection.compare_colors(colors, cvd_type=deficiency),
        lambda: color_detection.compare_colors(colors, deficiency_type=deficiency),
        lambda: color_detection.compare_colors(colors, colorblind_type=deficiency),
        lambda: color_detection.compare_colors(colors),
    ]

    last_exc: Exception | None = None
    for attempt in attempts:
        try:
            raw = attempt()
            decision, raw_repr = normalize_compare_result(raw)
            return decision, raw_repr
        except TypeError as exc:
            last_exc = exc
            continue
        except Exception as exc:  # pragma: no cover - defensive parsing
            last_exc = exc
            break

    return None, f"compare_failed: {last_exc}"


def to_builtin(value: object) -> object:
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_builtin(v) for v in value]
    return value


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
    png_path = find_png_export(metadata)

    if not png_path:
        report = {
            "status": "warning",
            "summary": "No PNG export found in metadata; accessiplot color checks skipped",
            "artifacts": [str(out.resolve())],
            "validation": {
                "metadata_exists": True,
                "png_export_available": False,
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

    common_colors = color_detection.get_common_colors_from_image(png_path)
    deficiencies = ["deuteranomaly", "protanomaly", "tritanomaly"]
    accessiplot_results = {}
    accessiplot_pass = True
    for deficiency in deficiencies:
        passed, raw = compare_with_accessiplot(common_colors, deficiency)
        accessiplot_results[deficiency] = {
            "passed": passed,
            "raw": raw,
        }
        if passed is False:
            accessiplot_pass = False

    pair_results = []
    marker_or_style_distinguishable = True

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

            pair_results.append(
                {
                    "series_a": a.get("name", f"series_{i}"),
                    "series_b": b.get("name", f"series_{j}"),
                    "marker_or_style_distinguishable": marker_style_ok,
                }
            )

    checks = {
        "metadata_exists": True,
        "png_export_available": True,
        "accessiplot_color_detection": accessiplot_pass,
        "marker_or_style_distinguishable": marker_or_style_distinguishable,
    }

    visibility_issues = []
    for s in series:
        name = str(s.get("name", "series"))
        if name.lower() == "data":
            continue
        alpha = s.get("alpha")
        lw = s.get("linewidth")
        if alpha is not None and float(alpha) < args.min_alpha:
            visibility_issues.append(
                f"{name}: alpha {float(alpha):.3g} < min_alpha {args.min_alpha}"
            )
        if lw is not None and float(lw) < args.min_linewidth:
            visibility_issues.append(
                f"{name}: linewidth {float(lw):.3g} < min_linewidth {args.min_linewidth}"
            )
    checks["line_visibility"] = len(visibility_issues) == 0
    failing = [k for k, ok in checks.items() if not ok]
    status = "ok" if not failing else "warning"

    report = {
        "status": status,
        "summary": (
            "Accessibility checks passed"
            if status == "ok"
            else "Accessibility checks reported warnings"
        ),
        "artifacts": [str(out.resolve())],
        "validation": checks,
        "accessiplot": {
            "png_input": png_path,
            "common_colors": to_builtin(common_colors),
            "deficiency_results": to_builtin(accessiplot_results),
        },
        "pairwise": pair_results,
        "visibility_issues": visibility_issues,
        "thresholds": {
            "min_alpha": args.min_alpha,
            "min_linewidth": args.min_linewidth,
        },
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
