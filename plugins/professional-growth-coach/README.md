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

The recruiter-networking flow includes a private `recruiter-target-shortlist-v1` artifact for manually supplied targets. It is a deterministic three-to-six-row review batch with `advance`, `clarify`, `pause`, or `stop` decisions. The builder and validator keep each row draft-only, consent-not-granted, authorization-required, and blocked from message or calendar actions; the bilingual offline renderer shows a localized semantic review date and one prominent, fixed batch next-step panel while omitting target identifiers, contact details, and URLs.

The shortlist privacy boundary also rejects phone-like strings, credential or bearer-token markers, and generic local filesystem paths in every bounded text field. This keeps private contact or machine material out of both the JSON artifact and its in-memory HTML review surface, even when it is supplied as `context_source`.

The same boundary rejects Unicode control and format characters (including zero-width, bidi, NUL, and newline controls) in diagnostic field names and dossier prose, preventing hidden or injected material from reaching validation output or local HTML.
Identity checks also inspect the NFKC-normalized form of prose, so compatibility characters cannot disguise a bare person name while the original candidate text remains unchanged for rendering.

Explicit requests to expand a network, contact recruiters, or prepare for a recruiter interview route through `scripts/route_recruiter_target_shortlist.py`, including natural English/Spanish phrasing such as “network with recruiters”, “reach out to recruiters”, “entrevista con un recruiter”, “primera entrevista con un reclutador”, defined-article variants such as “first interview with the recruiter” or “primera entrevista con la reclutadora”, and first-conversation variants such as “initial interview with the recruiter”, “first call with a recruiter”, “entrevista inicial con el reclutador”, or “primera llamada con la reclutadora”. Completed recruiter-screen language now has precedence over shortlist routing: “I had a recruiter screen; help me debrief”, “qué sigue después de mi entrevista con el reclutador”, and equivalent wording return an artifact-free `private_recruiter_screen_debrief` or `private_recruiter_next_stage_review` handoff with the correct module and one bounded context question. The same post-screen classifier recognizes recruiter calls and conversations in English and Spanish (`recruiter call`, `conversation`, `llamada`, `conversación`, `hablé con`) plus common “what comes next / siguiente paso” wording. Negated or future screen language (`have not had`, `didn't attend`, `did not complete`, `never had`, `never completed`, `scheduled for next week`, `aún no`, `no asistí`, `no tuve`, `todavía no`, `nunca tuve`, `nunca asistí`, `mañana`) is kept out of post-screen debrief and returns the artifact-free `recruiter_target_screen_intake` preparation boundary instead. The router requires recruiter/screen context, keeps technical interviews without that context in ordinary coaching, and preserves `authorization_required` for every action-shaped request even when the request does not match a recruiter route. With three to six supplied targets, the route runs builder → validator → renderer and returns the validated artifact plus private in-memory HTML with `next_action=review_recruiter_target_shortlist`; without enough context or with an invalid target container it asks one bounded intake question that names the minimum plan (goal/segments, 3–5 manual queries, weekly time, stop condition, and proof theme). Recursively nested or otherwise malformed in-memory plans take the same artifact-free intake path instead of surfacing a traceback. It does not infer recipients. The rendered card localizes the next safe action and summarizes the four decision counts before the manual `recruiter_target_decision_gate` handoff.

Natural recruiter interview intent also covers defined-article and scheduled
forms such as “I have an interview with the recruiter”, “tengo una entrevista
con la reclutadora”, “my recruiter screen is this Friday”, and “el viernes”; a
future weekday or month date routes to the artifact-free screen-intake
preparation boundary. A completed screen followed by “not yet ready for the
next stage” remains a next-stage review request rather than non-attendance.
Requests to respond, email, contestar, enviar, or mandar a un recruiter retain
`authorization_required=true` even on ordinary fallback routes.

The same language boundary recognizes recruiter screens that are invited,
missed, skipped, canceled, rescheduled, or still pending (`write back`, `ping`,
`DM`, `contéstale`, `respóndele`, and `escríbele` included for action checks).
Future dates are scoped to the recruiter event itself, including “is Monday”,
“is next Monday”, “is on Monday”, “in two days”, “scheduled for next week”,
“tomorrow”, and “en dos días”; an unrelated appointment date or invitation
after a completed screen cannot reopen pre-screen intake. An invitation to a
later stage remains a next-stage review request when the screen is already
complete.

The preparation boundary also covers conversational non-attendance such as
“I never went through the recruiter screen”, “I never spoke with a recruiter”,
and “No hablé con el reclutador”; these remain artifact-free screen intake.

Invitation and scheduling language is also normalized: `got invited`,
`received an invitation`, `was asked`, `pending`, `booked`, `scheduled to
speak`, and their Spanish equivalents route to the artifact-free screen-intake
boundary. If the same invitation asks to reply, accept, confirm, email, or
follow up, it enters the private `recruiter_reply_triage` intake first with an
identity-free summary plus one verified fact; no response or calendar action is
performed. Follow-up wording (`follow up`, `follow-up`, `dar seguimiento`) also
keeps the authorization requirement on fallback routes.

Inbound recruiter contact is normalized before any reply drafting: `messaged`,
`emailed`, `reached out`, “asked about my availability”, “what should I say?”,
and Spanish equivalents such as “me escribió”, “me contactó”, “me preguntó” and
“¿qué le digo?” enter artifact-free `recruiter_reply_triage` with an identity-free
summary plus one verified fact. The route remains authorization-gated and
performs no message, calendar, or scheduling action. Scheduling or choosing a
time, a calendar invite, “reply to a recruiter”, and Spanish “me pidió
disponibilidad” or “me llegó una invitación para agendar” use the same private
triage boundary.

The same preparation boundary covers explicit non-attendance such as “I never
went to the recruiter interview”, “I didn’t go to the recruiter screen”,
“Nunca fui a la entrevista con el reclutador”, “No fui”, “No me presenté”, and
“Nunca pasé por un filtro con el reclutador”.

Negated English forms such as “I had no recruiter screen yet” and “I have no
recruiter interview yet” take the preparation intake route rather than a
post-screen debrief.
Conversely, “I had no trouble/questions during or after the recruiter screen”
still counts as a completed screen; an explicit “what comes next” request uses
the next-stage review route.

The dossier v2 reading path keeps its nearest-section scrollspy responsive with a single guarded `requestAnimationFrame` update shared by scroll, resize, and `IntersectionObserver` callbacks; this limits layout reads and active-state mutations to at most one per frame without changing the initial hash or keyboard link behavior.
If the same request also asks to send, reply, connect, apply, publish, confirm, or schedule, the route receipt preserves `authorization_required=true` in both `ready` and `needs_intake` states; analysis-only networking remains `false`, and no external action is performed. The value is kept aligned with the artifact delivery gate.

Decision-gate rows are replay-bound to the corresponding shortlist target for every copied decision, rationale, context, contactability, draft type, and next action; the localized strategy and warm-intro guidance are also deterministic for the source locale and decision.

For a selected `advance` target, `route_recruiter_screen_intake` adds the target-specific `recruiter-target-screen-intake-v1` bridge. It requires a stated screen stage, `V-###` vacancy requirements, `F-###` candidate facts, non-unknown company evidence, a source date no older than 90 days from the gate snapshot, and four passing checks before returning only `manual_prepare_role_interviews_review`; stale context stays `clarify_first` with `clarify_context`, while `clarify` and `stop` targets remain blocked or in intake, with no message, calendar, or automatic preparation action.

The decision gate also enforces temporal continuity: its `as_of_date` must match the nested shortlist snapshot date, so a stale shortlist cannot be relabeled as a current screen-intake source.
All recruiter shortlist, gate, screen-intake, debrief, and next-stage date fields now require the canonical `YYYY-MM-DD` calendar form; the LinkedIn client-report runtime and dependency-free schema validator apply the same rule to evaluation and source access dates. Alternate ISO spellings are rejected before snapshots are chained.
Private recruiter conversion-outcome and follow-through checkpoint validators and renderers enforce the same canonical `--as-of` contract, so CLI replays cannot accept week-date spellings that the artifact schema rejects.
The same canonical-date guard is enforced by the market-learning dossier, vacancy-research, learning-option research, and executive-dossier runtime validators, keeping the schema and Python validation boundary aligned.

In `prefers-contrast: more`, screen-intake and screen-debrief cards and coverage rows use 2px borders and 0.5rem state bands, matching the stronger contrast treatment across the recruiter review family. Compact conversion-outcome and follow-through checkpoint receipts also use 2px rail, step, and marker borders, preserving state legibility without relying on color alone.

The decision gate, screen-intake bridge, post-screen debrief, and next-stage review now return the same private in-memory `rendered_html` contract whenever a validated artifact exists. Intake failures remain artifact-free; stopped or blocked artifacts still render their localized review surface without IDs, snapshots, contacts, or action tokens.

The five recruiter review surfaces also render the shared identity-free continuity rail from `scripts/recruiter_continuity_rail.py`: shortlist, decision gate, screen intake, screen debrief, and next-stage review. It uses localized closed labels inside a static `section` (not a navigation landmark), visibly states that it is orientation rather than progress or contact tracking, labels the current item as the current review surface (not a completed milestone), marks only that surface with `aria-current="step"`, remains non-interactive, collapses to one column below 420px, and keeps the same offline, print, forced-colors, and responsive boundary without adding candidate data or external actions. In forced-colors mode the shortlist priority panel resets to `Canvas`/`CanvasText` with an explicit `CanvasText` border so its color-mix accent cannot reduce readability.

Every artifact-free downstream handoff also returns a fixed `evidence_gaps`
list and one localized `intake_question`. The question is specific to the
missing handoff: the gate asks for the validated shortlist, screen intake asks
for stage/`V-###` requirements/`F-###` facts/company evidence/four checks,
debrief intake first accepts a validated checkpoint, receipt, and target intake
and asks only for structured coverage; full debrief recovery asks for
checkpoint/receipt/intake/structured coverage, and next-stage
review asks for a valid debrief plus a forward stage. If the debrief is already
valid but the selected non-terminal stage is not allowed, the route returns
`next_action=select_forward_stage` and taxonomy-derived `allowed_next_stages`;
`offer_stage` is terminal and returns `case_state=terminal` with
`next_action=record_terminal_stage` and no allowed stage. Recovery text never
reflects malformed input, private identifiers, or raw conversation text, so a
client can recover without guessing what to submit.
Downstream handoff routes also fail closed when a structured payload carries a
non-string or unknown locale: they return the same localized `needs_intake`
surface without a traceback or artifact.

The recruiter snapshot chain is closed at both contract layers: embedded
`source_shortlist`, `source_gate`, `source_intake`, `source_receipt`,
`source_checkpoint`, and `source_debrief` envelopes reject unknown fields in
the JSON Schemas as well as in the runtime validators. The debrief schema
reconciles its decision, measurement event, and safe action; the next-stage
schema reconciles its ready/blocked action and enumerates the same forward
stage transitions as the runtime taxonomy. Runtime validation remains
authoritative for dates, hashes, and cross-artifact provenance. A
`screen_attended` checkpoint also carries the identity-free `target_binding`
(`T-###` plus the shortlist snapshot) and must match the target-specific
intake exactly. Its source receipt must be `screen_requested` or
`interview_requested`, and the checkpoint and receipt locales must match;
legacy checkpoints without that binding, incompatible receipt events, or locale
drift recover artifact-free and are never combined silently. Schema-only
acceptance never grants preparation or external-action authorization.

Completed checkpoints that route to preparation (`screen_prepared` or
`interview_requested`) apply the same receipt gate: only a matching
`screen_requested` or `interview_requested` outcome can authorize that route;
contact, reply, and referral receipts remain clarification-only.

After a validated `screen_attended` checkpoint, `route_recruiter_screen_debrief_intake` starts an artifact-free, bilingual debrief intake that carries the validated checkpoint/receipt/intake boundary forward and asks only for requirement coverage, scope, and team context. It accepts both `screen_requested` and `interview_requested` receipts, preserving event-specific copy without inferring a stage. `route_recruiter_screen_debrief` then builds `private-recruiter-screen-debrief-v1` once that structured context is supplied. The private bilingual debrief records only structured coverage, unknown topics, supported facts used, and a manual `continue_review|pause|stop` decision. Complete coverage returns `ready` for `manual_prepare_next_stage_review`; incomplete coverage returns `needs_intake` for context collection, while a stop decision returns terminal `stopped` with `record_stop_decision`. No raw conversation text, contacts, messages, calendar actions, automatic preparation, or outcome prediction is retained.

When a next stage is explicitly selected, `route_recruiter_next_stage_review` builds `private-recruiter-next-stage-review-v1` from that debrief. It exposes a bilingual, checklist-based `ready|blocked` review for a closed forward transition such as `technical_screen → hiring_manager`, `technical_deep_dive`, `take_home`, `system_design`, `behavioral_loop`, `panel`, or `offer_stage`. The rendered header repeats both current and target stages so the candidate can verify the handoff. A blocked review returns `needs_intake`, while a stop decision returns terminal `stopped` with `record_stop_decision`; neither asks for more context. A blocked review also lists only the structured topics that must be clarified, never the raw unknown-topic notes. The current stage and backward transitions are rejected; `offer_stage` has no forward transition and is represented as terminal recovery with `record_terminal_stage`; only a manual `prepare-role-interviews` cue can proceed.

The next-stage renderer validates every linked snapshot before writing its
private HTML and emits a fixed success receipt only after the write succeeds;
invalid input returns an opaque error without leaving a partial artifact.
All shipped private HTML templates also declare
`noindex,nofollow,noarchive` and `no-referrer` alongside their restrictive CSP,
and JSON entrypoints normalize oversized-integer parse failures to a fixed
error without a traceback.

## Installation

This source tree is repo-local at `plugins/professional-growth-coach`. Source edits do not update the installed plugin cache. A separate explicitly authorized installation is required to publish a source increment into the local marketplace cache; existing chats may continue using their loaded version, so verify the new installation from a fresh chat. Use the repo-local marketplace workflow only after the exact target and command are approved.

Private JSON artifacts are written through a descriptor-anchored,
collision-safe path: parent symlinks, leaf symlinks, and hardlinked targets are
rejected; bytes are flushed before an atomic no-overwrite publication; and the
result remains mode `0600`. A failed write removes its temporary file and does
not alter an existing artifact.

The recruiter shortlist renderer reads its HTML and CSS only through the same
package-local regular-file boundary, and rejects future-dated artifacts even
when called directly instead of through the builder.

Shortlist decisions are reconciled with contactability before any handoff:
`contactable` requires `do_not_contact_reason=none`, `do_not_contact` requires
a named reason, and `clarify`, `pause`, and `stop` cannot remain contactable.
Those states also select their corresponding collection or observation action,
so a review card cannot imply outreach is ready while its decision says to
pause or clarify.

The same restricted-material detector is shared by shortlist and screen-debrief
validators. Bounded notes and context reject phone-like strings, generic local
paths, and credential or bearer-token markers before they are persisted into a
private artifact or carried into a later handoff.

Recruiter validators also reject a future evaluation date supplied through
`--as-of`; an explicit historical replay must use a date no later than today.
The target-specific screen-intake bridge applies the same inclusive 90-day
window to the source gate itself, so an old gate can only return `clarify_first`
until a fresh gate is built.

The visual release gate treats the full recruiter review flow as one
`recruiter_review` family: shortlist, decision gate, screen intake, screen
debrief, and next-stage review. `scripts/validate_design_tokens.py` checks all
five co-located stylesheets against their declared palette, while
`.superdesign/init/theme.md` records the corresponding source surfaces and
tokens, including the shared continuity rail treatment. A new recruiter
surface, rail state, or color must update both records and its parity tests
before release. The screen-intake `screen-blue` token has a dedicated dark-mode
value so action text remains above the contrast floor on dark surfaces.
The executive dossier reading path also switches to a two-column tablet layout
through 900px, then to one column at 640px, keeping all four destinations
usable without horizontal scrolling.
Its methodology links retain a minimum 44x44px touch target, including when a
link is rendered on a single line.
The decision gate presents its missing-context guidance once, alongside the
next-decision card, so the primary action is not repeated for sighted or screen
reader users.
At the tablet breakpoint, section anchors reserve space for the sticky reading path so each destination opens below the rail; the mobile breakpoint reserves `18rem` for its taller one-column rail.
The career-market matrix uses the same labelled stacked-row treatment in print
as on narrow screens, keeping multi-vacancy comparisons readable on paper
without changing table semantics; its generated mobile/print labels explicitly
use `CanvasText` in forced-colors mode.

Rendering CLIs write the requested private artifact but omit its absolute local
path from the success receipt by default. A trusted caller that already knows
the output target may opt in with `--include-artifact-path`; in-process render
APIs continue to return their richer receipt object without changing the
artifact itself.

Recruiter target builders, validators, and renderers use the same bounded
success receipt: `{"artifact_kind":"…","schema_version":"…","ui_locale":"es|en"}`.
They never print output paths, target identifiers, source snapshots, or free
text on success; failures remain fixed opaque JSON diagnostics.

Bounded JSON validators and market-dossier builders also reject duplicate
keys, oversized integers, and excessive nesting before validation or output;
their command-line failures stay opaque and never echo supplied content. All
private builders, validators, and renderers apply the same boundary to unknown
CLI arguments: they return the fixed `invalid_arguments` diagnostic without
reflecting the rejected value. The LinkedIn client-report validator and
executive dossier renderers also cap multi-error stderr at the shared 16 KiB
diagnostic budget and emit a stable
truncation marker, so malformed private fixtures cannot flood a terminal or
log sink. Learning-option evidence deduplicates source URLs by a normalized
HTTPS identity (host, default port, decoded path, and trailing slash), so
equivalent public URLs cannot masquerade as independent options.
Recruiter shortlist fact IDs are type-checked before uniqueness checks, so
malformed nested values produce the same opaque invalid-artifact response
without a traceback.
Renderer modules can also be imported directly from an installed checkout;
sibling safety helpers resolve relative to the module when no `PYTHONPATH` is
configured.

The repository-level discovery command is part of the release contract. The
decision-gate tests load the schema helper by isolated module spec rather than
mutating the test search path, so same-named root and plugin tests remain
discoverable in one pass.

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
screen it stays visible through all decision regions and marks the nearest
visible region with `aria-current="location"`; hash loads and keyboard clicks
set the active target immediately. Without script it remains a static,
keyboard-visible fallback. The anchors use responsive scroll-safe offsets,
remain available in print, and stack into 44px touch targets at 640px and
below; they do not hide or reorder any evidence.

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

The vacancy research validator now closes the freshness envelope before any
market composition: publication dates inside the inclusive 90-day window must
be `current`, dates outside the window must be `unknown`, and a missing
publication date must be `unknown`. Contradictory date/status combinations are
rejected fail-closed instead of being normalized silently.

Learning-provider research declares its own `evidence_mode`. The v2 artifact
preserves this separately as `learning_evidence_mode`, so a live vacancy sample
cannot make synthetic provider availability, price, or certification evidence
look current. When several options cover one recurring gap, selection is
deterministic: candidate-owned project, lab, free resource, course,
certification, then no-learning; ties use the stable option ID.

Paid learning decisions also enforce a 90-day provider-source freshness window
relative to the dossier snapshot. A source older than that remains a private
`consider` decision with a refresh gate; it cannot authorize a current
recommendation or enrollment.

The v2 aggregate `coach_decision` reconciles individual professional-gap
decisions. If any option requires `apply_with_boundary` or `pause` while no
`project_first` or `consider` path exists, the aggregate is
`review_learning_options`; it never reports `do_nothing_now` while an
individual learning action still needs review.

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
forced-colors, and narrow layouts. The market scan summary uses three compact
columns for sample, query count, and state, then gives its long hiring-fit
limitation a full-width row; the shortlist next-step panel keeps a solid-surface
fallback before its optional `color-mix()` tint for older browsers.
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
and the sample's research date. The link's accessible name includes its `Vn`
vacancy key, escaped employer, and escaped title so repeated titles remain
distinguishable without exposing internal IDs. New builder output preserves the access date,
publication date when known, a 90-day freshness window, and an explicit
`current`/`unknown` reason. Unknown publication dates are rendered as
“publication date: unknown” and never presented as current; the source link's
accessible name also includes the `Vn` vacancy key and escaped employer for
auditability. The link is for
auditability only: it does not open an application flow, send a message, or
authorize any external action.
Source links retain a minimum 44px touch target with centered text so the audit
trail remains usable on narrow screens without changing the action boundary.
Every vacancy card must carry the complete six-field freshness envelope. The
validator rejects contradictory status, basis, reason, or date-window
combinations: a dated posting is current only when its source status is current
and within 90 days; otherwise it is explicitly unknown. A missing publication
date is always unknown with an explicit access-date basis, so hand-authored
artifacts cannot present stale or unverified evidence as current.
Search-limit metadata is reconciled with the evidence count: only a complete
five-vacancy sample may use `target_reached` with `limitation=none`; limited and
unavailable states require an explicit limiting reason before downstream
dossier routing.
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

An explicit CSV bridge is available only when the candidate supplies an
application context: `export_private_recruiter_outcome.py` accepts a validated
`reply_received` receipt plus `candidate_id`, `application_id`,
`application_date`, and `as_of`, then writes one canonical `outcomes.csv` row
with `response_date` set to the observed reply date. It rejects
`screen_requested`, `interview_requested`, and `stop_decision` rather than
turning requests or terminal events into interviews or responses. The export
uses a deterministic `recruiter-receipt-sha256-...` replay key, so repeating
the same receipt/application pair is a no-op; no raw receipt prose, source ID,
candidate aggregation, message, calendar action, or causal claim is added.
The writer rejects symlink/non-regular outputs (including a symlinked immediate
parent) and spreadsheet-formula prefixes in optional text fields and existing
rows before any forced replay. Its temporary file creation and replacement stay
anchored to the validated parent descriptor, so a local parent swap fails closed
instead of following a symlink. Use `--force` only after reviewing an existing
output file: it preserves rows for distinct applications and replaces only the
row for the same `application_id`. Each component of the absolute parent chain
is opened with no-follow semantics before the final descriptor is retained.

After a completed `screen_attended` checkpoint, the rail uses the closed
`debrief_after_screen` action. `route_recruiter_screen_debrief_intake` carries
that validated boundary into an artifact-free prompt for requirement coverage,
scope, and team context; the checkpoint renderer still does not capture,
persist, or review raw notes. The later structured debrief remains
manual-only and does not send, schedule, auto-start preparation, or retain the
screen conversation. The shared rail uses three columns at intermediate
desktop widths and two columns in print so long localized labels remain
legible.

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

`private-recruiter-triage-practice-handoff-v2` is the closed composition
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
The wrapper also carries a `snap-practice-sha256-...` projection snapshot over
the complete unanswered practice session; standalone validation and rendering
reject changed projected context, question, or verified-fact prose unless the
handoff is rebuilt.

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
external action. The validator remains backward-compatible with legacy v1
handoff files that do not carry a projection snapshot; newly built wrappers
are always v2 and carry that projection attestation.

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
