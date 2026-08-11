# Case Input Error Redaction Design

## Context

The case CLI currently interpolates the exception raised while reading its
input file. An unreadable path can contain an email, token-like segment, or
private filename, so a rejected invocation can echo sensitive material to
stderr.

## Decision

Handle `OSError` separately from content errors and return the fixed message
`invalid case file: unable to read input`. Do not include the path or the
original exception text. Keep malformed JSON, invalid UTF-8, and recursion
errors deterministic and bounded; this change does not alter case schemas,
validation semantics, or rendered artifacts.

## Verification

The CLI regression invokes the validator with a missing sentinel-bearing path,
expects exit code 2 and the fixed message, and asserts the sentinel is absent.
The existing case-validator suite and repository privacy checks remain green.
