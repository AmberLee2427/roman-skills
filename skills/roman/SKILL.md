---
name: "roman"
description: "Route Roman analysis requests to the appropriate domain skill, especially plotting, modeling, photometry, and time-series QC."
---

<essential_principles>
Roman skills should route to the narrowest domain that can satisfy the request.

Prefer specialized leaf skills over broad top-level reasoning once the task type is clear.

If the user asks for a Roman lightcurve figure or publication plotting help, route to `../plotting/SKILL.md`.
</essential_principles>

<routing>
Route by task type:

- Plot generation, figure styling, publication exports, accessibility, or plot review:
  Read `../plotting/SKILL.md`.
- Model fitting, model comparison, retrieval, or microlensing model selection:
  Read `../modeling/` leaf skills relevant to the requested model family.
- Aperture photometry or difference imaging:
  Read `../photometry/` leaf skills relevant to the requested extraction method.
- Time-series QA and diagnostic checks:
  Read `../qc/` leaf skills relevant to the requested validation task.

When the user clearly needs a lightcurve plot now, do not stop at this router. Immediately continue into `../plotting/SKILL.md`.
</routing>

<success_criteria>
A well-executed Roman routing decision:
- Identifies the correct major domain quickly.
- Hands off to a narrower skill without duplicating its workflow.
- Keeps the user moving toward the actual leaf skill that performs the work.
</success_criteria>
