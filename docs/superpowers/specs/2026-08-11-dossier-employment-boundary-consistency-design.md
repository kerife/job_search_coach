# Dossier Employment Boundary Consistency Design

## Goal

Make the executive dossier use the same visible employment-continuity boundary as the practice, triage, and private recruiter receipt surfaces.

## Context

The dossier currently says that it does not recommend resigning or leaving a job, but it does not explicitly say that it does not recommend stopping the job search. The other candidate-facing surfaces already use the canonical sentence. This wording drift weakens the office-safe framing even though the current behavior is draft-only and non-executing.

## Design

Update only the localized `employment_boundary` strings in `render_executive_career_dossier.py` to the canonical values:

- EN: `This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.`
- ES: `Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.`

Keep the existing footer location, `employment-boundary` class, LinkedIn action boundary, no-action text, HTML escaping, and all privacy/action gates unchanged. The sentence remains visible in normal and print output; it must not be placed in a `no-print` element.

## Acceptance criteria

1. English and Spanish dossier renders contain the canonical sentence exactly once.
2. The previous shorter English and Spanish strings are absent.
3. `scenario-a-es`, `scenario-c-en`, and one partial dossier fixture still render deterministically and preserve `No LinkedIn action was performed.` / `No se realizó ninguna acción en LinkedIn.`.
4. Existing privacy, schema, forced-colors, dark-mode, print, and no-external-action contracts remain green.
5. The release is bumped, installed from `professional-growth-coach-local`, and source/cache parity plus installed smoke are recorded.

## Non-goals

- No schema, validator, route, action, or data-model changes.
- No browser navigation, LinkedIn access, or external action.
- No visual redesign beyond the existing footer copy.
