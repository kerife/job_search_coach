# Recruiter receipt groups

## Goal

Make the input receipt's allowed and forbidden boundaries unambiguous to
visual and assistive readers.

## Design

Replace the current repeated-row receipt with two explicitly labelled groups:
`Bring`/`Trae` containing the identity-free summary and one verified fact, and
`Do not bring`/`No traigas` containing raw recruiter text/identity and
calendar/contact details. Each group has its own heading and labelled list;
the fixed copy, ordering, ready-only state, and manual boundary remain.

No schema, routing, persistence, action, or data changes are introduced.
Mobile and print remain single-column and break-safe; forced-colors keeps
visible outlines and text labels.

## Verification

Tests assert group headings/order and four rows in both locales, omission in
clarify/stop, no interactive or unsafe output, accessibility linkage,
responsive/print/forced-colors hooks, escaping, and deterministic output.
