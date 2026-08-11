# Plan: Privacy Validator Loader

1. Run the existing privacy regression tests and capture the two false-positive
   failures (RED).
2. Add the temporary sibling-directory `sys.path` scope with `finally`
   restoration (minimal GREEN implementation).
3. Run privacy, root, plugin, static, release, and diff checks.
4. Refresh allowlisted provenance, consume the cachebuster once, publish,
   install, and verify source/cache identity.
