---
name: "roman-plotting-accessibility-checks"
description: "Run deterministic accessibility checks on plot metadata, including marker redundancy and grayscale/color separability signals for multi-series scientific figures."
---

# Roman Plotting Accessibility Checks Skill

## Purpose
Provide an automated accessibility gate for Roman figures before publication packaging.

## Use This Skill When
- Multi-series figures rely on color to distinguish data/model sources.
- You need a machine-readable accessibility report.
- You want gateable checks for grayscale and marker redundancy.

## Inputs To Confirm
- Plot metadata JSON path.
- Output report path.

## Workflow
1. Parse exports and series definitions from metadata.
2. Use `accessiplot.detection.color_detection` on the PNG export for CVD-aware color checks.
3. Run supplemental line-visibility and marker-style checks from metadata.
4. Emit JSON report with explicit checks and caveats.

## Dependencies
- Python package: `accessiplot`
- Install all project deps: `pip install -r requirements.txt`
- Note: `accessiplot` requires `colorthief` and `colorspacious` in this environment; both are included in `requirements.txt`.

## Output Contract
Return:
- `status`: `ok | warning | error`
- `summary`: short accessibility verdict
- `artifacts`: report path(s)
- `validation`: individual checks
- `provenance`: input metadata path and timestamp

## References
- `references/rules.md`

## Scripts
- `scripts/check_accessibility.py`
