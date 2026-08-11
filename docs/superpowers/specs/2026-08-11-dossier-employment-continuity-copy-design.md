# Dossier Employment-Continuity Copy Guard

## Goal

Ensure the executive-career dossier cannot render an imperative instruction to
resign, quit, leave an employer, reduce hours, or create a voluntary gap. The
dossier is a market-evaluation artifact for Professional Growth Coach, not a
separation recommendation.

## Scope

The guard applies to decision-bearing dossier prose that can become a next
action or market interpretation:

- `market_context.reason`;
- `priorities[].action` and `priorities[].why_now`;
- `seven_day_plan[].action` and `seven_day_plan[].done_when`.

The guard rejects direct imperative separation language in English and Spanish
(`resign`, `quit`, `leave your job`, `renuncia`, `renunciar`, `deja tu empleo`,
and equivalent bounded forms). It does not reject neutral analysis or the
explicit negated boundary already used by the plugin, such as “this is not
advice to resign” or “no es una recomendación de renunciar”.

Errors are deterministic, short, and do not echo the input. Rendering remains
fail-closed because dossier validation runs before HTML generation.

## Alternatives rejected

- A global word blacklist would flag valid continuity disclaimers and market
  analysis.
- A new required schema field would force a broad fixture and consumer
  migration for a localized copy safety problem.

## Acceptance

- A dossier with `market_context.reason="Resign now and leave your job."` is
  rejected and cannot render.
- Equivalent Spanish imperative copy in each scoped field is rejected.
- Neutral market evidence and explicit negated continuity boundaries remain
  valid.
- The rejected text is absent from diagnostics and generated HTML.
- Existing dossier, renderer, privacy, schema, and release gates remain green.
