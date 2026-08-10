# Conversion outcome loader hardening design

## Goal

Ensure private conversion-outcome ingestion cannot follow a symlink or accept excessively deep JSON before validation/rendering.

## Design

The existing loader remains the sole input boundary. It rejects a symlink path before reading, preserves bounded byte and duplicate-key checks, and rejects nested arrays/objects deeper than the existing private-artifact limit with the same fail-closed load error. Valid EN/ES fixtures and renderer behavior remain unchanged.

## Acceptance

Focused contract tests cover valid fixtures, symlink rejection, and over-depth JSON; CLI returns its existing failure code without an artifact, and renderer rejects the same malformed input through the validator gate. Static/privacy/full tests remain green.
