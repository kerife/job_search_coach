# Case Input Boundary Hardening

## Context

`validate_case.py` currently reads the caller-supplied path with
`Path.read_text()`. A symlink can redirect that read outside the intended input
file, a symlink to a streaming device can block indefinitely, and an oversized
JSON document can spend seconds in recursive sensitive-value regex checks.

## Design

Introduce a 64,000-byte maximum for case input and read through a validated file
descriptor. Open the path with `O_RDONLY | O_CLOEXEC | O_NOFOLLOW`, require a
regular file with `fstat`, read at most `MAX_CASE_BYTES + 1`, and reject any
payload that exceeds the limit before JSON parsing. Decode the bounded bytes as
UTF-8, then preserve the existing duplicate-key and validation behavior.

The email-shaped classifier is also skipped when the normalized value contains
no `@`, and its local/domain/TLD quantifiers are bounded to practical email
lengths. Together these prevent quadratic backtracking on long ordinary prose
or malformed email-shaped input.

Use fixed diagnostics:

- oversized input: `invalid case file: input exceeds safe size limit`
- symlink, device, race, or other open/read failure:
  `invalid case file: unable to read input`

Do not interpolate the path, payload, errno, or external target into stderr.
Fail closed if the platform lacks `O_NOFOLLOW`; this contract targets the
macOS runtime used by the plugin.

## Boundaries

- No schema, case-field, identity, provenance, or renderer changes.
- Regular UTF-8 JSON at or below the limit keeps existing behavior.
- JSON parse errors remain bounded by the existing parse diagnostic.
- The symlink and size protections are scoped to `validate_case.py`; analogous
  private loaders remain a separate hardening cycle.

## Acceptance

1. RED proves a symlink input is rejected, including a symlink to a valid case.
2. RED proves a payload above 64,000 bytes is rejected before recursive scans.
3. GREEN uses descriptor-based no-follow, regular-file, and bounded-read checks.
4. Tests assert no path, target, or oversized payload is echoed.
5. Static, privacy, full plugin, release, installed smoke, and source/cache
   parity checks remain green.
