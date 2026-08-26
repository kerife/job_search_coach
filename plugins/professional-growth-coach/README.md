# Professional Growth Coach

Professional Growth Coach is a local Codex plugin for evidence-based professional-growth coaching. It helps employees evaluate market options, strengthen their current role, and prepare reversible next steps while preserving current employment by default. It routes one candidate case at a time, keeps candidate records isolated, and sends work to focused modules:

- `optimize-professional-profile`
- `explore-career-options`
- `research-professional-market`
- `optimize-career-assets`
- `prepare-role-interviews`
- `recommend-career-learning`
- `track-career-outcomes`

Use the root `professional-growth-coach` skill when the request spans multiple areas or needs intake, routing, consent, or action-boundary checks.

## Employment continuity

This plugin evaluates the market; it does not encourage resignation. `preserve_current_employment_by_default` and `no_resignation_recommendation=true` apply to every module. Staying and growing in the current role, developing skills, exploring options, or `do_nothing_now` are valid outcomes. Path decisions are research/positioning decisions only, never instructions to resign, quit, leave an employer, reduce hours, or create a voluntary gap.

## Privacy

Keep one `candidate_id` per case. Coach mode must split combined requests into separately labelled candidate sections before analysis. Cross-candidate benchmarking stays off unless explicit consent is recorded, and consent never authorizes external actions.

The plugin can prepare drafts, plans, rubrics, and analyses. It must ask again before editing LinkedIn, publishing content, sending messages, applying to jobs, uploading files, or sharing candidate work with a third party.

## Installation

This source tree is repo-local at `plugins/professional-growth-coach`. Source edits do not update the installed plugin cache. A separate explicitly authorized installation is required to publish a source increment into the local marketplace cache; existing chats may continue using their loaded version, so verify the new installation from a fresh chat. Use the repo-local marketplace workflow only after the exact target and command are approved.

## Starter prompts

- “Analiza mi perfil de LinkedIn y entrégame una conclusión breve más un dossier HTML privado v2 y completo. No inventes datos ni realices acciones externas.”
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

Expected routing: start with `professional-growth-coach`, preserve evidence labels, then produce an ordered plan across professional positioning, assets, market research, and conversation preparation.

When the private dossier route receives validated dated vacancy evidence, its
v2 HTML renders a separate comparison table with the real sample date,
candidate-to-signal gaps, and sanitized public research sources. Without that
evidence it keeps one explicit unavailable-market state. Vacancy context never
changes the LinkedIn score and never authorizes outreach, applications, or
other external action.

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
