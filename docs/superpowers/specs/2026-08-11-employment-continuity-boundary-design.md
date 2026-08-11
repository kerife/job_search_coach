# Visible employment-continuity boundary for normal practice flows

## Context

Professional Growth Coach evaluates market options while preserving current
employment by default. The dossier and stop states show that boundary, but
normal recruiter-practice and triage states only say that no external action
was taken. In an office context, that omission can make a private preparation
artifact look like an instruction to leave a job.

## Design

Add one localized, visible `employment_boundary` sentence to the practice and
triage footers:

- EN: `This analysis evaluates professional options; it does not recommend
  resigning, leaving a job, or stopping your job search; you decide what comes
  next.`
- ES: `Este análisis evalúa opciones profesionales; no recomienda renunciar,
  dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.`

Practice always includes this sentence. Triage includes it for `clarify_first`
and `ready_for_private_prep`; the existing stop-specific recruiter-process
scope remains the sole stop disclaimer and is unchanged. The sentence is
ordinary footer content, not `.no-print`, a control, a link, or an action.

## Non-goals

No schema, validator, IDs, dynamic prose, CSS layout, external action, privacy
policy, or compact receipt behavior changes. Dark-mode work remains separate.

## Acceptance

1. Practice states `ready_to_practice`, `awaiting_answer`, and
   `feedback_available` render the localized boundary once in EN/ES.
2. Triage `clarify_first` and `ready_for_private_prep` render it once in EN/ES;
   stop renders its existing stop scope without a duplicate boundary.
3. The boundary is present in the visible footer and print output, with no
   private IDs/raw prose added and no external controls.
4. Deterministic render, static/privacy/schema/release gates, source/cache
   parity, and installed smoke remain green.
