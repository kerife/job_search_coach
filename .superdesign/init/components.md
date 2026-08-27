# Shared UI components

## Implementation finding

This is a Python-rendered static HTML/CSS plugin, not a React (or other client-framework) application.

- **Framework / meta-framework:** none. There is no `package.json`, no framework configuration, and no file-based or client router.
- **Component library:** none.
- **CSS approach:** eleven standalone CSS files are read by Python renderers and inserted into matching HTML templates as `{{INLINE_CSS}}`.
- **Shared JavaScript:** none. The dossier renderer may insert a page-specific inline script; there is no shared JS component directory.
- **Reusable UI primitive directory:** none found.

No source-backed shared primitives meet the criteria for this file. Do not infer React components, imports, props, or a design-system package from repeated CSS class names. The complete source for the five static document layouts is in `layouts.md`; complete stylesheet source is in `theme.md`.

## Reuse boundary

The repeated patterns are static markup produced inside Python renderers, not exported UI components. Candidate extractions are catalogued in `extractable-components.md` as future DraftComponent opportunities only. The decision-gate brief introduces static patterns `GateDecisionSummary`, `DecisionRow`, and `ManualBoundaryPanel`; the screen-intake brief adds `ReadinessSummary`, `CheckList`, and `EvidenceContextGrid`. They remain renderer-local markup rather than reusable client components.
