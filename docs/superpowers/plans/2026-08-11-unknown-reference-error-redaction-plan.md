# Plan: redact unknown reference values

1. Add RED tests for unknown triage and practice fact references containing an
   email and phone-like value; assert rejection, path, and no value echo.
2. Confirm both tests fail against the interpolating validators.
3. Replace only the interpolated value with the fixed unknown-identifier
   diagnostic in both validators.
4. Run focused validators/renderers, full plugin/root suites, static, privacy,
   and locked official release validation.
5. Bump the cache once, install the canonical plugin, smoke the redaction from
   source and cache, refresh attestation/provenance, and rerun final gates.
