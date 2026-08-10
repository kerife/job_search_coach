# Private prose control guard design

## Goal

Prevent invisible Unicode controls from bypassing the privacy and identity-free
prose boundaries in dossier, recruiter-practice, and recruiter-reply-triage
artifacts.

## Design

Add one dependency-free helper that NFKC-normalizes a string and rejects any
character whose Unicode category is `Cc` or `Cf`. Existing textual guards keep
their current pattern checks; the new helper is an additional fail-closed
condition, so visible whitespace remains valid while bidi, zero-width, BOM, and
other control characters are rejected before validation/rendering.

Use the helper from the dossier safe-text guard and from the triage/practice
prose validators. Add matching schema `not.pattern` control guards to every
projected prose field covered by those validators, so schema-only consumers and
custom validators agree.

## Acceptance

- Canonical EN/ES fixtures remain valid.
- Mutations containing U+200B, U+202E, U+2066, and U+FEFF in safe context,
  facts, questions, requirements, blocked claims, rubric, and feedback prose
  fail with bounded deterministic errors.
- The dependency-free schema checker rejects the same mutations.
- No error output echoes the private prose value; no renderer or action contract
  changes.
- Existing plugin, root, static, privacy, and marketplace-install gates remain
  green.
