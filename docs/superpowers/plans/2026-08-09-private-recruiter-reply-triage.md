# Private Recruiter Reply Triage Implementation Plan

## Task 1 — Closed triage contract

Add schema, validator, CLI, ES/EN fixtures, and RED/GREEN tests. Enforce the three states, six classification values, one fact, one safe question, reference integrity, no raw/identity/action/outcome prose, immutable draft-only delivery, and `handoff_allowed` only for ready state. Commit `feat: add private recruiter reply triage contract`.

## Task 2 — Offline private decision card

Add renderer/CLI, scoped CSS, and tests. Render classification, decision, facts, missing confirmation, blocked claims, handoff note, and no-action footer. Use atomic 0600 output, safe escaping, deterministic bytes, mobile/print/reduced-motion rules, and no raw reply. Commit `feat: render private recruiter reply triage`.

## Task 3 — Routing and skill contract

Add explicit private-triage precedence below private practice and above ordinary recruiter-reply routing. Missing summary/fact asks exactly one intake question; normal dossier/debug behavior remains unchanged. Update networking/interview/root/client-report references and integration tests. Review independently for value and security. Commit `feat: route private recruiter reply triage`.

## Task 4 — Publish and load

Refresh deterministic provenance, run all gates, invoke cachebuster exactly once preserving base `0.2.0`, commit release files, rerun gates, install the exact version, and smoke clarify/ready/stop states with source/cache identity.
