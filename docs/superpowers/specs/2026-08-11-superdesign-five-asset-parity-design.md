# Superdesign Five-Asset Parity

## Context

`.superdesign/init/theme.md` contains raw CSS dumps for five shipped
Professional Growth Coach surfaces, but the automated parity test compares
only the dossier, practice, and triage files. The two compact receipt assets
can therefore drift in print, dark-mode, or forced-color rules without a test
failure. A temporary mutation of a compact dump reproduces this blind spot.

## Design

Expand the parity contract to the five supported CSS assets and make the test
derive the theme's CSS headings before comparing content. Assert that the set
of theme dumps exactly equals the set of shipped asset filenames, then compare
each dump byte-for-byte. This is a test-only hardening change; no CSS, renderer,
copy, schema, or runtime behavior changes.

## Boundaries

- Keep the raw dump format and existing exact comparisons.
- Reject both missing and extra theme CSS headings.
- Do not use browser screenshots as evidence for this regression guard; the
  test proves source/dump synchronization only.

## Acceptance

1. RED demonstrates that mutating either compact dump is currently invisible to
   the three-asset test.
2. GREEN compares all five dumps and rejects missing/extra asset headings.
3. Existing renderer, design-token, static, release, and installed smoke gates
   remain green.
