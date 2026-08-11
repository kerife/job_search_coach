# Plan: Recruiter Practice v2 Content Locale

1. Add v2 contract/renderer tests and a mixed-language fixture mutation; verify
   the new cases fail while v1 remains green (RED).
2. Add the v2 schema, validator dispatch/locale checks, and renderer language
   attributes with the smallest shared helpers (GREEN).
3. Run v2-focused, v1, plugin, root, privacy, static, release, and diff gates;
   independently review schema closure and HTML language/ARIA output.
4. Refresh allowlisted provenance, consume the cachebuster exactly once,
   publish/install, and verify source/cache identity plus installed validation.
