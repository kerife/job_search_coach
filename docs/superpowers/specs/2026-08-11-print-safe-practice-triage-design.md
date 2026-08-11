# Print-safe practice and triage surfaces

## Intent

Make candidate-facing practice and private triage artifacts deterministic and
legible when printed or exported to PDF. Print must not capture a partially
animated entrance frame, and the practice next-action panel must remain
readable when print settings omit background graphics.

## Scope

- In `@media print`, disable animation, transition, and transform for the
  practice session and triage card.
- In practice print CSS, set `.practice-next-action` to transparent background,
  `var(--ink)` text, a visible `1px solid var(--ink)` border, and preserve its
  `4px` state marker; set its heading to `var(--ink)`.
- Keep existing page-break, reduced-motion, forced-colors, dark-mode, copy,
  privacy, and no-action behavior unchanged.
- Synchronize the practice and triage raw CSS dumps in `.superdesign/init/theme.md`.

## Acceptance

1. RED tests fail on the current white-on-white/animated print behavior.
2. GREEN tests assert the print rules in rendered EN/ES documents.
3. Plugin, root, privacy, static, release, source/cache, and installed smoke
   gates remain green.
