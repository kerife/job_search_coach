# Private JSON loader hardening

## Context

Private recruiter triage loaders already bound bytes, reject symlinks, and use
opaque CLI errors, but Python's JSON decoder can raise `ValueError` for an
integer exceeding the interpreter digit limit. One builder also parses without
applying the existing maximum-depth guard. In those cases a traceback can leak
runtime paths and bypass the intended bounded receipt.

## Brainstorm decision

The options were to raise the interpreter limit, catch errors only in each CLI,
or normalize loader failures at the shared input boundary and enforce depth
before validation. The last option is safer and smallest: it preserves the
platform limit, gives library callers the existing typed load errors, and makes
all direct CLIs inherit the same privacy boundary.

## Decision

Update the three private loaders—triage handoff builder, handoff validator, and
reply-triage validator—to catch `ValueError` alongside JSON/recursion errors,
map it to their existing bounded input exception, and apply `_assert_max_depth`
immediately after decoding. Keep valid JSON behavior, schema/semantic
validation, atomic `0600` writes, and opaque CLI envelopes unchanged.

## Acceptance criteria

1. Oversized integer and deeply nested JSON inputs return the existing bounded
   invalid-input envelope, nonzero exit, and no traceback/path/input echo.
2. The builder, handoff validator, and reply-triage validator all enforce the
   same depth boundary before semantic validation.
3. Valid fixtures and existing duplicate-key, symlink, size, and UTF-8 errors
   retain their current codes and behavior.
4. Black-box subprocess tests cover all three loaders with private sentinels;
   library tests confirm typed bounded exceptions.
5. Documentation records the fail-closed loader invariant without exposing
   runtime details or changing user-facing data flow.
