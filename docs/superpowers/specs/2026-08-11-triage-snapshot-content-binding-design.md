# Triage Snapshot Content Binding

## Goal

Bind new private recruiter triage v2 handoffs to the exact identity-free
triage payload that produced them, while preserving every existing v1
`snap-triage-###` fixture and consumer.

## Contract

- v1 triage remains unchanged: `schema_version=private-recruiter-reply-triage-v1`
  continues to accept `snap-triage-###` in both handoff packets.
- v2 triage uses `snap-triage-sha256-<64 lowercase hexadecimal characters>`
  in both `handoff.packet.source_snapshot` and
  `handoff.reentry_packet.source_snapshot`.
- The suffix is SHA-256 over canonical UTF-8 JSON (`sort_keys=true`, compact
  separators, no ASCII escaping) of the complete validated triage object after
  removing only those two duplicated `source_snapshot` fields. This avoids a
  recursive hash while binding all other safe context, facts, question,
  decisions, delivery, and handoff fields.
- The validator computes the expected v2 identifier and requires both packet
  values to match it. A changed summary, fact, question, or handoff field with
  the old digest fails closed.
- The JSON schema mirrors the v2 format. V1 schema and fixtures are untouched.

## Privacy and rendering

The digest is an internal provenance handle only. Validator errors remain
bounded and do not include triage content, caller-provided digests, or the
computed digest. Renderers continue omitting `source_snapshot`; no digest or
raw source is emitted in HTML/chat output.

## Scope and compatibility

This increment changes only v2 triage validation/schema and the shared helper.
It does not migrate v1 fixtures, alter practice-session contracts, or install
the plugin/cache. Existing v1 render and CLI behavior must remain green.

## Acceptance

1. A v2 ready fixture with the computed hash validates through the Python
   validator and v2 JSON schema.
2. Mutating any bound v2 content while retaining the prior hash is rejected.
3. Packet and reentry snapshots must both equal the computed hash.
4. V1 clarify/ready/stop fixtures continue to validate unchanged.
5. v2 renderer output contains neither `source_snapshot` nor the digest.
