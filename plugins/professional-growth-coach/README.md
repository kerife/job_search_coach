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

Private JSON market artifacts are written through a descriptor-anchored,
collision-safe path: parent symlinks, leaf symlinks, and hardlinked targets are
rejected; bytes are flushed before an atomic no-overwrite publication; and the
result remains mode `0600`. A failed write removes its temporary file and does
not alter an existing artifact.

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
other external action. On screens up to 680px, the table stacks signal cells
with localized labels while preserving its semantic and print layouts. The
section-coverage facts also collapse to one column at 640px and below so the
17-section ledger remains readable without horizontal scrolling.

The dossier schemas keep the source contract closed: methodology categories
must be present in the official registry, and secondary market sources must
use HTTPS. Unknown categories and non-HTTPS URLs are rejected by both schema
and runtime validation before rendering.

Current vacancy research uses the closed `target-vacancy-research-v1` artifact.
It is identity-free, bounded to at most five distinct postings, records dated
public-source provenance, and exposes only `complete`,
`limited_market_evidence`, or `market_evidence_unavailable`. Its deterministic
snapshot is suitable for downstream dossier work; it never performs external
actions or infers candidate eligibility.

Every vacancy artifact declares `evidence_mode` as `live` or `synthetic`.
Synthetic fixtures may use reserved example sources for reproducible tests;
live evidence rejects reserved domains and future-dated observations. Both
modes reject URLs, contact details, and session-shaped identifiers inside
observational prose, and diagnostics never echo the restricted value. A live
artifact must therefore be re-captured with dated public evidence before it is
used for a current-market decision. This required field is a v1 contract
migration: existing producers must add it before their artifact is accepted.

Migration: `career-market-learning-dossier-v1` and derived v2 artifacts now
require the propagated `evidence_mode`. Rebuild older v1 artifacts from their
source research instead of editing a snapshot-bound JSON file; synthetic
artifacts render with an explicit non-current-market boundary.

Learning-provider research declares its own `evidence_mode`. The v2 artifact
preserves this separately as `learning_evidence_mode`, so a live vacancy sample
cannot make synthetic provider availability, price, or certification evidence
look current. When several options cover one recurring gap, selection is
deterministic: candidate-owned project, lab, free resource, course,
certification, then no-learning; ties use the stable option ID.

For a normal local profile dossier, the default route is bounded five-vacancy
research: SRE, Platform Engineering, and DevOps in Mexico or stated remote
scope. It searches five distinct employers first, prefers official employer
and employer-operated ATS postings, and uses LinkedIn Jobs only as an
inspectable active backup. Every retained posting records active verification
and access date. A complete sample has five postings; limited `1..4` and
unavailable `0` results are never padded. Recurrence is always the actual
sample `k/N`; no work-authorization, internal-mobility, EOR, or
remote-eligibility is inferred. Research remains read-only: no apply, message,
connect, follow, publish, enroll, or purchase action.

The v2 renderer can optionally compose a validated
`career-market-learning-dossier-v1` or evaluated v2 learning dossier with
`--market-dossier`. The v2 composition
shows documented alignment cards, a semantic vacancy matrix, exact sample
recurrence, and a four-stage gap-closure route. Locale, evidence date, and the
executive-dossier snapshot must match before any HTML is written; omitting the
option preserves the existing no-market render byte-for-byte. Evaluated v2
cards expose a static coach decision, proof-first rationale, and a semantic
border treatment for project-first, consider, not-needed, and other states;
the state is always textual as well as visual and remains readable in print,
forced-colors, and narrow layouts.
Each learning card also leads with the decision and option type, then exposes
its decision basis and opportunity cost. Synthetic provider research receives
an explicit non-current-provider boundary in the rendered dossier.

The default composition begins with `learning_state=not_evaluated`. If bounded
market research cannot finish, the plugin preserves the valid profile dossier
and renders the limited or unavailable market state with one bounded reason;
it does not fabricate vacancies, market conclusions, or learning decisions.

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
