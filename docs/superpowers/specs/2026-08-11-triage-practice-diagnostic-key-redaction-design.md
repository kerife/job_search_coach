# Triage and Practice Diagnostic Key Redaction

## Context

The case validator now protects diagnostic paths, but the private triage and
recruiter-practice validators still interpolate unknown mapping keys verbatim.
An input key such as an email address, local path, or token-shaped label can
therefore appear in CLI stderr even though the artifact is rejected.

## Design

Add a small field-name sanitizer to `private_prose_safety.py` and use it only
when `_closed` or the top-level closed-mapping checks format unsupported keys in
`validate_private_recruiter_reply_triage.py` and
`validate_recruiter_practice_session.py`.

The sanitizer preserves short ordinary schema mistakes such as `extra` and
`unsupported_claim` so existing diagnostics remain useful. It returns the
fixed marker `<redacted-field>` for keys containing contact/credential/path
signals (email or phone punctuation, URL/local-path syntax, or sensitive terms
such as token, secret, password, credential, auth, cookie, or private key).
Classification is performed on the original key; the marker is the only value
that reaches the error string. No schema, renderer, handoff, prose scan, or
error-list API semantics change.

## Acceptance

1. Triage and practice reject injected email, local-path, and token-shaped
   unsupported keys without echoing any supplied value.
2. Ordinary unsupported names retain their current path-specific diagnostics.
3. The shared helper has focused unit coverage and both validators' CLI/error
   tests remain green.
4. Renderers continue to fail closed and never include the rejected key.
