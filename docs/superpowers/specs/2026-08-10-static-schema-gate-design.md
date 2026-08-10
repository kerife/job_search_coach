# Run private schema conformance from static checks

## Goal

Ensure the official static gate executes the private schema conformance harness,
not only the full integration suite.

## Design

At the end of `run_static_checks.py`, invoke the dependency-free harness through
its unittest entry point in-process (or the existing deterministic test runner)
and convert any failure into a static-check error. Keep the expected result
explicit at two tests, avoid external dependencies, and preserve the checker’s
existing concise output and exit contract.

## Verification

Static checks pass with the current schemas and fail when a targeted schema
mutation is introduced. Full integration, runtime validators, renderer, privacy,
and routing behavior remain unchanged.
