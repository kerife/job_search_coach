# Recruiter readiness focus

## Goal

Make the private ready handoff easier to scan and practice without expanding
its data contract.

## Design

Keep the three readiness rows, but make each `<dt>` a category (`Stage`, `Role
context`, `Critical constraints`) and each `<dd>` its fixed categorical value.
This removes duplicated label/value prose for screen readers while retaining
visible text status and current responsive/print styling.

Add one localized `Preparation focus` line derived from the existing
classification enum. The six mappings are fixed copy: screen invite practices
a concise opening; proof request chooses one verified example; eligibility and
compensation prepare their corresponding boundary question; decline uses a
stop/no-handoff cue; unknown asks for the smallest missing detail. It appears
only in ready state, has no score or action, and never interpolates reply text.

## Verification

Tests cover all six classifications in English and Spanish, generic safe
fallbacks, omission outside ready, exact `<dt>/<dd>` semantics, escaping,
privacy/action/calendar/outcome absence, accessibility, print/mobile, and
deterministic output.
