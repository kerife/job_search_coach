# Case Sensitive-Key Diagnostic Redaction Design

## Context

The isolated case validator rejects sensitive keys and unsupported fields, but
its path diagnostics currently interpolate the complete caller-supplied key.
Malformed input such as an email-shaped or token-shaped key can therefore be
copied into stderr or logs even though the case is rejected.

## Decision

Keep diagnostics path-specific, but replace any non-canonical key segment that
matches a sensitive-key or credential-shaped classifier with
`<redacted-key>`. Canonical sensitive names already used by the contract (for
example `password` and `api_key`) remain readable because they contain no
caller-specific material. Unsupported non-sensitive names retain their current
diagnostics for compatibility.

Apply the safe segment when constructing closed-mapping, JSON-domain,
sensitive-data, and identity-field paths. This prevents an unsafe key from
reappearing through a later recursive validation error.

## Behavior and compatibility

Cases containing sensitive or credential-shaped keys remain rejected. Their
diagnostics remain deterministic and identify the affected location without
echoing the supplied key. Existing canonical path wording and non-sensitive
unsupported-field wording remain unchanged. No schema version or action-boundary
behavior changes.

## Verification

The regression matrix inserts synthetic email-, contact-, and token-shaped
unsupported keys at top-level, target, and record scopes. Each case must fail
validation while its sentinel is absent from stderr. Existing case-validator
tests must remain green.
