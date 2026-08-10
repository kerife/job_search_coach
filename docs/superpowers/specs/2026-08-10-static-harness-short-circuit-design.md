# Static harness short-circuit design

## Goal

Make the static gate stop after the first conformance-harness failure instead
of launching another expensive subprocess.

## Problem

`run_static_checks.main()` records a private-schema harness failure, then still
runs the dossier-practice harness before returning. The root tests explicitly
require an early abort, and the nested subprocess can hit its 30-second bound,
masking the original diagnostic and slowing the full suite.

## Design

After validating the private-schema harness, print its bounded diagnostics and
return `1` immediately when errors exist. Only when it passes should the
dossier-practice harness run. Preserve the existing validation and diagnostics
for both harnesses when the first one is healthy. Do not change timeout values,
plugin contracts, schemas, renderers, or marketplace metadata.

## Acceptance

- A private-schema timeout or invalid summary returns before starting the
  dossier-practice subprocess.
- A dossier-practice timeout still aborts before package checks.
- A healthy pair continues to run the package checks and passes static checks.
- Existing static and root tests no longer hang on the early-abort cases.
