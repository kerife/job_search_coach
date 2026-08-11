# Plan: JSON Schema Pattern Semantics

1. Add the unanchored/anchored pattern cases and observe the unanchored case
   fail under the current `fullmatch` implementation (RED).
2. Replace the single matching call with `re.search` and keep diagnostics
   bounded (GREEN).
3. Run focused and complete gates with `PYTHONPATH` set for sibling scripts,
   then refresh allowlisted provenance.
4. Consume the cachebuster exactly once, publish/install, and verify source/cache
   identity plus the installed release validator.
