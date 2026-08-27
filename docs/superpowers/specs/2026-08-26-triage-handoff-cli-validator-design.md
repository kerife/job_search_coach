# Triage handoff CLI and independent validator

## Goal

Make the validated `private-recruiter-triage-practice-handoff-v1` composition
usable outside an in-process test by exposing a deterministic, private-input
CLI and an independent validator that consumers can run before rendering.

## Scope and boundaries

- Accept only `private-recruiter-reply-triage-v2` with
  `state=ready_for_private_prep`, `handoff_allowed=true`, and one `verified`
  fact.
- Recompute and compare the triage snapshot, packet, and re-entry references;
  never trust a supplied snapshot.
- Emit only the closed handoff wrapper. The CLI never sends, schedules,
  uploads, auto-starts, saves raw replies, or retains raw answers.
- Read JSON through the existing bounded private-input loader. Reject
  symlinks, duplicate keys, invalid UTF-8/JSON, oversized files, and unsafe
  output paths with concise non-sensitive errors.
- The independent validator accepts only the wrapper plus its nested practice
  session and checks schema, provenance, projected `Q-001/R-001/F-001`
  references, fixed delivery flags, and the existing practice validator.
- Update routing and docs so the handoff path requires v2; legacy v1 fixtures
  remain legacy inputs and are not silently upgraded by the CLI.

## CLI contract

`build_private_recruiter_triage_practice_handoff.py --input INPUT --output OUTPUT`
returns exit code 0 and writes canonical UTF-8 JSON on success. It returns a
non-zero code and a short JSON error object on failure; errors do not echo raw
input, paths beyond the requested basename, IDs, URLs, or prose. Output uses
the existing atomic private writer conventions and refuses overwrite unless
`--force` is explicitly supplied.

## Validation contract

`validate_private_recruiter_triage_practice_handoff.py INPUT` exposes a
`validate_handoff(value)` function returning a list of errors and a CLI that
returns 0 only for an empty error list. It must reject any mutation of wrapper
source snapshot/scope/delivery, nested handoff context, projected references,
locale, or nested practice content.

## Testing and release

Focused tests cover valid ES/EN CLI round trips, malformed JSON, duplicate
keys, symlink and size boundaries, v1 rejection, wrapper mutations, unsafe
prose/HTML, and validator-to-renderer flow. Existing plugin, privacy, static,
release, and root suites remain green. The plugin is reinstalled and its
source/cache parity is re-attested before each published increment.
