# Plan: include schema conformance in static gate

1. Add a RED static-gate test or assertion that fails when schema conformance is
   not executed.
2. Add the minimal in-process harness invocation and verify both pass/fail paths.
3. Run static/full focused checks, publish once, install exact version, and
   verify identity.
