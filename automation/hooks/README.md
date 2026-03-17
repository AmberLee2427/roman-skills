# Generic Hooks

This repository is agent-platform neutral. Hook automation should be configured through whichever runner/orchestrator executes agent workflows.

Use this folder for hook templates and trigger wiring that are **not vendor-specific**.

## Suggested Hook Events
- `post-plot`: run style and accessibility gates after figure generation.
- `pre-publication-bundle`: fail if gate reports include `error`.
- `session-stop`: summarize unresolved warnings.

## Suggested Commands
- `python skills/plotting/accessibility-checks/scripts/check_accessibility.py --metadata <plot.meta.json> --output <out/accessibility.json>`
- `python skills/plotting/style-profiles/scripts/check_style_profile.py --metadata <plot.meta.json> --profile <apj|mnras|aanda> --output <out/style.json>`
