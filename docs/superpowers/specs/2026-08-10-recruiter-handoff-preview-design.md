# Recruiter handoff preparation preview

## Goal

Make a ready private recruiter triage handoff immediately usable by showing
the already validated preparation inputs without creating a second artifact or
starting interview preparation automatically.

## Design

Only `ready_for_private_prep` renders a compact preview containing the fixed
classification label, the one verified fact summary, and the one validated
question. These are copied from fields already accepted by the triage
validator; no new identifiers, recruiter/company details, raw reply, links,
times, or analytics are introduced. Clarify and stop states omit the preview.

The preview is a semantic `dl` with a visible heading and descriptions. It
keeps the existing manual re-entry, no-action, no-calendar, and local-save
disclosures. It has no button, link, form, auto-start, score, or outcome
language. Print keeps the block together; mobile remains single-column and
keyboard reading order is unchanged.

## Verification

Tests assert ready-only rendering in English and Spanish, exact one fact and
question, absence for clarify/stop, safe escaping, no forbidden prose or
internal IDs, accessible labeling, print containment, deterministic bytes, and
unchanged normal dossier/routing behavior.
