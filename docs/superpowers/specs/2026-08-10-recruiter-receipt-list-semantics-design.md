# Recruiter receipt list semantics design

## Goal

Make the ready-only handoff receipt semantically scannable by using two labeled lists instead of repeated definition-list labels.

## Design

Keep the existing `Bring`/`Do not bring` (and Spanish equivalents) headings and four fixed privacy-boundary items. Each group becomes a labeled `<ul>` with exactly two `<li>` elements. No user data, schema fields, IDs, links, controls, or routing behavior change.

## Acceptance

EN/ES ready output has two `aria-labelledby` groups, two list items per group, no `dt`/`dd` within the receipt, and the allowed group precedes the prohibited group. Clarify/stop omit the receipt. Existing responsive, print, forced-colors, escaping, and no-action tests remain green.
