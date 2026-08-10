# Recruiter handoff context preview

## Goal

Show the identity-free context that the ready handoff promises to carry into
manual preparation.

## Design

Add a localized `Identity-free context` row as the first item in the existing
ready-only preview, followed by the verified fact and safe question. Its value
comes only from the already validated `safe_context.summary` and is HTML
escaped. No schema or routing changes are needed; clarify/stop omit the
preview as before.

The row remains static, noninteractive, and subject to the existing prose
safety validator. It introduces no recruiter/company identity, raw reply,
contact, calendar, score, action, outcome, link, or internal identifier.

## Verification

Tests cover English/Spanish labels, exact three-row order, escaping, omission
outside ready, unsafe-prose rejection, accessibility/print/mobile hooks,
deterministic output, and unchanged receipt groups/routing.
