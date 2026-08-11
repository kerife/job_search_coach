# Palette family contract implementation plan

1. Add RED tests for the canonical asset allowlist and synthetic unknown or
   mismatched colors.
2. Add a pure-Python checker with explicit family-to-asset mapping and invoke
   it from `run_static_checks.py`.
3. Clarify the family allowlists in `.superdesign/design-system.md` while
   preserving current CSS values and compact receipt boundaries.
4. Run focused tests, plugin static checks, full repository tests, and
   `git diff --check` before release work.
