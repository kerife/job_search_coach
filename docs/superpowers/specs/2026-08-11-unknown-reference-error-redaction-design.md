# Redact unknown reference values from validator errors

## Context

Private triage and practice validators reject references that are not present in
their bounded evidence set. Their current error includes the untrusted
reference value itself. A malformed `fact_ids` entry can therefore echo an
email, phone number, or other private identifier into stderr and logs.

## Design

Keep the exact field path and deterministic rejection, but replace the value
interpolation with the fixed message `references unknown identifier`. The
renderers remain fail-closed because validation still returns the same error;
only diagnostic disclosure changes. Apply the same behavior to every unknown
reference path in both triage and practice validators.

## Non-goals

No acceptance of unknown references, schema change, renderer copy change,
logging format outside this error, or attempt to infer/redact values after
they have already been emitted.

## Acceptance

1. Unknown reference errors retain their JSON path and fixed reason.
2. Supplied email, phone, URL, and arbitrary sentinel values never appear in
   validator stderr or renderer error text.
3. Known references and all existing valid fixtures remain unchanged.
4. Privacy, static, schema, release, plugin, root, source/cache, and installed
   smoke gates remain green.
