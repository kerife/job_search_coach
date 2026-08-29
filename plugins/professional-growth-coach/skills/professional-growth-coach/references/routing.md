# Routing

Apply `preserve_current_employment_by_default` to every route. Module choices evaluate market evidence and professional positioning only; they do not advise resignation, quitting, leaving an employer, reducing hours, or creating a voluntary gap. Staying and growing in the current role is valid (`staying_and_growing_is_valid`), and any explicit separation analysis must set `no_resignation_recommendation=true`.

Always build this contract internally for each candidate. Emit it once only for non-artifact responses:

```text
case_state: ready | blocked_on_evidence | needs_intake | awaiting_authorization
evidence_gaps: [specific missing or conflicting facts]
selected_module: module name
next_action: one safe, concrete step
authorization_required: true | false
```

For a normal local LinkedIn artifact, use the internal fields to select and validate the branch, but return no visible router contract, no `module_execution_packet`, no `coach_case_brief`, no `coach_executive_review`, no weekly workstream rows, and no ordered-plan handoff. That client chat ends after the receipt summary plus one verified link.

Choose one module:

- `optimize-professional-profile`: LinkedIn/CV positioning, profile drafts, or a profile conflict.
- `explore-career-options`: role transition or high-compensation direction before a concrete market question.
- `research-professional-market`: current demand, compensation, role requirements, or a target vacancy.
- `optimize-career-assets`: CV, cover letter, portfolio, or ATS assets without a LinkedIn-specific need.
- `prepare-role-interviews`: interview preparation for a specific role or vacancy.
- `recommend-career-learning`: a repeatedly evidenced gap with plausible return.
- `track-career-outcomes`: a 14/30/60/90-day results review.

## Recruiter-conversion observation routing

An explicit conversion receipt is a candidate-supplied observation only, not a candidate identity claim, aggregate, causal explanation, score, fit, or outcome proof. Apply this exact mapping: `contact_received` and `reply_received` → `clarify_context_before_reply`; `referral_received` → `prepare_fact_checked_summary`; `screen_requested` and `interview_requested` → `route_to_prepare-role-interviews`; `stop_decision` → `record_stop_decision`. The mapped value is a manual next step only. Its compact receipt rail uses only closed localized copy for that value; `record_stop_decision` is a terminal recorded state and never says to continue. `interview_requested` stays a neutral observed request label; stage and vacancy context must be re-entered privately before preparation. It must not auto-start a module, create a module packet, send, schedule, or create a calendar item. Keep normal CSV/outcome measurement and ordinary recruiter-reply and LinkedIn routes unchanged when the receipt is absent.

Market evidence routing preserves the evidence count: only a complete five-vacancy sample may use `target_reached` with no limitation; limited and unavailable samples must name the source or search limitation before any downstream dossier route.

## Recruiter follow-through checkpoint routing

An explicit `private-recruiter-followthrough-checkpoint-v1` is accepted only with its separately supplied, validated conversion receipt. Treat the pair as candidate-supplied, identity-free, non-aggregated observations. Replay of the same receipt/checkpoint pair is idempotent: do not append a CSV row, duplicate a route, create a packet, reuse an answer, or claim a new outcome. Before local handling, derive the pair's no-persistence key with `replay_fingerprint(checkpoint, receipt)` from the installed validator; equal keys are a no-op replay and changed structural fields produce a distinct pair. This key contains no raw event prose or candidate identity. A `completed` checkpoint sourced from `screen_requested` or `interview_requested` may expose one manual cue to re-enter `prepare-role-interviews`; contact, reply, and referral receipts remain clarification-only and cannot authorize that preparation route. A `completed` `screen_attended` checkpoint must carry identity-free `target_binding.target_id` and `target_binding.source_gate_snapshot`, exactly matching the target-specific intake. Its source receipt is restricted to `screen_requested` or `interview_requested`, and checkpoint/receipt locales must match. Missing or mismatched binding, incompatible receipt event, or locale drift returns artifact-free `needs_intake`; legacy checkpoints are never silently combined. A bound checkpoint exposes only the manual `debrief_after_screen` cue to re-enter a private conversation. This artifact does not capture or persist debrief notes. Neither cue starts a module, transfers execution context, or bypasses vacancy/fact intake, and the debrief cue never sends or schedules follow-up. `interview_requested` is a neutral observed request, not a guaranteed recruiter-screen stage. `declined` blocks preparation, and any `stop_decision` source blocks preparation regardless of state; its action must be `record_stop_decision` and its rail is terminal. `accepted` and `deferred` remain checkpoints with no preparation authorization. After a completed `screen_attended` checkpoint, `route_recruiter_screen_debrief_intake` accepts either the `screen_requested` or `interview_requested` receipt event and carries the validated checkpoint, receipt, and target-specific intake boundary into an artifact-free prompt for requirement coverage, scope, and team context. The `interview_requested` copy stays neutral and asks the candidate to confirm the stage; it never infers stage from the event. Keep the ordinary CSV route and ordinary recruiter-reply route unchanged when the explicit checkpoint/receipt pair is absent.

Inbound contact without interview language (`messaged`, `emailed`, `reached out`,
schedule/choose-a-time wording, calendar links or proposed times, “asked about my availability”,
“reply to a recruiter”, “me escribió”, “me contactó”, “me pidió disponibilidad”,
or “¿qué le digo?”)
enters artifact-free `private_recruiter_reply_triage` before any draft. It asks
only for an identity-free summary and one verified fact, keeps
`authorization_required=true`, and never sends, schedules, or creates a calendar
item. Received-message wording such as `I got a recruiter message/email` and
`me llegó un mensaje/correo del recruiter` follows the same boundary.

Post-screen progression wording such as “passed the recruiter screen”, “moved
forward to the hiring manager”, and “ya pasé el filtro y ahora sigue” enters
`private_recruiter_next_stage_review` with the same artifact-free debrief intake;
it does not infer a successful outcome or start preparation automatically.

Post-screen follow-through wording (`follow up`, `thank-you`, `no response`,
`ghosted`, `dar seguimiento`, `agradecimiento`, `sin respuesta`, `me dejaron en
visto`) requires recruiter plus screen context and routes to artifact-free
`private_recruiter_screen_debrief` with `collect_debrief_context`. A response
request keeps `private_recruiter_reply_triage` precedence; future or explicitly
not-attended screens keep `recruiter_target_screen_intake` precedence. The
screen-intake renderer removes internal `V-###` requirement keys from rendered
HTML while preserving them in validated source data.

## Private recruiter-practice routing

Before every other route, check for an explicit private recruiter-practice request. It takes precedence over recruiter-reply triage, every LinkedIn branch, and debug, eval, detail, raw, or internal-row requests. When it includes an identity-free vacancy summary and at least one supplied candidate fact, select `prepare-role-interviews` and create the separate private recruiter practice session. This is a private artifact branch for one recruiter-screen question, not a normal local LinkedIn artifact and not a client-report fallback.

If either required input is missing, including when both inputs are missing, use `needs_intake`, keep `authorization_required: false`, and ask exactly one concise question requesting only the missing identity-free vacancy summary or candidate fact. Do not ask a second question or infer the missing input from a profile, recruiter message, or prior case. Do not expose internal identifiers, router rows, module-execution packets, or raw vacancy or candidate-fact text in this intake response.

For a ready private session, the response is limited to the renderer's human summary once, one verified absolute local artifact link, and the statement `No external action is performed.` Keep it one-question/one-answer: score and feedback stay `unknown` before an observed answer, and later feedback uses only that answer and its rubric. Treat the observed answer as ephemeral and no-save-by-default. Do not expose internal identifiers, router rows, module-execution packets, or raw vacancy or candidate-fact text. When an explicit private recruiter-practice request is absent, retain the existing recruiter-reply triage and LinkedIn delivery behavior, including debug, eval, and detail_requested legacy output.

## Private recruiter-reply triage routing

After checking private recruiter-practice and before ordinary recruiter-reply routing, check for an explicit private recruiter-reply triage request. This narrow private branch takes precedence over ordinary `recruiter_reply_triage` (**private triage precedence**), but it does not change normal dossier or debug, eval, and detail_requested behavior when the request is not explicit.

Require an identity-free recruiter-reply summary and one supplied candidate fact. If either is missing, including when both are missing, use `needs_intake`, keep `authorization_required: false`, and ask exactly one concise intake question requesting only the missing identity-free recruiter-reply summary or supplied candidate fact. Do not infer either input from a raw reply, profile, recruiter message, or prior case. Do not retain or display a raw reply, identity, contact detail, internal identifier, router row, draft reply, action, proposed time, or calendar detail.

When both inputs are supplied, create only the closed `private-recruiter-reply-triage-v1` decision card, validate it with `validate_private_recruiter_reply_triage.py`, and render it with `render_private_recruiter_reply_triage.py --include-artifact-path` for the trusted caller that must deliver a verified absolute local artifact link. Direct CLI receipts omit the local path by default; consumers that parse `artifact_path` must opt in explicitly. Its private delivery is limited to the renderer's human summary once, one verified absolute local artifact link, and `No external action is performed.` The card may state a private handoff only when its closed contract permits it; it does not send, reply, accept, schedule, or create a calendar item. Do not expose internal identifiers, raw reply content, router rows, module-execution packets, or a normal dossier/client-report fallback in this branch.

For `ready_for_private_prep`, the closed handoff is only a manual re-entry cue for `prepare-role-interviews`, scoped to one recruiter-screen question and an identity-free summary plus verified fact. It is **manual input only**: it does not auto-start, transfer execution context, create a `module_execution_packet`, or emit router rows. Its exact boundary is `candidate_answer_state=unanswered` and `score_state=unknown` until the candidate supplies an answer in a later explicit preparation request. Clarify-first and stop cards omit the handoff. Private triage precedence applies before all ordinary recruiter and LinkedIn routes; normal recruiter-reply behavior remains unchanged, including legacy debug/eval/detail behavior.

When the candidate explicitly supplies a v2 triage JSON file for private re-entry,
the only file route is a deliberate two-step projection: first
`build_private_recruiter_triage_practice_handoff.py --input TRIAGE.json --output HANDOFF.json`,
then `render_private_recruiter_triage_practice_handoff.py HANDOFF.json --output PRACTICE.html`.
The builder accepts only a validated `private-recruiter-reply-triage-v2` ready
handoff and revalidates its snapshot-bound provenance before producing the closed
wrapper. The renderer independently validates that wrapper and its nested
practice session before it writes a private `0600` HTML artifact. Its minimal
receipt exposes only `artifact_kind=private_recruiter_triage_practice_handoff_html`
and `ui_locale`; do not surface a path, source snapshot, IDs, raw reply, answer,
score, or action result.

This remains a draft-only, manual re-entry route: neither command starts
rehearsal, persists an answer, sends, schedules, uploads, or authorizes an
external action. A v1 triage remains in its legacy route and cannot be passed as
a compatible substitute to either command; manually recreate and validate v2
before considering this private handoff.

## Multi-module routing

Outside the normal local LinkedIn artifact branch, use a multi-module ordered plan when one self-service or coach mode request contains several safe workstreams, such as LinkedIn audit plus CV rewrite plus imminent interview preparation. The router contract still gets exactly one `selected_module`: choose the first module that should run safely after evidence and authorization gates. Then add an `ordered plan` with one line per later module. In the artifact branch, keep later-module planning internal and end the client chat after the verified link.

Ordered plan rules:

- Start with evidence repair or `optimize-professional-profile` when visible profile facts conflict with CV facts.
- Use `research-professional-market` before `explore-career-options` when current demand, compensation, geography, or role requirements are needed.
- Use `optimize-career-assets` before `prepare-role-interviews` when the vacancy-specific fact matrix is missing.
- Use `recommend-career-learning` only after repeated target evidence shows a gap and cheaper proof alternatives were considered.
- Use `track-career-outcomes` only after dated application, response, interview, or offer records are available for one isolated candidate.
- Keep coach mode candidates separated; never put two candidates in the same ordered plan item.

## Coach case brief

Outside the normal local LinkedIn artifact branch, add `coach_case_brief` for multi-module work as the bridge from routing to execution. The brief is not a motivational summary; it is the case manager's decision record for the next cycle. Use these fields exactly: `candidate_id`, `case_goal`, `coach_verdict`, `evidence_strength`, `primary_bottleneck`, `module_sequence`, `handoff_ready`, `first_interview_strategy`, `weekly_commitment`, `success_signal`, `stop_condition`, `privacy_boundary`, and `causality_boundary=descriptive_only_no_guaranteed_outcome`.

Set `handoff_ready=false` when evidence conflicts, target criteria are missing, assets are not vacancy-specific, or external action authorization is missing. For a first-interview goal, the safe sequence is usually `optimize-professional-profile > optimize-career-assets > research-professional-market > prepare-role-interviews > track-career-outcomes`: fix public positioning and proof first, prepare one targeted application packet, research the vacancy/market evidence, practice the first conversation, then measure outcomes. Do not include `recommend-career-learning` unless repeated role evidence shows a skill gap and a lower-effort proof asset would not close the gap.

The brief must preserve candidate isolation, avoid benchmarking without consent, and never promise interviews, offers, faster hiring, compensation increases, or causal lift from any intervention.

## Coach executive review

Outside the normal local LinkedIn artifact branch, add `coach_executive_review` after `coach_case_brief` for multi-module work. This is the one-screen executive decision the candidate can act on this week. Use these fields exactly: `candidate_id`, `diagnosis`, `decision`, `decision_rationale`, `priority_order`, `tradeoffs`, `risk_register`, `seven_day_plan`, `defer_until`, `first_interview_path`, `measurement_plan`, `leading_indicators`, `outcome_signals`, `privacy_boundary`, `authorization_gate`, and `causality_boundary=descriptive_only_no_guaranteed_outcome`.

The review should diagnose the blocking constraint in one phrase, choose one next-cycle decision, explain why that decision beats the obvious alternative, name the priority order, name the tradeoffs, list operational risks with mitigations, and state what to defer until evidence or authorization gates are satisfied. Candidate-facing fields must read like coach notes a person can act on, not snake_case compliance tokens. The `seven_day_plan` must use day-labelled actions, beginning with evidence repair when claims conflict. The `first_interview_path` should connect profile positioning, application packet, recruiter bridge, and stage-specific practice. The `measurement_plan` should separate controllable `leading_indicators` from observed `outcome_signals`; neither may be framed as proof that the intervention caused outcomes. Keep external actions blocked until exact action-and-target authorization.

## Weekly operating plan

Outside the normal local LinkedIn artifact branch, add `coach_weekly_operating_plan` after `coach_executive_review` for multi-module work, followed by exactly five `coach_weekly_workstream` rows. This is the operating board for the next seven days. The plan row uses `coach_weekly_operating_plan=multi_module_weekly_execution_board` and fields `candidate_id`, `weekly_goal`, `source_review`, `workstream_count=5`, `sequence_model=evidence_repair_to_assets_to_market_to_interview_to_measurement`, `primary_constraint`, `week_exit_criteria`, `blocked_external_actions`, `measurement_boundary=leading_indicators_are_observations_not_causal_proof`, `privacy_boundary=single_candidate_only_no_benchmark_without_consent`, `authorization_gate=exact_action_and_target_required_before_external_action`, `draft_only=true`, and `no_external_action=true`.

Workstream rows use `coach_weekly_workstream=weekly_execution_lane` and cover exactly `linkedin_positioning`, `application_packet`, `market_targeting`, `interview_prep`, and `outcome_tracking`. Each row needs `candidate_id`, `workstream`, `module`, `objective`, `required_evidence`, `deliverable`, `done_when`, `risk_if_skipped`, `metric_to_log`, `owner=candidate|candidate_with_coach_review`, `day_range`, `authorization_need`, `next_safe_action`, `draft_only=true`, and `no_external_action=true`. Keep every workstream private/draft-only until exact action-and-target authorization. Do not promise first interviews, recruiter replies, offers, compensation, faster hiring, ranking, or causal lift.

Choose exactly one `case_state` in this order:

For a normal local LinkedIn diagnostic with at least one inspectable or supplied LinkedIn section, a conflicting or unsupported claim remains `unknown` and blocked for public copy but does not block the entire honest diagnostic. The case may remain `ready` for a private partial dossier when the unresolved issue can be isolated: mark affected copy `requires_confirmation` or `omit`, keep every other claim within its evidence boundary, and put at most the first decision-changing question in chat. Use `blocked_on_evidence` only when the unresolved issue blocks the entire honest diagnostic. If there is no other inspectable or supplied evidence, do not create a dossier; ask exactly one useful intake question.

Outside that narrow partial-dossier exception:

1. Use `blocked_on_evidence` for a source conflict or unsupported material claim. This wins over every later state.
2. Otherwise use `needs_intake` when a required goal, location, constraint, or target detail is missing.
3. Otherwise use `awaiting_authorization` only when evidence and intake are sufficient and a requested external action has an exact action and target ready for authorization.
4. Otherwise use `ready`.

Route a source conflict to `optimize-professional-profile`; ask for confirmation and do not draft the disputed section as ready public copy. The private partial dossier exception above may still diagnose supported sections and hold the disputed copy. Set `authorization_required: true` independently whenever the request includes an external action, even if an unresolved conflict or intake gap wins the `case_state`. Drafting and analysis alone require `false`.

## Explicit recruiter-network shortlist route

When a request explicitly asks to expand a recruiter/referral network, find recruiters, or prepare for a first recruiter screen, route to the private `recruiter-target-shortlist-v1` flow before ordinary outreach prose. Natural English and Spanish forms such as `network with recruiters`, `expand my recruiter network`, `grow my recruiter network`, `build recruiter relationships`, `recruiter referrals`, `meet recruiters`, `conocer reclutadores`, `referidos de reclutadores`, `recruiter outreach`, `recruiter networking`, `recruiter connections`, `first interview with a recruiter`, `first interview with the recruiter`, `initial interview with the recruiter`, `first call with a recruiter`, `networking con recruiters`, `networking con reclutadores`, `primera entrevista con un reclutador`, `entrevista inicial con el reclutador`, and `primera llamada con la reclutadora` are covered; ordinary technical interview, Network Engineer, and data-network requests remain outside this route. Preparation phrases such as `get ready for a recruiter phone screen` and `preparing for a recruiter interview` stay in screen intake, while completed follow-through such as `I talked with the recruiter` and `what happens after talking to a recruiter?` retains post-screen precedence. `route_recruiter_request` is the deterministic local handoff: with three to six candidate-supplied targets and a valid `recruiter_network_expansion_plan`, it runs builder → validator → renderer and returns `case_state=ready`, `selected_module=optimize-professional-profile`, `next_action=review_recruiter_target_shortlist`, a validated offline artifact, and private in-memory `rendered_html` with placeholders and internal IDs removed. If the bounded target set or context is missing, return `case_state=needs_intake`, `next_action=ask_one_intake_question`, and one localized intake question that names the minimum plan: targets/context, goal/segments, 3–5 manual queries, weekly time, stop condition, and proof theme. Invalid target container types or recursively nested in-memory plans must take the same artifact-free intake path; do not invent identities, contact details, or URLs. The rendered artifact is a private review surface only. It must preserve `draft_only=true`, `consent=not_granted`, `authorization_required=true`, `no_message_action=true`, and `no_calendar_action=true` on every row. Only `advance` rows may hand off to `recruiter_outreach_lab`; all four decisions remain visible in the subsequent `recruiter_target_decision_gate` for manual review. Compound intent matching must not intercept ordinary technical interview preparation or unrelated uses of “network”.

Post-screen classification must treat explicit non-completion as pre-screen intake before checking debrief or next-stage intent. English forms include `didn't attend`, `did not complete`, `have not had`, `had no`, `have no`, `never had`, `never completed`, `never went`, and `didn't go`; Spanish forms include `no asistí`, `no tuve`, `todavía no`, `aún no`, `nunca tuve`, `nunca asistí`, `nunca fui`, `no fui`, `no me presenté`, and `nunca pasé por`. These requests return artifact-free `recruiter_target_screen_intake` with `selected_module=prepare-role-interviews` and `next_action=collect_screen_intake`; positive completion wording remains eligible for debrief or next-stage review. The `never`/`nunca`/`no fui`/`no me presenté` checks are restricted to recruiter screen/interview/call/conversation events, so phrases such as `had no trouble` or `had no questions` remain completed-screen language.

Target-vacancy research applies the same temporal boundary to employer
qualification evidence: `source_date` and `access_date` cannot be after the
artifact `as_of_date`, preventing future employer facts from entering a
historical snapshot.

Phrases such as `had no trouble` or `had no questions` describe a completed
screen rather than a missing screen; with an explicit next-step question they
use the next-stage route, while explicit debrief/review wording still wins.

Conversational non-attendance also takes the pre-screen intake route when
recruiter context is explicit: `never went through`, `never spoke`, `no hablé`,
and equivalent bounded forms return `recruiter_target_screen_intake` without an
artifact. Positive `spoke with` or `hablé con` wording remains eligible for
post-screen debrief or next-stage review.

Negative post-screen observations such as `rejected`, `declined`, `rejection`,
`unsuccessful`, `failed the recruiter screen`, `failed the recruiter
screening`, `didn't get past the recruiter screen`, `got a no after the
screen`, `said no`, `not selected`, `another candidate`, `moved forward with
another candidate`, `no pasé el filtro`, `no me eligieron`, `me rechazaron`,
`me descartaron`, or `siguió con otra persona` also route to the
artifact-free `private_recruiter_screen_debrief` with
`selected_module=track-career-outcomes` and `next_action=collect_debrief_context`
when recruiter or screen context is present. This records the candidate's
observation without inferring a cause or outcome, while explicit non-attendance
retains pre-screen intake precedence.

Natural post-screen requests use precedence `debrief > next_stage > shortlist > ordinary`. A recruiter/screen context combined with `debrief`, review language, or explicit completed-screen wording routes artifact-free to `private_recruiter_screen_debrief` with `selected_module=track-career-outcomes` and `next_action=collect_debrief_context`; the context vocabulary includes recruiter calls and conversations (`call`, `conversation`, `llamada`, `conversación`, `hablé con`, `spoke to`, `talking with`, `speaking to`, `hablar con`, `interviewed`). Follow-through also recognizes `has not replied`, `never replied`, `no respondió`, `nunca respondió`, and `no recibí respuesta`. Common next-step forms such as `what comes next`, `what comes after`, `what do I do next`, `next step`, and `siguiente paso` route to `private_recruiter_next_stage_review` with `selected_module=prepare-role-interviews` and the same context-collection boundary. A completed screen plus readiness wording such as `not yet ready for the next stage` remains in the next-stage branch. Negated or future screen language (`have not had`, `never had`, `never completed`, `never went`, `didn't go`, `get ready for my recruiter phone screen`, `scheduled for next week`, a named future weekday/month date, `aún no`, `nunca tuve`, `nunca asistí`, `nunca fui`, `no fui`, `no me presenté`, `nunca pasé por`, `mañana`) takes precedence over those post-screen patterns and returns artifact-free `recruiter_target_screen_intake` with `next_action=collect_screen_intake`, so preparation is never described as a completed screen. The classifier requires recruiter or screen/interview context, so generic technical-interview preparation remains ordinary coaching and recruiter networking remains the shortlist route. Inbound triage additionally recognizes slot-booking/setup requests, choose-a-slot wording, shared times, and received recruiter email or LinkedIn messages. Contact, send, reply, respond, email, contestar, enviar, mandar, connect, schedule, and similar wording always sets `authorization_required=true` before classification and on the ordinary fallback, without performing an action. Private conversion-outcome and follow-through checkpoint replays require `--as-of` in canonical `YYYY-MM-DD` form; alternate ISO spellings are rejected at the CLI boundary so validation and rendered receipts share one date contract.

The classifier treats English `screening` as the same recruiter-screen context as `screen` across completed, next-stage, invitation, future, and non-attendance forms. This keeps requests such as `I completed my recruiter screening`, `after the recruiter screening, what comes next?`, and `I have a recruiter screening next week` on the same artifact-free routes without broadening generic technical-screening requests.

After the shortlist is validated, `route_recruiter_decision_gate` may build `recruiter-target-decision-gate-v1`. It binds the full shortlist snapshot, requires the gate locale to match the embedded shortlist locale, and reconciles `advance|clarify|pause|stop` counts. Its legacy `screen_context` input is bounded context only: reject contact-shaped text, local paths, URLs, and similar private payloads. The renderer presents the highest-score `advance` target as the first target to review; when none can advance, it labels the highest-score fallback as blocked so a score never implies eligibility. A validated gate returns the artifact plus private in-memory `rendered_html`; invalid intake remains artifact-free. It is never a preparation handoff; callers with generic context receive `collect_screen_intake` and must continue through the target-specific bridge below. The gate itself never starts preparation or performs an external action.

Before that manual handoff, `route_recruiter_screen_intake` may build `recruiter-target-screen-intake-v1` for one target. The bridge must match the target and gate snapshot, require `stated_stage`, `V-###` vacancy requirements, `F-###` candidate facts, non-unknown company evidence, a `source_date` no older than 90 days from the gate snapshot, and exactly four checks (`target_context`, `proof_packet`, `low_friction_ask`, `screen_readiness`). The builder deep-copies those checks before returning the artifact so later caller mutations cannot change readiness or handoff state. The gate snapshot itself must also be no older than 90 days from the evaluation date; an old gate is valid only as `clarify_first` with `clarify_context` and must be rebuilt before preparation. Stale context is valid only as `clarify_first` with `clarify_context`; it can never return a manual preparation handoff until refreshed. A validated artifact returns its private in-memory `rendered_html`, including for a blocked/clarify state; malformed or non-advance input that cannot build an artifact remains artifact-free with a route-specific question requesting stage, requirements, facts, company evidence, and the four checks. Only an `advance` target with fresh context, a fresh gate, and four `pass` checks returns `manual_prepare_role_interviews_review`; `clarify|pause|stop` returns `collect_screen_intake` or `stop_and_record` and an observable measurement event.

After a completed `screen_attended` checkpoint, `route_recruiter_screen_debrief` may build `private-recruiter-screen-debrief-v1` only when the checkpoint and receipt are valid and the linked target-specific intake remains `ready`; runtime validation reconciles both `target_binding` fields before building. The bridge records exactly three coverage topics (`requirement`, `scope`, `team_context`), bounded unknown topics, supported fact IDs, and a manual `continue_review|pause|stop` decision. A validated artifact returns its private in-memory `rendered_html` for ready, incomplete, and terminal stop states. Complete coverage returns `case_state=ready` with `manual_prepare_next_stage_review`; incomplete coverage returns `case_state=needs_intake` with `collect_debrief_context`; an artifact-free failure asks specifically for the attended-screen checkpoint, receipt, target intake, and structured debrief; a stop decision returns terminal `case_state=stopped` with `record_stop_decision` and never requests more context. The replay fingerprint includes the binding so reprocessing remains idempotent, and no raw transcript, contact, message, calendar, automatic preparation, score, or outcome prediction is retained.

The debrief renderer exposes a labeled three-state coverage summary (`discussed`, `not_discussed`, `unclear`) with explicit localized labels and counts; it never collapses state counts into an unlabeled numeric pair. The summary remains readable in responsive, dark, high-contrast, forced-colors, and print contexts.

The next-stage JSON Schema mirrors the runtime terminal boundary: when the embedded intake stage is `offer_stage`, every forward `next_stage` is rejected. Cross-artifact target-binding equality remains a runtime semantic check because standard JSON Schema cannot compare two independent values.

`route_recruiter_next_stage_review` consumes that debrief only with a manually selected forward transition from the closed recruiter-stage taxonomy (`recruiter_screen`, `first_interview`, `technical_screen`, `hiring_manager`, `technical_deep_dive`, `take_home`, `system_design`, `behavioral_loop`, `panel`, `offer_stage`) and builds `private-recruiter-next-stage-review-v1`. It validates the debrief, receipt, target intake, and checkpoint before deriving any transition recovery; invalid source inputs stay artifact-free with an explicit evidence gap. A validated artifact returns the private in-memory `rendered_html` for ready, blocked, and terminal stop states. It returns a private `ready|blocked` checklist, maps blocked reviews to `case_state=needs_intake`, maps stop decisions to terminal `case_state=stopped`, rejects same-stage and backward transitions plus stale dates, and preserves the manual-only `prepare-role-interviews` boundary. When the debrief is already complete but the selected stage is invalid, non-terminal stages use `next_action=select_forward_stage` and expose only taxonomy-derived `allowed_next_stages`; `offer_stage` is terminal and instead returns `case_state=terminal`, `next_action=record_terminal_stage`, `terminal_reason=offer_stage_has_no_forward_transition`, and no allowed stages. Other failures ask specifically for the missing debrief/checkpoint context. The rendered header shows `current stage → target stage` in localized copy without identifiers.

All five recruiter review artifacts render the same localized, non-interactive five-step continuity rail: shortlist, decision gate, screen intake, screen debrief, and next-stage review. The current artifact alone carries `aria-current="location"`; the rail is a static `section`, not a navigation landmark, collapses to one column below 420px, uses 2px rail and marker borders in `prefers-contrast: more`, does not infer completed stages, and does not add links, contacts, messages, calendar actions, or other external behavior. Its labels and markup come from `scripts/recruiter_continuity_rail.py` and remain identity-free across screen, print, forced-colors, and responsive output. The five rail styles preserve `overflow-wrap: anywhere` inside their print rules so long localized target or company names cannot overflow the two-column paper layout. The compact conversion-outcome, follow-through checkpoint, and recruiter-practice rail styles explicitly select two columns in print as well; their narrow-screen rule remains one column.

The candidate-facing Markdown validator rejects every URI scheme with an
authority (`scheme://`) unless it is a permitted validated LinkedIn source;
this includes `ftp`, `ws`, `gopher`, and embedded userinfo. Dangerous inline
schemes such as `javascript`, `vbscript`, and `data` remain rejected separately.
The learning, vacancy, and LinkedIn secondary-source URL policies also reject
raw ASCII control/format characters before URL parsing, so tab/newline/carriage-
return obfuscation cannot be normalized into an accepted public URL.

In forced-colors mode, shortlist and decision-gate rows retain the redundant left-border styles for `advance`, `clarify`, `pause`, and `stop` (`solid`, `dashed`, `double`, and `dotted`), so high-contrast comparison does not depend on color.

Shortlist cards and the overview expose `context_priority_score / 100` only as a deterministic manual-review ordering. The adjacent localized note must say that it does not predict a response; keep the note visually secondary and preserve it in print, forced-colors, and high-contrast output. Recruiter routing recognizes talent-acquisition, talent-partner, sourcer, and headhunter wording, passive or called inbound contact, plain post-screen waiting/thanks wording, and natural recruiter-screen preparation requests. These aliases affect routing only and never infer an outcome or authorize an external action.

All bounded prose validators apply the shared normalization contract before checking privacy, markup, and Unicode-control rules. Normalization decodes nested percent/HTML layers to a bounded fixed point and fails closed when input still changes after the depth budget. This includes encoded forms, which must be rejected when they decode to private contact data, URLs, authorization-like text, or controls. Dangerous URL detection also removes ASCII controls and spaces before evaluating the scheme, so tab- or newline-obfuscated variants such as `java\tscript:` remain blocked.

Candidate-facing LinkedIn Markdown is also rejected when normalized text contains active HTML elements, inline event-handler attributes, or dangerous `javascript:`, `vbscript:`, or `data:` URL schemes. This applies to visible report prose and ordinary evidence appendices before rendering.

The JSON Schemas are closed contracts at the same snapshot boundaries as runtime: the
embedded shortlist, gate, intake, receipt, checkpoint, and debrief envelopes
reject unknown fields. Schema conditionals keep debrief decision → event →
safe action and next-stage state → handoff action coherent, and enumerate the
forward transition matrix. Runtime validation remains authoritative for
snapshot hashes, dates, and cross-artifact equality; schema-valid input never
authorizes preparation, messaging, scheduling, or another external action.
schema-only acceptance is therefore not an authorization signal. The private
screen-debrief schema also closes the embedded shortlist network plan, target
rows, and delivery envelope with the same typed fields, bounds, enums, and
authorization constants as the standalone shortlist contract; schema-only
consumers reject malformed nested values before runtime validation.

## Recruiter reply and send-now routing

When neither an explicit private recruiter-practice request nor an explicit private recruiter-reply triage request is present, inbound recruiter replies, recruiter screen invitations, proposed times, and user requests to send, reply, confirm, accept, schedule, book, or create a calendar item route to `optimize-professional-profile` first so the response includes `recruiter_reply_triage`. Use `awaiting_authorization` only after the exact recipient, finalized draft, action, and target are known; otherwise keep the safe next step as triage or clarification. In all of these cases set `authorization_required: true` because the user is asking for an external action. For a proposed time, keep `proposed_time_state=do_not_accept_or_propose_time_without_exact_authorization`, `no_calendar_action=true`, and `draft_only=true`; do not report that a message was sent, a screen was scheduled, a time was accepted, or a calendar event was created. A prior approval or general send instruction is insufficient unless immediately before execution it names the exact action, exact target, and exact final content or asset identity when content or assets apply.

Natural invitation and scheduling variants (`got invited`, `received an invitation`, `was asked`, `pending`, `booked`, `scheduled to speak`, `me invitaron`, `recibí una invitación`, `me pidieron`, `pendiente`, `agendada`) route to artifact-free `recruiter_target_screen_intake` when the candidate only asks for preparation. When the same event asks to reply, accept, confirm, email, or follow up, `route_recruiter_request` returns artifact-free `private_recruiter_reply_triage` with `next_action=collect_recruiter_reply_triage_context`, `evidence_gaps=identity_free_recruiter_reply_summary,one_verified_candidate_fact`, and `authorization_required=true`; no response or calendar action is performed. Follow-up terms (`follow up`, `follow-up`, `dar seguimiento`) always preserve the authorization flag on fallback routes.

The private recruiter reply triage renderer includes a static three-step continuity rail (`classify reply`, `clarify or prepare`, `manual re-entry`) in localized copy. Exactly one rail step is marked `aria-current="step"` according to `clarify_first`, `ready_for_private_prep`, or `stop`; the handoff detail remains pending without creating a second current marker. The rail is orientation only and preserves responsive, dark, high-contrast, forced-colors, reduced-motion, and print boundaries.

The target-specific screen-intake, post-screen debrief intake, full debrief, and next-stage review routers catch bounded deep-copy recursion failures and return the same artifact-free `needs_intake` contract as other malformed inputs; they never leak a traceback from an in-memory nested context.

## Ready module execution

If the chosen state is `ready`, execute the selected module rather than returning a routing-only answer. For the explicit private recruiter-practice or private recruiter-reply triage branches, the validated private artifact is the execution proof; do not emit a router contract, `module_execution_packet`, or internal identifiers. Otherwise, outside the normal local LinkedIn artifact branch, add one `module_execution_packet` row with `candidate_id`, `selected_module`, `execution_depth`, `delivered_sections`, `evidence_ids`, `candidate_next_practice`, `authorization_gate`, and `causality_boundary=descriptive_only_no_guaranteed_outcome`. In the normal LinkedIn artifact branch, the validated dossier and renderer receipt are the execution proof and stay out of client-visible contract rows.

For a `ready prepare-role-interviews` route, include the useful core sections from the interview skill in the same response: `competency_map`, `likely_questions`, `truthful_story_bank`, `practice_answer_coaching`, `role_practice`, `mock_interview`, `scorecard`, `interviewer_questions`, `follow_up_draft`, `first_interview_conversion_plan`, `recruiter_screen_brief`, `recruiter_bridge_script`, `vacancy_candidate_gap_map`, `objection_response_map`, `question_bank`, and `follow_up_lifecycle`. Use stable `V-###`, `F-###`, and `Q-###` IDs. If those sections cannot be delivered from the available vacancy and candidate facts, mark the case `needs_intake` or `blocked_on_evidence` instead of `ready`.
