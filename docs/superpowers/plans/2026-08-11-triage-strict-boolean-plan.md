# Plan: Strict Boolean Triage Delivery Contracts

1. Add focused RED mutations for each immutable delivery/handoff boolean and
   verify the runtime validator accepts the malformed numeric values.
2. Replace only the affected Python comparisons with strict type-aware equality.
3. Run focused triage/schema/render tests, then the repository/static/privacy
   gates and `git diff --check`.
4. Refresh allowlisted provenance, consume the release cachebuster once, publish
   and install the local marketplace plugin, and verify source/cache identity.
