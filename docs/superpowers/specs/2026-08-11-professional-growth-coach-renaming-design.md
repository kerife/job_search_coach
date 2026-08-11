# Professional Growth Coach Rename and Workplace-Neutral Positioning

## Goal

Rename the plugin and its user-facing skill surface from Job Search Coach to
Professional Growth Coach, while making the product's purpose explicit:
evidence-backed professional development and market literacy, not a tool that
encourages resignation or performs job-search actions.

## Decision

This is a breaking identity migration, not a cosmetic label change.

| Current identity | New canonical identity |
| --- | --- |
| `job-search-coach` plugin | `professional-growth-coach` plugin |
| `job-search-coach-local` marketplace | `professional-growth-coach-local` marketplace |
| `Job Search Coach` display name | `Professional Growth Coach` |
| `skills/job-search-coach` root skill | `skills/professional-growth-coach` |
| `discover-high-value-career-paths` | `explore-career-options` |
| `research-target-job-market` | `research-professional-market` |
| `optimize-job-search-assets` | `optimize-career-assets` |
| `track-job-search-outcomes` | `track-career-outcomes` |
| `optimize-linkedin-career` | `optimize-professional-profile` |

`prepare-role-interviews` and `recommend-career-learning` remain descriptive
capability names. The old plugin is not silently overwritten: the new
marketplace entry is installed as a separate package, and migration notes tell
existing users to switch deliberately.

## Workplace-neutral contract

The active root skill, career-options skill, path-scoring reference, routing
reference, README, and private triage stop state must all state:

- preserve current employment by default;
- `prioritize`, `research`, `defer`, and `reject` are research/positioning
  decisions, never separation instructions;
- the plugin never recommends resigning, quitting, leaving an employer,
  reducing hours, or creating a voluntary employment gap;
- staying and growing in the current role, developing skills, exploring the
  market, and doing nothing now are all valid outcomes;
- if a person explicitly asks about leaving, return a neutral scenario matrix
  covering runway, benefits, notice, work authorization, safety, and HR/legal
  questions, with `no_resignation_recommendation=true`;
- no employer monitoring, HR export, recruiter outreach, application,
  messaging, scheduling, or other external action occurs automatically.

The stop triage card must name the recruiter process explicitly and say that it
does not mean stopping the job search or leaving employment; the candidate
decides what comes next.

## Compatibility and migration

- Do not use symlinks for the renamed package or assets; the repository's asset
  trust boundary rejects them.
- Update all active tests, fixture paths, imports, static-check expectations,
  marketplace references, skill links, and installed-cache verification to the
  new names.
- Historical SDD documents may retain old names as historical record, but an
  active source scan must contain no stale old plugin/skill IDs outside an
  explicit migration allowlist.
- Preserve schema versions and data contracts unless a test proves the rename
  requires a change. This is an identity/copy migration, not a schema rewrite.
- Fix the Python 3.11-compatible nested f-string syntax in
  `validate_linkedin_client_report.py` before the release gate.

## Superdesign review

Run the authenticated Superdesign CLI preflight, read all six `.superdesign/init`
files and the local design system, then review the existing canvas/drafts for
the new product language. Keep the current offline editorial visual system,
privacy, CSP, print, responsive, and accessibility behavior. A visual draft is
only changed if the review finds a concrete comprehension problem; a name and
copy migration must not introduce new fonts, colors, remote assets, forms, or
automation.

## Release acceptance

1. New manifest, marketplace, directory, skill inventory, and active references
   all use the Professional Growth Coach identity.
2. Contract tests prove the continuity boundary and neutral stop copy in EN/ES.
3. Python 3.11 locked validation and the full root/plugin suites pass.
4. Static, privacy, schema, handoff, release, and diff checks pass.
5. The cachebuster is consumed exactly once for the new package identity.
6. The new marketplace package installs/enables successfully, its source and
   versioned cache are byte-identical, and the old package is not silently
   mutated.
7. The final Git worktree contains only the intended migration/release commit.
