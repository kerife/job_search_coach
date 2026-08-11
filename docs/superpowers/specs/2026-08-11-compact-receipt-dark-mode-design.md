# Compact receipt dark-mode design

## Intent

Make the two compact private receipts truthful when they declare
`color-scheme: light dark`. The dark treatment is a screen-only presentation
variant; it must not change receipt meaning, continuity copy, privacy behavior,
print output, or forced-colors semantics.

## Visual direction

- Keep the existing compact receipt geometry: centered 48rem shell, rounded
  card, two-column facts above 40rem, left-accent boundary, and local footer.
- On `screen` with `prefers-color-scheme: dark`, use a deep blue-gray document
  background, a raised blue-gray card surface, light primary text, muted light
  labels, a readable light-blue accent, and a visible slate divider.
- Use the shared dark tokens `#101521` (canvas), `#182235` (surface),
  `#f3f6ff` (ink), `#b8c4d8` (muted), `#8eb2ff` (accent), and `#5f718e`
  (line); declare `color-scheme: dark` inside the screen-only media query.
- Keep the existing light tokens as the default and keep `@media print` light.
- Keep `@media (prefers-contrast: more)` and `@media (forced-colors: active)`
  after the dark block so accessibility modes remain authoritative.

## Boundaries

- No new controls, links, scripts, remote assets, or dynamic data.
- No renderer, schema, or copy changes.
- Both checkpoint and conversion-outcome CSS must implement the same semantic
  token values, and `.superdesign/init/theme.md` must contain exact raw dumps.

## Acceptance

1. EN and ES checkpoint/outcome render tests find the screen dark-mode hook and
   the shared dark token values.
2. Existing print, contrast, forced-colors, privacy, and no-action tests stay
   green.
3. Theme/source parity remains byte exact.
4. Full plugin and repository gates pass before one cachebuster, install, and
   source/cache comparison.
