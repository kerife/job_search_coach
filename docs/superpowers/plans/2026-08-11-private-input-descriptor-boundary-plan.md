# Plan: descriptor-anchored private input boundary

1. Add RED tests covering intermediate parent symlinks for all six loaders,
   preserving direct symlink rejection and regular-file acceptance.
2. Add the shared descriptor reader with reason-coded failures and bounded
   reads; keep each validator's current error wording and JSON semantics.
3. Run focused loader tests, the plugin suite, root/static/privacy/official
   gates, and a race-safe installed smoke against the canonical cache.
4. Bump the plugin once, reinstall from the local marketplace, recompute the
   107-file source/cache hash, refresh provenance/attestation, and verify a
   clean worktree.

No browser capture is required: this increment changes private input
validation, not rendered UI.
