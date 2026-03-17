---
name: "roman-plotting-plot-types"
description: "Route Roman figure-generation requests to the correct plot type, especially lightcurve residual plots now and additional plot families as they are added."
---

<essential_principles>
Choose the narrowest plot-type skill that matches the requested scientific figure.

Prefer an implemented leaf skill over a generic plotting plan.

When only one relevant plot type exists, route directly instead of forcing extra choice.
</essential_principles>

<routing>
Current plot-type routing:

- Lightcurve with optional residual panel, including model overlays and multiband normalization:
  Read `lightcurve-residuals/SKILL.md`.

Planned plot types to add under this directory include caustic diagrams and color-magnitude diagrams. Until those exist, do not invent parallel workflows here.
</routing>

<success_criteria>
A well-executed plot-type routing decision:
- Reaches `lightcurve-residuals` immediately for current lightcurve work.
- Leaves space for future plot families without overbuilding the router today.
</success_criteria>
