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

Rendering CLIs write the requested private artifact but omit its absolute local
path from the success receipt by default. A trusted caller that already knows
the output target may opt in with `--include-artifact-path`; in-process render
APIs continue to return their richer receipt object without changing the
artifact itself.

Bounded JSON validators and market-dossier builders also reject duplicate
keys, oversized integers, and excessive nesting before validation or output;
their command-line failures stay opaque and never echo supplied content. All
private validators and renderers apply the same boundary to unknown CLI
arguments: they return the fixed `invalid_arguments` diagnostic without
reflecting the rejected value. The LinkedIn client-report validator also caps
multi-error stderr at the shared 16 KiB diagnostic budget and emits a stable
truncation marker, so malformed private fixtures cannot flood a terminal or
log sink.
Renderer modules can also be imported directly from an installed checkout;
sibling safety helpers resolve relative to the module when no `PYTHONPATH` is
configured.

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

The v2 dossier keeps the verdict and recruiter scan together as the first
decision row, then adds a localized reading path linking to section coverage,
coaching priorities, market evidence, and first-conversation preparation. On
screen it stays visible while scrolling and marks the visible region with
`aria-current="location"`; without script it remains a static, keyboard-visible
fallback. The anchors use scroll-safe targets, remain available in print, and
stack into 44px touch targets at 640px and below; they do not hide or reorder
any evidence.

When market evidence is unavailable, the `Mercado`/`Market` region now keeps a
static next-research card visible instead of ending at a generic notice. It
states the bounded scope (SRE, Platform Engineering, and DevOps in Mexico or
declared remote scope), a five-employer sample target, priority official
employer/ATS sources, and the access-date requirement. The card is read-only:
it never applies, contacts, follows, publishes, or infers eligibility.

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
Each evaluated card now includes provider, option, source title/date, geography,
role, seniority, and any recorded unknowns when present. Vacancy cards expose
documented alignment alongside evidence coverage and qualitative band; the
visible legend keeps this directional evidence separate from hiring fit. Each
vacancy card also retains its location, arrangement, and source type, while a
separate boundary states that eligibility and work authorization are not
inferred.
Each card also exposes a passive, accessible link to its validated public source
and the sample's research date. The link is for auditability only: it does not
open an application flow, send a message, or authorize any external action.
Canonical source labels remain localized for `official_employer`,
`employer_operated_ats`, and `linkedin_jobs_backup`.
The follow-through checkpoint validator also exposes a pure `replay_fingerprint`
for the validated receipt/checkpoint pair. Equal keys are safe no-op replays;
changed structural fields produce a distinct key without persisting raw prose or
candidate identity.

Private recruiter outcome receipts, follow-through checkpoints, and practice
sessions also include a static, localized continuity rail. Compact outcome and
checkpoint rails select one closed copy set from the validated
`next_safe_action`, separating the recorded evidence, the safe route, and the
manual review with textual states. `record_stop_decision` is terminal and uses
Recorded/Registrado copy without continuation language. The rail is
explanatory only: it does not store answers, expose private identifiers,
auto-start preparation, or create a message, calendar, or other external
action. Its surface token remains readable in dark mode and its borders/text
remain explicit in print, forced-colors, and higher-contrast modes.

After a completed `screen_attended` checkpoint, the rail now uses the closed
`debrief_after_screen` action: it is a cue to re-enter a private conversation
and manually note what was discussed and what remains unknown. The checkpoint
renderer does not capture, persist, or review those notes; any structured
debrief artifact requires a separately specified contract. This is still
manual-only and does not send, schedule, auto-start preparation, or retain the
screen conversation.

When feedback is available, the practice rail remains the same three-step
private map but reflects the validated governing label in its final state:
`pending` for `solid`, or `blocked` for `confirm` and `do_not_assert`. Its
styling is a closed visual cue only; it does not verify meaning, score
readiness, transport feedback text, start another rehearsal, or trigger an
external action. The static rail remains readable in narrow, print, dark,
forced-colors, and higher-contrast modes.

Practice sessions also begin with a first-conversation readiness card. It shows
the recruiter-screen stage, whether supplied evidence is confirmed or still
needs confirmation, the private-only boundary, and the manual next step. It is
derived from validated state only; it never displays internal IDs or raw answers
and never sends, schedules, or saves anything.

When a validated recruiter-reply triage opens a private practice session, the
client sees one static, localized first-answer outline before the route and
handoff panels. Its three short steps reuse the validated question-kind coaching
only; it neither captures nor saves an answer, changes evidence, nor triggers
an external action.

After feedback is available, the session also places one static, localized
next-version bridge after the governing decision and before the continuity rail.
It names the three manual moves—keep, adjust, and check—from closed coaching
copy selected by the validated question kind and governing feedback label. The
bridge is explanatory only: it never exposes an answer or feedback statement,
saves a revision, starts another rehearsal, or performs an external action. The
continuity rail remains the separate, non-interactive map of evidence,
rehearsal, and the pending next version.

`private-recruiter-triage-practice-handoff-v1` is the closed composition
boundary from a private recruiter-reply triage into one private rehearsal. It
accepts only a validated `ready_for_private_prep` triage with
`handoff_allowed=true` and exactly one verified fact. Before composition, it
recalculates the triage snapshot and requires the packet and re-entry snapshots,
question, fact, and preparation scope to agree. The resulting practice session
is unanswered (`ready_to_practice` with unknown pre-answer feedback), carries
only the safe question and verified-fact context, and records the exact triage
snapshot as provenance. It never copies raw reply material, source identifiers,
URLs, or a candidate answer.

The handoff is draft-only and local: it cannot send, schedule, upload, save, or
auto-start anything. Rehearsal begins only after the candidate manually re-enters
the validated context in a later private practice request. Snapshot drift,
candidate-reported facts, non-ready triage states, or mismatched handoff
references are rejected rather than converted into practice material.

For an explicit private file workflow, use two deliberate commands: first run
`build_private_recruiter_triage_practice_handoff.py --input TRIAGE.json --output HANDOFF.json`,
then, after inspecting that closed wrapper, run
`render_private_recruiter_triage_practice_handoff.py HANDOFF.json --output PRACTICE.html`.
The builder accepts only the v2 triage contract, reads one bounded non-symlink
JSON object, recalculates and verifies the handoff provenance before an atomic
private write, and will not overwrite an existing regular file without
`--force`. The renderer independently validates the wrapper and its nested
practice session before projecting HTML; it does not render a bare session as a
wrapper. Both outputs are private mode `0600`, and failures use compact JSON
error envelopes without echoing supplied prose.

The renderer receipt is intentionally minimal:
`{"artifact_kind":"private_recruiter_triage_practice_handoff_html","ui_locale":"es|en"}`.
It confirms only the local artifact kind and interface locale; it contains no
path, source identifier, snapshot, raw reply, answer, score, or action result.
The rendered status remains a private draft that requires manual re-entry. It
does not start a rehearsal, send, schedule, save, upload, or authorize an
external action. Legacy v1 triage remains readable only through its existing
legacy routes and is not eligible for this wrapper, renderer, or manual re-entry
path; manually recreate a validated v2 triage instead.

The direct practice-session commands use the same private terminal boundary:
`render_recruiter_practice_session.py` returns only its fixed artifact-kind and
locale receipt, while `validate_recruiter_practice_session.py` returns only a
fixed valid acknowledgement. Their argument and input failures use fixed JSON
error envelopes and never echo a supplied path, prose, or value. This is
deliberately narrower than in-process library use: `write_session_html` may
return its richer `RenderReceipt` to a trusted caller, and `load_session` plus
`validate_session` retain bounded diagnostics for in-process handling. Do not
relay those library values through a direct CLI transcript.

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
