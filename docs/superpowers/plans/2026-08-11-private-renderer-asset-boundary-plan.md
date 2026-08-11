# Private renderer asset boundary implementation plan

1. Add RED tests for direct/intermediate/broken symlinks and an external-marker
   renderer case across the canonical asset families.
2. Implement the common loader and route all five renderers through it.
3. Extend the static package check to all ten HTML/CSS assets; keep the dossier
   security checks and existing error contracts intact.
4. Run focused tests, plugin/static/privacy/full gates, independent review,
   refresh provenance, consume the cachebuster once, publish, install, and
   verify source/cache identity plus installed validation.
