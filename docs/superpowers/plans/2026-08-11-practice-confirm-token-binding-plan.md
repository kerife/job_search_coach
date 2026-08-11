# Practice Confirm Dark Token Binding Plan

1. Add a regression assertion that extracts `--gold-soft` from the dark root,
   resolves `--ink`, and uses those values for the contrast calculation.
2. Run the focused test to capture RED while the token is absent.
3. Add the single dark token declaration to the practice CSS and its
   Superdesign raw dump.
4. Run dark-mode, theme-parity, practice-renderer, static, and plugin suites.
5. Bump the plugin once, install it, compare source/cache inventories and hash,
   refresh provenance/attestation, and run installed smoke plus release gates.
