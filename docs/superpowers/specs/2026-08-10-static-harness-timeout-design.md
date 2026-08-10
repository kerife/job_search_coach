# Bound static schema-harness execution time

## Goal

Prevent a hung private schema conformance harness from blocking releases
indefinitely.

## Design

Run the existing harness subprocess with a 30-second timeout. Catch
`subprocess.TimeoutExpired` and add a deterministic failure message containing
the harness path and timeout, without a traceback or captured fixture content.
Keep normal stdout, error formatting, exit code, and harness behavior unchanged.

## Verification

Add a focused unit test for the timeout helper/branch using a simulated timeout;
the normal static gate and conformance tests remain green.
