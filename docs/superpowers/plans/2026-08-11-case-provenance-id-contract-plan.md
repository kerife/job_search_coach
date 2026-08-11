# Plan: require provenance IDs in case records

1. Add stable synthetic source/claim IDs to the canonical valid test case and
   add a table-driven RED test for missing IDs on all four record arrays.
2. Confirm the new test fails against the current optional-field validator.
3. Make the smallest validator change: require presence, then retain the
   existing non-empty-string check.
4. Run focused and full case/plugin/root/static/privacy/release checks.
5. Bump the cache once, install the canonical plugin, verify source/cache
   parity and installed smoke, refresh provenance/attestation, and rerun final
   gates.
