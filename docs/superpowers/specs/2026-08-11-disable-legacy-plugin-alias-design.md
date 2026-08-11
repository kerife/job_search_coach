# Disable legacy plugin alias design

## Context

Codex configuration currently enables both `job-search-coach@job-search-coach-local`
and the canonical `professional-growth-coach@professional-growth-coach-local`.
The legacy cache does not contain the current employment-continuity guard, so a
legacy skill resolution can bypass the product's safety contract.

## Decision

Remove only the legacy plugin entry from the active Codex configuration. Keep
the historical cache untouched for reversibility, but do not leave it enabled
or routable. The canonical marketplace entry remains enabled and points to the
project source.

## Acceptance

1. The active config contains no enabled `job-search-coach@job-search-coach-local`
   entry and retains the canonical entry.
2. `codex plugin list --json` reports the canonical plugin installed and enabled.
3. Canonical source/cache validation rejects a resignation imperative in dossier
   copy; the legacy cache is not used by active routing.
4. Repository tests, privacy/static/release checks, and source/cache identity
   remain green.

The historical cache is not deleted in this increment; deletion would be a
separate destructive cleanup decision.
