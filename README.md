# Professional Growth Coach marketplace

This repository is a Git-shareable Codex marketplace for the `professional-growth-coach`
plugin. The marketplace catalog lives at `.agents/plugins/marketplace.json` and
the plugin itself lives at `plugins/professional-growth-coach/`.

## Repository layout

- `.agents/plugins/marketplace.json` — local marketplace catalog.
- `plugins/professional-growth-coach/` — plugin manifest, skills, scripts, schemas, assets, and plugin tests.
- `tests/` — repository-level structure, privacy, provenance, and release gates.
- `docs/` — design specifications and implementation plans.
- `.superdesign/` — shareable design-system/source artifacts; private generated renders belong in ignored paths.

Learning recommendations use the closed `learning-option-research-v1` schema and
validator to keep provider evidence dated, identity-free, and separate from
market snapshots; paid or external actions remain blocked until explicitly
authorized.

The market-learning v2 dossier composes that research only with an exact market
snapshot and recurring vacancy rows. It emits three to five ranked, draft-only
decisions, prefers a candidate-owned proof project before paid learning, and
does not recommend a paid option when budget or current source evidence is
unknown. Every decision remains bounded by `no_external_action=true`.

## Share through Git

Clone this repository, then add its marketplace root to Codex:

```bash
codex plugin marketplace add .
```

Run the command from the repository root. The catalog points to
`./plugins/professional-growth-coach`, so the plugin remains portable when the
repository is shared by Git.

## Validate locally

```bash
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
python3 -B -m unittest discover -s tests -p 'test*.py' -q
```

The official plugin validator additionally requires the `PyYAML` package in the
active Python environment. Do not install dependencies implicitly in release
automation; install them explicitly when setting up a development environment.

## Plugin scope

Professional Growth Coach is a local Codex plugin for evidence-based professional-growth coaching. It routes one candidate case at a time, keeps candidate records isolated, and sends work to focused modules:

- `optimize-professional-profile`
- `explore-career-options`
- `research-professional-market`
- `optimize-career-assets`
- `prepare-role-interviews`
- `recommend-career-learning`
- `track-career-outcomes`

Use the root `professional-growth-coach` skill when the request spans multiple areas or needs intake, routing, consent, or action-boundary checks.

## Privacy

Keep one `candidate_id` per case. Coach mode must split combined requests into separately labelled candidate sections before analysis. Cross-candidate benchmarking stays off unless explicit consent is recorded, and consent never authorizes external actions.

The plugin can prepare drafts, plans, rubrics, and analyses. It must ask again before editing LinkedIn, publishing content, sending messages, applying to jobs, uploading files, or sharing candidate work with a third party.

## Installation

This source tree is repo-local at `plugins/professional-growth-coach`. Source edits do not update the installed plugin cache. A separate explicitly authorized installation is required to publish a source increment into the local marketplace cache; existing chats may continue using their loaded version, so verify the new installation from a fresh chat. Use the repo-local marketplace workflow only after the exact target and command are approved.

## Starter prompts

- “Analiza mi perfil de LinkedIn y entrégame una conclusión breve más un dossier HTML privado y completo. No inventes datos ni realices acciones externas.”
- “Compare professional-growth options for a synthetic SQL/Airflow/dbt background, then tell me what market evidence is missing.”
- “Prepare me for this interview using the supplied vacancy and my candidate fact matrix.”
- “Build a first-interview recruiter screen brief, objection response map, and draft-only outreach funnel from my confirmed evidence; do not send anything.”

## Self-service example

Use self-service mode when one candidate asks for their own professional-growth plan:

```text
candidate_id: candidate-synthetic-01
mode: self-service
target: Data Platform Specialist
stack: SQL, Airflow, dbt
request: Audit LinkedIn, identify CV gaps, and prepare interview drills for this vacancy.
```

Expected routing: start with `professional-growth-coach`, preserve evidence labels, and evaluate professional positioning, assets, market research, and conversation preparation without recommending resignation.

## Coach mode example

Use coach mode when helping multiple people:

```text
mode: coach
candidates:
  - candidate_id: candidate-a
    request: LinkedIn audit for SRE roles.
  - candidate_id: candidate-b
    request: Enterprise AE transition learning plan.
```

Expected routing: split the request into isolated candidate sections. Do not reuse facts, outcomes, metrics, or drafts across candidates.
