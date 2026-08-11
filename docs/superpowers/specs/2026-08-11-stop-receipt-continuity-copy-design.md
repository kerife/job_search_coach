# Stop Receipt Continuity Copy Design

## Goal

Keep isolated stop-decision receipts aligned with Professional Growth Coach's
employment-continuity boundary: a stop records one recruiter process or
preparation path, never a recommendation to leave employment or abandon a job
search.

## Scope

Change only the localized action and boundary copy emitted for `stop_decision`
in the follow-through checkpoint and conversion outcome renderers. Non-stop
events, schemas, data fields, HTML structure, CSS, privacy guards, and external
action behavior remain unchanged.

## Copy contract

For English stop receipts:

- Action: `Record this recruiter-process outcome privately; do not continue this preparation path.`
- Boundary: `Scope: this records one recruiter-process outcome only. It is not advice to resign, leave a job, or stop your job search; you decide what comes next.`

For Spanish stop receipts:

- Action: `Registra en privado el resultado de este proceso de reclutamiento; no continúes por esta vía de preparación.`
- Boundary: `Alcance: esto solo registra un resultado de este proceso de reclutamiento. No es una recomendación de renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.`

The copy is rendered only when the validated event/state is
`stop_decision`. Existing boundary copy remains for all other events.

## Implementation and data flow

The two renderers already localize action labels and boundary text from the
validated event. Add a stop-specific branch in each renderer's localization
table/selection logic, then pass the resulting strings through the existing
HTML escaping and template slots. No schema change or new field is required.

## Verification

Tests must demonstrate, before implementation, that the current stop fixtures
fail the new assertions. After implementation they must verify:

1. English and Spanish stop checkpoint and outcome receipts contain the exact
   recruiter-process action and continuity boundary.
2. Non-stop English and Spanish receipts retain their existing action/boundary
   copy.
3. Rendered output contains no forms, links, external actions, raw IDs, or
   unescaped sentinel text.
4. Existing compact receipt, triage, privacy, static, and release gates remain
   green.

The next cycle may address canonical binding of dossier→practice snapshots;
that provenance change is deliberately excluded here.
