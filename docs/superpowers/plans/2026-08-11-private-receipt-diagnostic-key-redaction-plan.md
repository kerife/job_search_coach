# Plan: private receipt diagnostic-key redaction

1. Add RED tests to the checkpoint and conversion-outcome validator suites for
   suspicious unknown keys and an ordinary `extra` key.
2. Import `safe_diagnostic_field_name` from `private_prose_safety` and apply it
   only when formatting unsupported-field diagnostics in both `_closed`
   helpers.
3. Run focused validator tests, the plugin suite, root privacy/static checks,
   and the official release validator.
4. Bump the plugin once, install the canonical local package, recompute the
   source/cache inventory hash, refresh smoke/provenance sidecars, and verify
   the installed cache before handoff.

No browser capture is required: this increment changes only validator
diagnostics and does not alter rendered UI.
