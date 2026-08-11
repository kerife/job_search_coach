# Dossier Dark Progress Contrast

## Context

The dossier renders semantic `<progress>` bars for score dimensions. In dark
mode the fill remains `--forest: #8fc9b0`, but the track changes with the muted
token to `#b8c4d8`, producing only about 1.07:1 non-text contrast. The bar's
filled and unfilled states therefore visually merge.

## Design

Keep the light palette unchanged. Inside the dossier's screen-only dark block,
set the progress track and WebKit track pseudo-element to
`var(--forest-soft)` while retaining the existing forest fill. Also set the
Mozilla progress fill explicitly to preserve the semantic fill across engines.
The declared dark tokens must be used by the accessibility test to calculate a
minimum 3:1 non-text contrast ratio.

## Boundaries

- No DOM, accessible names, fallback text, copy, schema, or action changes.
- Print, reduced-motion, forced-colors, and light-mode rules remain unchanged.
- Sync the raw dossier CSS dump in `.superdesign/init/theme.md` exactly.

## Acceptance

1. RED proves the dark block lacks explicit track overrides and contrast is
   below 3:1.
2. GREEN declares track overrides for `progress` and WebKit/Mozilla behavior.
3. The test derives `--forest` and `--forest-soft` from the dark block and
   proves contrast >=3:1.
4. Existing semantic progress tests, theme parity, render, static, plugin,
   release, and installed smoke checks remain green.
