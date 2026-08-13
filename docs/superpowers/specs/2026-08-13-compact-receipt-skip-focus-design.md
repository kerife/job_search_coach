# Compact receipt skip-link focus design

## Problem

The conversion-outcome and follow-through-checkpoint receipts expose a
keyboard skip link, but their forced-colors blocks only style the main focus
target. A user navigating with Windows High Contrast or another forced-colors
mode has no explicit system focus indicator for the skip link.

## Decision

Add the same forced-colors treatment to both compact receipt stylesheets:

```css
.skip-link {
  background: Canvas;
  border-color: CanvasText;
  color: CanvasText;
}

.skip-link:focus-visible {
  outline: 2px solid Highlight;
  outline-offset: 2px;
}
```

The rules live inside the existing `@media (forced-colors: active)` block.
The normal palette, markup, copy, layout, JavaScript, schema, and print rules
remain unchanged. The exact CSS is mirrored in `.superdesign/init/theme.md`.

## Verification

Add a parametrized static test that extracts each forced-colors block and
requires the system colors and explicit `:focus-visible` Highlight outline.
Run the dark-mode/accessibility and Superdesign parity tests, both compact
renderers, the full plugin suite, static/privacy/release validators, and the
installed-cache smoke checks. Browser/OS forced-colors rendering remains a
separate manual QA item because this environment has no browser engine.
