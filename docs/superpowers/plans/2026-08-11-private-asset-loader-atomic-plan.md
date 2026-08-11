# Plan: atomically read private renderer assets

1. Add one RED regression to `test_private_asset_loader.py` that swaps the
   validated asset to an external symlink before the loader's read step and
   asserts `PrivateAssetError` without external bytes in the error.
2. Run that focused test and record the expected failure against the current
   pathname-based `read_text` implementation.
3. Replace the second pathname open with an `os.open` descriptor walk: root and
   intermediate directories use `O_DIRECTORY|O_NOFOLLOW`, the leaf uses
   `O_NOFOLLOW`, and `fstat` enforces regular-file plus single-link invariants.
4. Read/decode from the opened descriptor and close all descriptors through
   success, decode failure, and OS-error paths.
5. Run focused loader/render tests, the plugin suite, static/schema/privacy
   gates, the locked release validation script, and `git diff --check`.
6. Bump the plugin cachebuster once, install the canonical marketplace entry,
   compare source/cache byte-for-byte, run installed smoke fixtures, refresh
   the installation attestation and final-evaluation provenance, then rerun
   the final gates.
