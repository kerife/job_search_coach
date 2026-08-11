# Isolated Privacy Validator Loading

## Context

The repository privacy checker loads the recruiter-practice validator through
`importlib` from a file path. The validator imports the sibling
`private_prose_safety` module, but the loader does not expose its `scripts/`
directory during module execution. The import failure is swallowed and the
checker falls back to raw scanning, producing false `SECRET_ASSIGNMENT`
violations for a valid fixture.

## Design

Update only the privacy checker's isolated loader. Immediately before
`exec_module`, temporarily prepend the validator's parent directory to
`sys.path`; in a `finally` block restore the exact previous path list. This
allows the validator's real prose-safety dependency to load while avoiding
global path contamination after the isolated import. Existing error handling,
redaction, validator behavior, and fixture content remain unchanged.

## Verification

The existing privacy tests are the RED regression: they fail with two false
`SECRET_ASSIGNMENT` findings before the fix. They must pass after the fix,
along with the repository privacy CLI, full root suite, static checks, and
release validation. The loader must leave `sys.path` unchanged after success
and import failure.
