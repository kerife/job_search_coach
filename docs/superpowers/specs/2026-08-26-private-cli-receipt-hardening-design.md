# Private CLI receipt hardening

## Context

The direct practice renderer and validator are private-data boundaries, but
their standard `argparse` error path echoes unknown argument values and the
renderer success receipt currently prints the output path and a chat summary
derived from question text. Terminal logs, CI transcripts, or Codex tool output
can therefore retain data that the HTML boundary correctly omits.

## Brainstorm decision

Three options were considered: (1) leave the CLI contract unchanged and rely on
local terminal hygiene, (2) redact only known sensitive patterns, or (3) make
the CLI boundary opaque with a private parser and fixed receipts. Option 3 is
the smallest durable policy: redaction lists cannot anticipate arbitrary private
values, while a fixed receipt removes the data channel entirely. Library callers
retain the richer `RenderReceipt` and `build_chat_summary` API; only CLI output
changes.

## Decision

- Direct renderer CLI success emits only stable artifact kind/type and locale;
  it never emits an output path, summary, question, answer, IDs, snapshots, or
  action result.
- Renderer and validator CLIs parse arguments without allowing standard parser
  diagnostics to echo supplied values. Invalid arguments return a stable,
  bounded error envelope and nonzero exit code.
- Existing library APIs, validation semantics, file permissions, and wrapper
  receipts remain unchanged.
- Error output is fixed/bounded and cannot reflect the rejected argument or
  input prose.

## Acceptance criteria

1. Valid direct renderer CLI output contains only the opaque receipt fields and
   no private path or question summary.
2. Unknown/invalid arguments for both CLIs never echo sentinel values,
   URL/contact/path/credential-looking strings, or parser usage containing them.
3. Library callers can still use `RenderReceipt.artifact_path` and
   `build_chat_summary` as before.
4. Existing wrapper and HTML privacy tests remain green; subprocess tests cover
   success and failure for both CLIs.
5. README and relevant skill reference document the opaque CLI boundary.
