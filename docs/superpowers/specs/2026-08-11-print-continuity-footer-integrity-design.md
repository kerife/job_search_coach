# Print Continuity Footer Integrity Design

## Context

All five candidate-facing Professional Growth Coach renderers put the
employment-continuity boundary in a footer. Their print styles protect the
main card or evidence sections, but not the footer itself. A browser printing a
long artifact may therefore split the sentence that says the analysis does not
recommend resignation or abandoning the job search away from the decision it
qualifies.

## Decision

Add print fragmentation protection to the existing footer selector in each
surface:

```css
break-inside: avoid;
page-break-inside: avoid;
```

The change is CSS-only. It preserves the current DOM, localized copy, print
visibility, dark/contrast/forced-colors behavior, and no-action boundaries.
The footer remains a single semantic unit; no duplicate disclaimer or new
interactive control is introduced.

## Alternatives and trade-off

Moving the boundary next to each action would change markup and visual order.
Duplicating the boundary would increase copy and screen-reader repetition.
Protecting the existing footer is the smallest change that keeps the safety
sentence attached to the artifact context during print/PDF generation.

## Verification

Static CSS assertions must find both declarations in each of the five relevant
print blocks. Render tests for EN/ES representative artifacts must confirm the
boundary remains present exactly once, is not inside `no-print`, and no STOP
copy or action behavior changes. Browser print-preview evidence remains a
follow-up when a permitted user-opened tab is available.
