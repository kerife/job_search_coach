# Triage prefers-contrast support

## Context

The Professional Growth Coach design system requires `prefers-contrast: more`
support. The dossier and practice surfaces implement it, but the private
recruiter-triage stylesheet only covers reduced motion, print, and forced
colors. Its stop, next-safe-action, and blocked panels therefore rely on the
normal color/border hierarchy when a user requests increased contrast.

## Design

Add one `@media (prefers-contrast: more)` block to the triage stylesheet. Keep
the existing editorial palette and copy, but strengthen the semantic panels:

- state badges and triage sections use a minimum 2px border;
- stop, next-safe-action, and blocked panels retain explicit visible border
  hierarchy;
- headings in those panels are underlined so the distinction is not color-only.

The block is additive and scoped to the existing document class. It does not
alter layout, print rules, forced-colors behavior, reduced-motion behavior,
ARIA, privacy, or external-action boundaries.

## Verification

1. Add a RED static CSS test for the missing media query and semantic selectors.
2. Add bilingual render assertions that the stop copy remains recruiter-scoped
   and still includes the employment-continuity disclaimer.
3. Implement the CSS-only block and run the triage/practice renderer suites,
   plugin/static/privacy/release gates, and the full repository suite.
4. Consume one cachebuster, install the new marketplace version, compare source
   and cache byte-for-byte, and run installed validation.

