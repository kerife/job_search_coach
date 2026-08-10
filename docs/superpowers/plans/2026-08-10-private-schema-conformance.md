# Plan: test private schema conformance

1. Add RED tests and a minimal test-only validator for the schema subset in use.
2. Make valid fixtures pass and invalid date/action mutations fail.
3. Run focused/full relevant checks, publish once, install exact version, and
   verify identity.
