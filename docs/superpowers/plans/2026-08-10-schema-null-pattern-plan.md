# Implementation plan: nullable pattern handling

1. Add focused RED tests for the nullable pattern case, matching/non-matching
   strings, a string-only type mismatch, and the canonical dossier fixture.
2. Run the focused tests and confirm they fail because the checker applies the
   pattern to `null`.
3. Change the checker to evaluate `pattern` only for string instances after
   type validation.
4. Run the focused suite, plugin discovery, static/privacy/release gates, and
   `git diff --check`.
5. Review the diff for scope/privacy, refresh final provenance, consume the
   cachebuster once, commit the release, reinstall the exact marketplace
   version, and rerun installed-cache verification.
