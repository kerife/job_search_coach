# Schema combinator branch-shape guard

## Problem

The public dependency-free schema validator assumes every nested combinator
branch is an object. JSON-compatible caller input such as `{"oneOf": [null]}`
therefore raises a Python exception instead of returning validator diagnostics.

## Design

At the recursive `_validate` boundary, reject any non-mapping schema value with
the fixed message `schema branch is invalid`. This single guard covers branches
under `oneOf`, `anyOf`, `allOf`, `if`, `then`, `else`, and `not`, without
changing valid branch behavior, evaluation budgets, `$ref` handling, or the
canonical schemas loaded by the plugin.

## Success criteria

- Non-object branches return `schema branch is invalid` and never raise.
- All five exposed combinator families are covered by regression tests.
- Existing schema conformance, handoff, plugin, static, privacy, and release
  gates remain green before publishing.

