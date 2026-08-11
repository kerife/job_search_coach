# Case Diagnostic Boundary

## Context

The case input is now bounded to 64,000 bytes, but thousands of unsupported
fields can still expand CLI stderr to hundreds of kilobytes. A single long
ordinary key can also be echoed nearly in full. This is a diagnostic resource
amplification risk and can pollute logs or terminal output.

## Design

Keep `validate_case()`'s list API unchanged for internal callers and tests. At
the CLI boundary, format diagnostics as complete newline-delimited records with
a 16,384-byte UTF-8 budget. Preserve the existing output byte-for-byte when it
fits. If records exceed the budget, emit only complete lines that fit after a
fixed final notice:

`validation diagnostics truncated; additional errors omitted`

If the next individual record cannot fit, omit it rather than splitting UTF-8
or control sequences. The formatter must never interpolate paths or input
content beyond the already-generated diagnostic text.

## Boundaries

- No schema, validation semantics, renderer, or API list changes.
- Existing short error assertions remain exact.
- The separate intermediate-parent symlink/descriptor-walk hardening remains a
  follow-up cycle.

## Acceptance

1. A 4,000-key case produces stderr no larger than 16,384 bytes and includes the
   fixed truncation notice without the final key.
2. A single oversized diagnostic key is bounded and not echoed in full.
3. A multibyte diagnostic is never split and output remains valid UTF-8.
4. Existing short diagnostics remain unchanged and deterministic.
