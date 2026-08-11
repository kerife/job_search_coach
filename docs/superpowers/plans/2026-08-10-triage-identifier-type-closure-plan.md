# Triage Identifier Type Closure Implementation Plan

> For agentic workers: execute this plan task by task, keeping each change
> small and verifiable.

**Goal:** Make triage v1/v2 JSON Schema identifier and snapshot types agree with
the existing fail-closed Python validators.

**Architecture:** Schema-only contract tightening; no production Python or HTML
behavior changes. Both versioned schemas receive the same `type: "string"`
constraints, and conformance tests exercise v1 plus mixed-locale v2.

**Verification:** Run RED mutations first, then focused schema/triage tests,
plugin discovery, root discovery, privacy/static/release gates, consume the
cachebuster exactly once, publish, install, and compare source/cache trees.

**Out of scope:** dossier v2, practice v3, renderer redesign, automatic locale
detection, and any external action or network integration.
