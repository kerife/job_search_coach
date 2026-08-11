# Dossier Snapshot Binding

## Goal

Make the dossier-to-practice handoff cryptographically bound to the exact
validated dossier that produced it. A syntactically valid but fabricated
`source_snapshot` must never pass the handoff builder or parity validator.

## Contract

`source_snapshot` uses the closed format
` snap-dossier-sha256-<64 lowercase hexadecimal characters> `. The suffix is
the SHA-256 digest of the canonical JSON serialization of the validated
dossier (`sort_keys=true`, compact separators, UTF-8, no ASCII escaping).

The builder computes the expected identifier from the supplied dossier and
requires the caller-provided value to match exactly. The parity validator
recomputes the same value before comparing projections. Errors remain bounded
and never include the dossier, digest, or caller input.

Existing triage snapshot identifiers remain unchanged. Practice-session
schemas accept the new dossier format only when
`handoff_context.source=executive_career_dossier`; triage keeps its existing
`snap-triage-###` contract.

## Compatibility and privacy

This is a contract versioning change within the existing v1 handoff artifact;
the opaque snapshot remains hidden by renderers. No raw dossier text, URLs,
candidate identifiers, or digest values are rendered. Direct practice
sessions that use the dossier source must use the content-bound identifier;
triage-sourced sessions are unaffected.

## Acceptance

- A canonical dossier plus its computed snapshot builds and validates.
- `snap-dossier-999`, a valid-format ID with the wrong digest, is rejected by
  both builder and parity validator.
- Mutating the dossier after computing the snapshot is rejected.
- Schema subset validation accepts the new dossier snapshot format and still
  rejects triage snapshots in dossier handoffs.
- Existing triage snapshots remain valid.
- No diagnostics echo private input.
