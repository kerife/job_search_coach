# Conversion fact ID type guard design

## Goal

Ensure malformed conversion-outcome `fact_ids` values return deterministic validation errors instead of crashing on set construction.

## Scope

In the existing validator, validate list shape and string element types before uniqueness checks. Preserve the closed ID grammar, renderer gate, CLI exit behavior, and valid EN/ES fixtures. No schema, routing, or HTML changes.

## Acceptance

Object-valued and mixed-type `fact_ids` produce ordinary validation errors; renderer and CLI do not raise `TypeError`; valid IDs and duplicate-ID rejection remain unchanged. Focused contract/renderer, static, privacy, and full tests pass.
