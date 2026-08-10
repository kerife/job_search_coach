# Run private schema conformance in the release gate

## Goal

Ensure the dependency-free private schema conformance harness is executed by
the repository's full integration suite rather than only by a manually named
test module.

## Design

Add one integration test in `tests/test_full_plugin.py` that loads the harness
from the plugin test directory, executes its unittest module through the normal
test command, and asserts that the valid fixtures pass and a representative
schema mutation fails. Keep the harness itself unchanged and avoid spawning a
subprocess or adding dependencies; this is a release-discovery assertion, not a
second validator.

## Verification

The integration test passes in the full suite and fails if the harness module is
missing or no longer rejects the mutation. Existing focused schema/runtime and
static tests remain green.
