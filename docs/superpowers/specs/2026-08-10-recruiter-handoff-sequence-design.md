# Recruiter handoff sequence

## Goal

Make the ready handoff's decision path legible at a glance on desktop, mobile,
and print.

## Design

Wrap the existing readiness, preparation-focus, and manual-next-step sections
in a semantic ordered list with fixed visible step labels: `01 Conditions`,
`02 Focus`, and `03 Manual re-entry`. The existing fact/question preview stays
inside step 03 as an inset, not as a fourth decision step. No section content,
schema, routing, or copy safety rules change.

The sequence uses text labels and borders, not color alone. It remains a
single-column reading order on narrow screens, keeps print blocks together, and
adds a forced-colors outline fallback. Clarify and stop states retain their
current non-handoff layout.

## Verification

Tests assert ordered structure, exact step labels/order, ready-only rendering,
clarify/stop omission, no interactive markup or unsafe prose, forced-colors
CSS, mobile/print hooks, accessibility labeling, escaping, and deterministic
bytes.
