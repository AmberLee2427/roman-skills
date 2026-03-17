---
name: "roman-event-summary"
description: "Generate standardized Roman microlensing event summary products from local analysis tables, including key scalar metrics, model metadata, and reproducible provenance for downstream reports and plotting workflows."
---

# Roman Event Summary Skill

## Purpose
Build concise, machine-readable event summaries from analysis inputs so downstream agents can reason over standardized event metadata.

## Use This Skill When
- You need a one-page event summary for a dataset or fit result.
- Multiple events require normalized metadata extraction.
- Downstream plotting/reporting should consume stable summary fields.

## Inputs To Confirm
- Input CSV path.
- Column mapping for time, value, and uncertainty.
- Optional model columns/metadata fields.
- Output JSON path.

## Workflow
1. Validate required columns and parse numeric fields.
2. Compute core descriptive statistics.
3. Estimate event-level diagnostics (peak timing/value, amplitude, duration proxy).
4. Include optional model metadata if supplied.
5. Emit canonical summary JSON with provenance.

## Output Contract
Return:
- `status`: `ok | warning | error`
- `summary`: short event descriptor
- `artifacts`: summary JSON path
- `validation`: required-field and parse checks
- `provenance`: input path and timestamp

## Constraints
- Do not infer physical lens parameters unless explicitly provided.
- Keep derived values clearly labeled as descriptive proxies.
- Always include units labels when passed by caller.

## References
- `references/schema.md`
- `references/fields.md`

## Scripts
- `scripts/build_summary.py`
