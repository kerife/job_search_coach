# Conversion evidence plural design

## Goal

Render the validated evidence count with natural localized singular/plural copy.

## Scope

Use the existing validated `fact_ids` count to select closed EN/ES labels: `1 candidate-supplied fact`/`N candidate-supplied facts`, and `1 hecho reportado por la persona`/`N hechos reportados por la persona`. No IDs, schema, routing, action, or persistence changes.

## Acceptance

One- and two-fact fixtures render the correct localized form; neither `fact(s)` nor `hecho(s)` appears. Existing privacy, skip, CSP, deterministic, and mode-0600 behavior remains green.
