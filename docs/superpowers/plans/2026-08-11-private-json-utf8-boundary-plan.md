# Implementation plan: private JSON UTF-8 boundary

1. Add RED tests that write invalid UTF-8 bytes and invoke each private loader
   CLI, asserting code 3, no traceback, and the generic surface error.
2. Extend each loader's read/decode exception boundary with `UnicodeError`.
3. Run focused loader tests, the complete plugin suite, static/privacy checks,
   and the relevant root integration tests.
4. Bump the plugin cache version once, install the canonical plugin, render the
   five installed smoke artifacts, and verify source/cache inventory and hash.
5. Refresh installed attestation and cycle provenance, then rerun release gates
   with a clean worktree.
