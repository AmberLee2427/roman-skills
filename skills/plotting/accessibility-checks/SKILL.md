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
1. Parse series definitions from metadata.
2. Check pairwise distinguishability using marker and color distance rules.
3. Estimate grayscale separability from luminance distance.
4. Emit JSON report with explicit checks and caveats.

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
