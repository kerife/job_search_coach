# Case Diagnostic Unicode Safety

## Context

The case validator already bounds input size and escapes C0/DEL characters in
unsupported-field diagnostics. A JSON key containing an unpaired Unicode
surrogate is still accepted by `json.loads`, then crashes diagnostic encoding
with `UnicodeEncodeError` and exits with a traceback. Unicode line and
paragraph separators can also be interpreted as record breaks by log tools.

## Design

Extend `_escape_diagnostic_controls` in
`plugins/professional-growth-coach/scripts/validate_case.py` so diagnostic path
segments escape exactly these Unicode categories as `\\uXXXX` code units:

- `Cc`: C0/C1 control characters and DEL;
- `Cs`: isolated surrogate code points;
- `Zl` and `Zp`: line and paragraph separators.

The helper runs before a path segment reaches `_format_diagnostics`, while
sensitive-key classification continues to inspect the original key. Ordinary
Unicode labels, accents, combining marks, and printable punctuation remain
unchanged. Validation semantics, the `validate_case()` list API, input limits,
diagnostic byte cap, schemas, renderers, and release behavior are unchanged.

## Acceptance

1. A case with an unpaired surrogate in an unsupported key returns `rc=2` with
   one bounded diagnostic line and no traceback or raw surrogate.
2. U+2028 and U+2029 in unsupported keys are escaped and cannot split a
   diagnostic record in `str.splitlines()` or a log processor.
3. Existing C0/DEL, accent, combining-mark, sensitivity, and short-diagnostic
   assertions remain unchanged.
4. The source and installed cache expose the same helper behavior.
