---
name: "roman-plotting-style-profiles"
description: "Validate figure metadata against journal-oriented style profiles (for example ApJ, MNRAS, A&A) and produce deterministic pass/warn/fail reports for publication prep."
---

# Roman Plotting Style Profiles Skill

## Purpose
Provide a reusable profile-based style gate for Roman figures so publication requirements are checked consistently before manuscript assembly.

## Use This Skill When
- You need publication style conformance checks.
- Figures are being prepared for a specific target journal.
- You want a machine-readable style report in CI/agent pipelines.

## Inputs To Confirm
- Plot metadata JSON path.
- Target profile (`apj`, `mnras`, `aanda`).
- Output report path.

## Workflow
1. Load metadata and confirm required structural fields.
2. Apply profile-specific checks from `references/profiles.md`.
3. Emit JSON result with explicit pass/fail checks and caveats.

## Output Contract
Return:
- `status`: `ok | warning | error`
- `summary`: short style verdict
- `artifacts`: report path(s)
- `validation`: individual checks
- `provenance`: input metadata path and timestamp

## References
- `references/profiles.md`

## Scripts
- `scripts/check_style_profile.py`
