# Case Parent Descriptor Lifecycle

## Context

`validate_case.py` walks parent directories with `O_NOFOLLOW` and validates
each opened directory before adopting its descriptor. If `os.fstat()` or the
directory-type check raises after the child descriptor is opened, the outer
error handler closes only the previously adopted descriptor. The child file
descriptor remains open until process exit, creating a repeatable resource
leak under filesystem or mocked-`fstat` failures.

## Design

Keep the existing descriptor walk, trusted `/tmp` and `/var` compatibility,
lexical path normalization, regular-file check, bounded read, and fixed error
messages. Treat each newly opened parent descriptor as provisional: close it on
every validation failure, and adopt it only after `fstat()` confirms a
directory. The successful path must close the prior descriptor exactly once.

## Boundaries

- No schema, renderer, case-field, provenance, or CLI diagnostic changes.
- No change to accepted regular paths, final-component no-follow behavior, or
  the 64,000-byte input limit.
- The test must validate descriptor ownership deterministically without a live
  race or platform-specific filesystem assumptions.

## Acceptance

1. RED reproduces a failed parent `fstat()` and observes an opened descriptor
   that is not closed.
2. GREEN closes every provisional descriptor on failure and keeps successful
   parent traversal green.
3. Existing case boundary, privacy, static, release, and installed smoke gates
   remain green.
