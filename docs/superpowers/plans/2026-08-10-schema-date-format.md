# Plan: add schema date formats

1. Add RED schema-only tests using `FormatChecker` for impossible dates.
2. Add minimal `format: date` properties to both schemas and run focused tests.
3. Run static/provenance checks, publish once, install exact version, and verify
   identity plus schema/runtime smoke.
