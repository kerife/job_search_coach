# Case Input Error Redaction Plan

> TDD cycle: keep the release/cache unchanged until RED and GREEN checks pass.

1. Add a CLI RED test for an unreadable path containing an email/token-shaped
   sentinel; assert bounded stderr and no sentinel echo.
2. Separate `OSError` in `validate_case.py` and emit the fixed read-error
   message; preserve existing parse/encoding diagnostics.
3. Run focused and full case-validator tests, static/privacy/release gates.
4. Bump once, install once, compare source/cache, refresh provenance and smoke
   attestation, then run the complete plugin and repository suites.
