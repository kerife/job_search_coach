# Recruiter handoff input receipt

## Goal

Make the manual re-entry boundary explicit by showing exactly what private
preparation may receive next.

## Design

Inside step 03 of the ready-only handoff sequence, render a compact localized
receipt before the fact/question preview. It has two fixed “bring” rows:
identity-free role/reply summary and one verified fact; two fixed “do not
bring” rows: raw recruiter text/identity and calendar or contact details; and a
fixed sentence that practice starts only after manual re-entry. It derives no
new user data and adds no schema fields.

The handoff aside references its existing scope/privacy paragraph with
`aria-describedby`; visual step numbers remain decorative while `<ol>` order
is the spoken structure. Clarify/stop omit the receipt. No buttons, links,
auto-start, persistence, scores, or outcome language are introduced.

## Verification

Tests cover both locales, ready-only ordering, omission outside ready, exact
allowed/forbidden rows, no actionable markup or unsafe prose, aria linkage,
mobile/print/forced-colors hooks, escaping, deterministic output, and
unchanged routing/privacy behavior.
