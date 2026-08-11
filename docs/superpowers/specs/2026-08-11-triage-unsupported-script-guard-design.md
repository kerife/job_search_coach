# Triage unsupported-script identity guard

## Context

The private recruiter-triage contract accepts only `en`/`es` content and
promises identity-free prose. The contextual Latin guard now rejects selected
person/company disclosures, but Cyrillic and CJK names bypass those patterns
and are embedded in the private HTML receipt.

## Design

Add a fail-closed prose guard for scripts outside the supported Latin locales.
Inspect Unicode character names and reject prose containing letters from
scripts such as Cyrillic, CJK, Japanese, Korean, Arabic, Hebrew, Greek, or
Devanagari. Keep Latin letters (including Spanish accents), digits, punctuation,
emoji, non-letter symbols, and ordinary technical terms accepted. The guard applies uniformly to
the four client-facing triage prose fields and the final recursive safety pass.

The error is a stable category (`unsupported_script`) and never includes the
offending text. The renderer continues to validate before reading dynamic prose,
so rejected values cannot reach HTML.

## Contract and scope

- This is limited to the private triage artifact, whose locale contract is
  already `en`/`es`; it does not alter dossier/practice schemas or UI copy.
- Existing Latin/Spanish fixtures and role-focused technical prose remain valid.
- No external actions, network access, schema version, or cache format changes
  are introduced.
- Future multilingual support must explicitly broaden the locale contract and
  replace this guard with a locale-aware identity redaction policy.

## Verification

1. Add RED tests for Cyrillic and CJK person/company prose in all four fields,
   plus a Latin technical-prose acceptance test and renderer rejection test.
2. Implement the Unicode-name guard with bounded diagnostics.
3. Run triage/renderer, plugin, privacy, static, release, and full suites.
4. Consume one cachebuster, publish/install, compare source/cache byte identity,
   and run the installed guard smoke.
