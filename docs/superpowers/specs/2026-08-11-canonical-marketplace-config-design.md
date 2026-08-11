# Canonical marketplace configuration design

## Context

The active Codex config no longer enables the legacy plugin, but it still keeps
the `[marketplaces.job-search-coach-local]` table. That stale marketplace alias
can reintroduce legacy resolution even though the canonical catalog and plugin
are now named `professional-growth-coach`.

## Decision

Remove only the stale legacy marketplace table from the active Codex config and
retain one active `[marketplaces.professional-growth-coach-local]` table for
the canonical catalog. Keep historical plugin cache files untouched for
rollback, and keep the canonical marketplace catalog in
`.agents/plugins/marketplace.json` unchanged.

## Acceptance

1. Active config contains no `job-search-coach-local` marketplace or plugin
   entry, and retains both the canonical marketplace and plugin entries.
2. The marketplace catalog remains `professional-growth-coach-local`.
3. `codex plugin list --json` reports only the canonical plugin as installed and
   enabled; source/cache identity remains byte-identical.
4. Repository static, privacy, release, plugin, and root tests remain green.

This is configuration hygiene, not cache deletion; the old cache remains
inactive and recoverable.
