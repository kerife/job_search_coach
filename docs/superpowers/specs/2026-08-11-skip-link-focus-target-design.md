# Focusable skip-link targets

## Context

The dossier, recruiter-practice, and triage renderers expose a skip link to
`#main-content`, but their main elements are not programmatically focusable.
Keyboard and assistive-technology users can scroll to the fragment without
getting a reliable focus destination or context.

## Design

Add `tabindex="-1"` to the existing `<main id="main-content">` in all three
long-form renderers. Keep the same IDs, copy, landmark order, CSS, CSP, and
offline behavior. Do not add JavaScript or a new focus style: the target is a
non-interactive focus destination and existing descendant `:focus-visible`
styles remain unchanged.

## Contract

- Each long-form EN/ES render has exactly one skip link and one matching main
  target with `tabindex="-1"`.
- Compact receipts are unchanged.
- No new IDs, text, forms, remote resources, or action controls are emitted.

## Verification

Focused renderer tests cover dossier, practice, and triage output. Existing
static, privacy, schema, full-suite, print, and installed-plugin gates remain
required before publication.
