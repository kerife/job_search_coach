# Plan: redact LinkedIn unknown-reference diagnostics

1. Add RED tests for unknown evidence/fact IDs in score, priority, copy, and
   generic reference paths; assert context remains and sentinel values do not.
2. Confirm the tests fail against the interpolating validator.
3. Replace only untrusted-value interpolation with fixed diagnostic wording.
4. Run LinkedIn, plugin, root, static, privacy, and locked official release
   gates.
5. Bump once, install, smoke source/cache redaction, refresh attestation and
   provenance, and rerun final gates.
