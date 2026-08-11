# Disable legacy plugin alias implementation plan

1. Add a configuration-contract regression test or static assertion for the
   canonical-only active plugin identity.
2. Remove the legacy plugin block from the active Codex config.
3. Verify plugin listing, canonical safety behavior, and no legacy active entry.
4. Update the local installed-smoke attestation and provenance metadata if the
   repository report changes; run all release gates and diff checks.
