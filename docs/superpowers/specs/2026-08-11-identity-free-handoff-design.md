# Identity-free dossier-to-practice projection design

## Context

The dossier-to-practice bridge promises an identity-free source projection,
but a fact paraphrase beginning with an unlabelled person name can currently
pass the shared safe-text guard and be copied into the private handoff.

## Decision

Add a strict identity-free text contract only to the source-fact projection
fields (`dossier_projection.fact_summary` and `practice_projection.facts[].summary`).
The guard will reject a bare two-token person-name introduction when it is
followed by an identity-bearing reporting verb, while preserving ordinary role
prose such as `Senior Engineer leads incident response.`. Existing general
safe-text fields and dossier input semantics remain unchanged.

The builder, handoff validator, and dependency-free schema must agree. Errors
remain bounded and never echo the rejected prose.

## Acceptance

1. `Ana López reports Terraform experience.` is rejected by the strict helper,
   builder, custom handoff validator, and schema checker.
2. Equivalent English/Spanish reporting forms and `Jordan Lee works at Acme`
   are rejected without input echo.
3. Normal role prose such as `Senior Engineer leads incident response.` and
   the canonical fixtures remain accepted.
4. No renderer, external action, network, or raw-input behavior changes.
5. Focused handoff/schema tests, plugin tests, static/privacy gates, release
   validation, and source/cache parity remain green.
