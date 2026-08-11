# Implementation plan: compact receipt breakpoint

1. Add RED static tests that parse both compact CSS assets and require a
   strictly-greater-than-640px media query for the two-column facts grid.
2. Change both CSS assets from `min-width: 40rem` to `min-width: 641px`.
3. Update the compact breakpoint statement and raw CSS dumps in
   `.superdesign/init/theme.md`.
4. Run compact renderer tests, design-token/parity/static/privacy/root gates.
5. Bump the plugin once, install it, run five installed renderer smokes, refresh
   hash/attestation/provenance, and verify a clean checkout.
