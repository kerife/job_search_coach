# JSON Schema Pattern Semantics

## Context

The dependency-free schema checker uses `re.fullmatch` for JSON Schema
`pattern`. JSON Schema pattern keywords use search semantics unless the schema
author supplies `^` and `$`. The current checker therefore rejects valid
substring matches and can diverge from a standards-compliant validator.

## Design

Change only the pattern operation from full-match to search. Keep all existing
type checks, invalid-regex diagnostics, and schema-authored anchors unchanged:
anchored patterns continue to require the complete format, while unanchored
patterns accept a matching substring. No production schema needs to change in
this increment.

## Verification

Add a focused conformance regression proving an unanchored pattern accepts a
prefix/suffix string and an explicitly anchored pattern still rejects extra
text. Run schema conformance, static, privacy, renderer, root, release, and
diff checks before publication.
