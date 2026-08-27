# Plan: feedback-sensitive continuity rail

## Task 1 — renderer contract and tests

- Extend the closed continuity copy and renderer signature with validated
  `state` and `governing_label` inputs.
- Pass the already-derived governing label only for `feedback_available`.
- Add bilingual label/kind matrix tests, pre-feedback regression tests, ordering,
  deterministic output, and privacy/control sentinels.

## Task 2 — CSS, theme parity, and documentation

- Add minimal state-specific rail styles while preserving responsive, print,
  forced-colors, contrast-more, and reduced-motion contracts.
- Copy the exact CSS contract into `.superdesign/init/theme.md`.
- Update README and `skills/prepare-role-interviews/SKILL.md` with the static
  continuity boundary.
- Run CSS parity and documentation/static checks.

## Task 3 — release and publication

- Bump the plugin cachebuster and install the local plugin.
- Verify source/cache parity, normalized digest, installed smoke behavior, and
  all plugin/root/privacy/release suites.
- Produce a provenance attestation whose `source_commit` is the immediate
  parent of the attestation commit.
- Obtain an independent release review, then push `HEAD:main` and verify the
  remote ref.
