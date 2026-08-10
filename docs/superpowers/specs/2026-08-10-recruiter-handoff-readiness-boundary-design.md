# Recruiter handoff readiness boundary

## Goal

Make the ready-only handoff explain its safety gate before presenting the
verified fact and question.

## Design

Move the existing handoff section directly after the decision section. Add a
small localized readiness boundary with three fixed, categorical rows: stage
is recruiter-screen, role context is confirmed, and critical constraints are
confirmed. The rows are derived only from validated enum values and do not
display a score, percentage, identity, vacancy, recruiter, or raw text.

The existing two-item preview remains below the boundary. Clarify and stop
states keep the current ordering and do not render readiness or handoff. The
manual re-entry, no-action, no-calendar, and disabled-save disclosures remain
visible. Semantic headings, text labels, mobile stacking, print containment,
and deterministic output are preserved.

## Verification

Tests assert ready ES/EN ordering and all three rows, omission in clarify/stop,
fail-closed behavior when any readiness enum is tampered, no scores or unsafe
prose, accessibility labeling, print hooks, and unchanged normal dossier and
routing behavior.
