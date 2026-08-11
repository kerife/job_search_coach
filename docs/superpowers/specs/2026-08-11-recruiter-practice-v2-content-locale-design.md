# Recruiter Practice Session v2 Content Locale

## Context

The v1 practice contract uses one `locale` for both fixed interface copy and
free-form candidate/vacancy prose. A valid session can therefore have English
chrome around Spanish (or English) source prose, causing an inaccurate document
language for assistive technology. Adding an optional field to v1 would violate
its closed schema and make old consumers disagree about accepted objects.

## Design

Introduce `recruiter-practice-session-v2` as an additive contract. It replaces
v1's `locale` with required `ui_locale` and `content_locale`, each `es|en`.
The existing v1 validator, schema, fixtures, and rendered markup remain
unchanged. The shared practice validator dispatches v1/v2 by
`schema_version`; v2 requires both locale fields and uses the same privacy,
state, identifier, and delivery rules.

The practice renderer uses `ui_locale` for all fixed labels, headings, copy,
and document `lang`. It adds `lang=content_locale` to the dynamic prose nodes:
safe context, requirement, question, fact, observed answer, rubric, and
feedback statements. Static UI text is never inferred or translated. V2
rendering remains offline, escaped, private, and schema-validated.

This increment intentionally scopes the versioned contract to recruiter
practice. Triage and dossier will need their own versioned content-locale
contracts rather than silently accepting new fields in v1.

## Compatibility and errors

V1 remains accepted exactly as before and rejects `ui_locale`/
`content_locale` as unsupported fields. V2 rejects missing/invalid locale
fields and any v1-only `locale`; malformed or unsafe prose still fails closed.

## Verification

Add a v2 schema and fixture-derived conformance tests for independent English
UI/Spanish content plus rejection of missing/invalid locale fields. Add
renderer tests that assert document `lang="en"`, dynamic `lang="es"` nodes,
English fixed copy, resolved ARIA references, and no raw identifiers. Preserve
all v1 tests and run the full release/install matrix.
