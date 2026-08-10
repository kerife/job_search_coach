# Plan: timeout static schema harness

1. Add RED test proving a simulated timeout is converted to a bounded static
   error.
2. Add the 30-second subprocess timeout and deterministic catch; run focused
   static tests.
3. Refresh provenance, publish once, install exact version, and verify identity.
