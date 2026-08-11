# Canonical marketplace configuration plan

1. Run a RED assertion showing the legacy marketplace table is still present.
2. Remove the exact legacy marketplace block and retain the canonical
   marketplace block in the active config.
3. Run GREEN config/list/source-cache checks and repository gates.
4. Commit the design, configuration attestation, and provenance metadata without
   changing plugin code or consuming a plugin cachebuster.
