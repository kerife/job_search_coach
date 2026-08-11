# Compact receipt contrast implementation plan

1. Add RED assertions to the two compact receipt renderer test modules for the
   `prefers-contrast: more` hook and required selectors.
2. Run the focused tests and confirm they fail because the hook is absent.
3. Add the minimal CSS blocks to the checkpoint and outcome assets.
4. Run focused tests, plugin tests, static/privacy/release gates, and diff
   checks.
5. Commit the functional change, refresh provenance, consume the cachebuster
   once, publish, install, and verify source/cache identity plus synthetic
   receipts.
