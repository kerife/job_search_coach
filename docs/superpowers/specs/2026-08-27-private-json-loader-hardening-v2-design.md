# Uniform private JSON loader hardening v2

## Decision

Close the remaining JSON parse boundary in four private validators:
`validate_private_recruiter_followthrough_checkpoint.py`,
`validate_recruiter_practice_session.py`, `validate_executive_career_dossier.py`,
and `validate_executive_career_dossier_v2.py`. Their loaders already enforce
bounded descriptor-anchored reads, UTF-8, duplicate-key rejection, and maximum
depth; the missing case is Python's `ValueError` from oversized integer parsing.

Catch that error at the JSON boundary and map it to the validator's existing
opaque typed load error. Renderers inherit the fix through their existing typed
error handling. Do not change schemas, accepted values, HTML, CSS, artifacts,
storage, or external actions.

## Security contract

- Oversized integers, invalid UTF-8, malformed JSON, duplicate keys, excessive
  depth, symlink inputs, and oversized files must fail closed.
- CLI failures use the existing return code `3`, fixed stderr diagnostics,
  empty stdout, no traceback, no raw input echo, and no path/ID reflection.
- Valid inputs render exactly as before and remain deterministic.

## Acceptance criteria

1. Each of the four validators maps oversized integer `ValueError` to its typed
   load error in both direct loader and CLI paths.
2. Renderer CLIs for practice and dossier v1/v2, plus checkpoint, fail closed
   with their existing opaque diagnostics for the same corpus.
3. Regression tests cover all four validators, both valid and invalid states,
   and the existing UTF-8/depth/symlink/size boundaries.
4. Plugin/root static, privacy, release, and full suites pass without changing
   schema or public copy contracts.
