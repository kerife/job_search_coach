# Case Input Boundary Hardening Plan

1. Add RED CLI tests for symlink input and a case payload larger than 64,000
   bytes, asserting fixed errors and no sentinel echo.
2. Add a bounded descriptor reader using `O_NOFOLLOW`, `O_CLOEXEC`, `fstat`, and
   a `MAX_CASE_BYTES + 1` read threshold.
3. Guard the email regex behind an `@` prefilter and add a deterministic no-regex
   regression test for long non-email input.
4. Update the case contract with the input-size and regular-file boundary.
5. Run focused case tests, privacy/structure tests, static checks, and the full
   plugin suite.
6. Bump once, install, compare source/cache inventory and hash, refresh
   provenance/attestation, and run installed smoke plus release validation.
