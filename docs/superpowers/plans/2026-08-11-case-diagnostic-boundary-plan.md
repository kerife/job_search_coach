# Case Diagnostic Boundary Plan

1. Add RED tests for many unsupported keys, one long key, a multibyte key, and
   C0/DEL control characters in an unsupported key.
2. Implement a CLI-only UTF-8 byte-budget formatter with a fixed truncation
   notice, preserving complete diagnostic lines, plus terminal-safe path-key
   escaping.
3. Document the diagnostic cap and keep `validate_case()` API output unchanged.
4. Run case, structure/privacy, static, plugin, and release suites.
5. Bump once, install, refresh provenance/attestation, compare source/cache, and
   run installed smoke.
