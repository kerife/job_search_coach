# Long Surface Dark-Mode Implementation Plan

1. Add RED static assertions for dossier, practice, and triage dark media,
   token values/order, print-light rules, forced-colors system colors, and
   theme dump parity; add render assertions for EN/ES boundary preservation.
2. Add the scoped dark token blocks and hardcoded-panel overrides to the three
   CSS assets, then synchronize their raw dumps in `.superdesign/init/theme.md`.
3. Run focused render/design-token tests, plugin/static/privacy/release gates,
   and the complete repository suite.
4. Cache-bust once, install once, verify source/cache parity and dark contract
   in the installed tree, refresh provenance/smoke attestation, and rerun all
   gates. Browser screenshots remain a separate manual acceptance step if the
   file URL policy permits them.
