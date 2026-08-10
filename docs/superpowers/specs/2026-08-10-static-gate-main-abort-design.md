# Abort static gate immediately on harness failure

## Goal

Prove the static gate's `main()` returns failure immediately when the schema
harness times out or emits an invalid summary, rather than continuing into
unrelated checks.

## Design

Add in-process tests that inject the harness result/failure and patch a sentinel
downstream check. Assert return code 1, deterministic harness error, and that the
sentinel is not called. Keep normal success behavior and existing bounded timeout
unchanged.

## Verification

Focused main-abort tests, static gate, full harness, and diff checks remain green.
