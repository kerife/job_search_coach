# Plan: feedback next-version bridge

## Goal

Close the feedback loop with one static, private, localized instruction for
building the next answer version while preserving the existing continuity rail.

## Task 1 — Closed renderer copy and tests

Add closed bilingual copy tables and a renderer helper for
`.practice-next-version`, keyed only by validated locale, question kind, and
governing feedback label. Insert it after `.practice-decision` and before the
continuity rail only in `feedback_available`. Extend both plugin and root
renderer tests for ES/EN × five kinds × three labels, order, unique ARIA id,
absence in pre-answer states, and strict no-private-data/no-control assertions.

## Task 2 — Theme and documentation

Style the bridge in
`plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`
and synchronize the matching block in `.superdesign/init/theme.md`: forest
surface/border, three-to-one-column responsive layout, dark, forced colors,
contrast-more, print, and reduced-motion contracts. Update README and the
interview-map reference to describe the manual next-version bridge and its
relationship to the continuity rail.

## Task 3 — Release, install, and publication

Bump the cachebuster, install the plugin, run installed bridge smoke and source
parity, refresh immediate-parent provenance, run plugin/static/privacy/release/
root suites, obtain independent release review, then push
`git push origin HEAD:main` and verify remote equality.

## Verification

- Focused plugin and root renderer suites plus `git diff --check`.
- Static/privacy/release gates and exact Superdesign CSS parity.
- Installed ES/EN smoke with no external action and private `0600` artifacts.
- Full root suite and local/remote commit equality.
