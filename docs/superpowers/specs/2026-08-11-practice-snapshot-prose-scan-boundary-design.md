# Practice Snapshot Prose-Scan Boundary

## Goal

Prevent a valid triage v2 content-bound snapshot from being mistaken for a
phone number or identity prose by the practice-session privacy scan.

## Contract

- `handoff_context.source_snapshot` remains structurally validated by the
  existing v1/v2 patterns and source-specific checks.
- The practice prose scan excludes only the `source_snapshot` field inside
  `handoff_context`; all other handoff fields and all user-facing prose remain
  scanned.
- Practice-session v1 behavior and its legacy `snap-triage-###` contract are
  unchanged. No digest is recomputed or trusted by this change.

## Privacy and rendering

The snapshot remains an internal handle. Renderer output continues omitting
`source_snapshot`, and validation errors do not echo caller-provided values.
Excluding the handle from prose scanning avoids a false positive; it does not
weaken the structural format or source checks.

## Acceptance

1. A v2 practice session carrying a valid hash whose hex includes a
   phone-like digit run validates.
2. The same session still rejects identity/action/raw prose in ordinary fields.
3. V1 legacy sessions remain green and malformed snapshots fail structurally.
4. Practice rendering does not include the snapshot or its digest.
