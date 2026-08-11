# Plan: show employment continuity in normal practice flows

1. Add RED renderer tests for all normal practice states and triage ready/
   clarify states in English and Spanish; assert the stop copy remains exact
   and no duplicate boundary appears.
2. Run the focused tests and confirm the current footers fail the new contract.
3. Add only localized `employment_boundary` copy and footer rendering to the
   practice and triage renderers.
4. Run focused render/validator tests, the full plugin/root suites, static,
   privacy, and locked official release validation.
5. Bump the cachebuster once, install the canonical marketplace entry, compare
   source/cache, run installed smoke, refresh attestation/provenance, and run
   final gates.
