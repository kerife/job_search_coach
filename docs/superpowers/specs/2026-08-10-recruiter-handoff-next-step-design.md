# Recruiter handoff next step

## Goal

Make the manual decision after a ready private triage unambiguous without
introducing an actionable control.

## Design

Inside the existing ready-only handoff rail, render one localized static
“Manual next step” strip after the preparation focus and before the fact/question
preview. Its fixed copy says to open private preparation manually and answer
the one safe recruiter-screen question. It is a labeled section or paragraph,
not a button, link, form, `role=status`, or dynamic action.

Clarify and stop states omit the strip. The strip derives no raw text, IDs,
identity, contact, vacancy, times, scores, calendar, send, or outcome terms.
Existing no-action, no-save, and manual re-entry disclosures remain unchanged.

## Verification

Tests cover localized ready-only copy, ordering, omission outside ready,
absence of interactive/actionable markup, escaping/privacy, accessibility,
mobile/print containment, deterministic output, and unchanged routing.
