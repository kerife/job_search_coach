# Case Diagnostic Format-Control Escaping

## Context

`validate_case.py` already escapes control, surrogate, and Unicode line
separator characters before writing unsupported-key diagnostics. Unicode format
characters (`Cf`) such as bidi overrides, isolates, and zero-width markers are
still emitted literally. A rejected field name containing one of these marks
can visually reorder or hide diagnostic text in a terminal, log viewer, or
review UI.

## Design

Extend `_escape_diagnostic_controls` to treat Unicode category `Cf` exactly
like the existing diagnostic-safe categories. Emit a stable lowercase
`\\uXXXX` escape for each such code point. Keep the original value for
classification, preserve ordinary field names, and leave the validator error
list API unchanged.

## Boundaries

- No schema, renderer, case semantics, or input-size changes.
- Preserve existing escaping for `Cc`, `Cs`, `Zl`, and `Zp`.
- Keep diagnostic byte caps and short ordinary messages byte-for-byte stable.

## Acceptance

1. RED reproduces raw bidi/zero-width format characters in CLI diagnostics.
2. GREEN emits escaped `\\uXXXX` sequences and no raw format characters.
3. Case validator, plugin, privacy, static, release, installed smoke, and
   source/cache parity gates remain green.
