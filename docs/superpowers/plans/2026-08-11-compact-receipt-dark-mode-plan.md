# Compact receipt dark-mode implementation plan

1. Add RED assertions to checkpoint and outcome renderer tests for the
   screen-only dark-mode hook and shared tokens.
2. Add the same dark token override to both compact receipt stylesheets and
   synchronize the two raw CSS dumps in `.superdesign/init/theme.md`.
3. Run focused receipt/theme tests, plugin tests, privacy/static/release gates,
   and the full repository suite.
4. Commit the functional change, consume one cachebuster, bind final eval
   provenance, install the exact version, compare source/cache, and record a
   fresh installed smoke attestation.
