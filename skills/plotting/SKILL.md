---
name: "roman-plotting"
description: "Route Roman plotting work to the correct plotting skill, including plot generation, style-profile checks, and accessibility checks."
---

<essential_principles>
Roman plotting should default to deterministic, publication-safe workflows when an executable plot skill exists.

Use validation skills only when the user asks for style or accessibility review, or when plot QA is part of the task.

Do not route into customization guidance unless the default plotting workflow cannot satisfy the request.
</essential_principles>

<routing>
Route by plotting intent:

- Generate or revise a Roman figure:
  Read `plot-types/SKILL.md`.
- Check target-journal formatting or produce a style verdict:
  Read `style-profiles/SKILL.md`.
- Check color/marker accessibility or grayscale separability:
  Read `accessibility-checks/SKILL.md`.

If the user asks for a lightcurve figure, continue into `plot-types/SKILL.md` immediately.
</routing>

<success_criteria>
A well-executed plotting routing decision:
- Sends figure-generation requests to a plot-type skill.
- Sends validation-only requests to the appropriate checking skill.
- Preserves strict defaults unless the request explicitly requires deviation.
</success_criteria>
