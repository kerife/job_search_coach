# Plan: require conversion CLI reference dates

1. Add failing CLI tests proving missing `--as-of` is rejected for validator and
   renderer.
2. Make the existing parser option required with minimal changes; retain direct
   library compatibility and run focused tests.
3. Run static/provenance checks, publish once, install exact version, and smoke
   invalid/missing/help/date paths.
