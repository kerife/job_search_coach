# Plan: make schema gate count extensible

1. Add RED parser tests for current/larger/malformed unittest summaries.
2. Replace the exact-count assertion with the minimal generic parser and run
   focused/full gate checks.
3. Refresh provenance, publish once, install exact version, and verify identity.
