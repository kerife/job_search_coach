# Case Duplicate-Key Guard Design

## Goal

Make `validate_case.py` fail closed when a case JSON document contains
duplicate object keys, so hidden or overwritten private content cannot pass the
case contract through last-write-wins parsing.

## Design

Add a small `object_pairs_hook` used only by the case CLI loader. It raises a
bounded internal duplicate-key error at the first repeated key, including no
key name or input value in its public diagnostic. `main()` catches that error
with the existing parse/read failures and returns `2` with exactly the generic
prefix `invalid case file: duplicate JSON key`.

The hook applies recursively because `json.loads` invokes it for every JSON
object. Normal unique-key cases, nested mappings, privacy scanning, and all
existing validation behavior remain unchanged.

## Alternatives

- Post-parse duplicate detection is rejected: the standard decoder has already
  discarded the earlier value.
- Scanner-only detection is rejected: callers of the case CLI would still
  accept ambiguous input.
- A shared loader refactor is rejected: this boundary is local to `validate_case`
  and does not justify changing unrelated artifact loaders in this increment.

## Acceptance

- Duplicate top-level and nested keys return `rc=2` and the generic diagnostic.
- The diagnostic does not echo the duplicate key, URL, or private payload.
- Valid case fixtures remain `rc=0`; malformed JSON keeps its existing bounded
  parse error behavior.
- Focused, static, privacy, full, release, publish, and install gates remain
  green.
