# Plan: triage-first answer outline

## Goal

Make the first safe answer structure visible before triage process metadata,
without expanding the private-data projection surface.

## Task 1 — Static renderer and focused tests

Add a dedicated helper in
`plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py`
that validates the locale/question kind, reads only `REHEARSAL_COPY`, escapes
its hint and steps, and emits the localized outline markup. Insert it only for
`private_recruiter_reply_triage` after the claim guardrail and before the route.
Extend the renderer tests for ES/EN × five kinds, exact order/count, absence in
dossier/unsourced sessions, and strict no-ID/no-URL/no-raw-data assertions.

## Task 2 — Theme-aligned CSS and documentation

Style the new variant in
`plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`
using the local Superdesign palette and existing accessibility contracts:
forest border/surface, three-column steps, 640px collapse, dark,
forced-colors, contrast-more, print, and reduced-motion behavior. Add exact
theme parity coverage and update README plus the interview-map reference with
the static/no-save/no-external-action boundary.

## Task 3 — Release, install, and publication

Bump the plugin release cachebuster, install the local plugin, verify source and
cache parity and installed smoke coverage, refresh the immediate-parent release
attestation, run plugin/static/privacy/release/root suites, obtain an
independent release review, then commit and execute the authorized
`git push origin HEAD:main`. Verify local/remote commit equality and leave the
plugin installed and enabled.

## Verification commands

- `python3 -m unittest discover -s plugins/professional-growth-coach/tests -p 'test_*.py' -q`
- static/privacy/release checks used by the plugin release harness
- `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -q`
- exact CSS parity against `.superdesign/init/theme.md`
- `git status --short --branch`, `git rev-parse HEAD`, and remote ref equality
