# Dossier Snapshot Binding Plan

1. Add a dependency-free canonical dossier snapshot helper that returns the
   `snap-dossier-sha256-<digest>` identifier.
2. Add RED tests for canonical binding, fabricated IDs, dossier mutation, and
   schema/practice-session parity.
3. Update the handoff builder/validator, handoff schema, and dossier-source
   practice-session schemas to use the bound identifier.
4. Update synthetic fixtures and renderer/schema tests to the canonical ID;
   preserve triage snapshot IDs and renderer privacy behavior.
5. Run focused TDD suites, plugin static/privacy/release gates, then run the
   full repository suite before the single cachebuster/release/install pass.

Out of scope: changing triage snapshot semantics, exposing digests in HTML,
or adding an external registry/database.
