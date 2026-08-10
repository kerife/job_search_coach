# Practice reference type guard design

## Goal

Prevent malformed practice-session reference arrays from crashing uniqueness checks.

## Scope

In `_references`, validate list shape, string elements, ID grammar, and only then uniqueness. Preserve valid sessions, existing error messages/exit codes, renderer gating, and all private boundaries. No schema or routing changes.

## Acceptance

Object-valued or mixed-type `fact_ids` in requirements/questions produce deterministic validation errors and renderer rejection without `TypeError`; valid EN/ES fixtures and duplicate-ID rejection remain unchanged.
