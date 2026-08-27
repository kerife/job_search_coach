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

## Recruiter follow-through checkpoint routing

An explicit `private-recruiter-followthrough-checkpoint-v1` is accepted only with its separately supplied, validated conversion receipt. Treat the pair as candidate-supplied, identity-free, non-aggregated observations. Replay of the same receipt/checkpoint pair is idempotent: do not append a CSV row, duplicate a route, create a packet, reuse an answer, or claim a new outcome. Before local handling, derive the pair's no-persistence key with `replay_fingerprint(checkpoint, receipt)` from the installed validator; equal keys are a no-op replay and changed structural fields produce a distinct pair. This key contains no raw event prose or candidate identity. A `completed` checkpoint sourced from `screen_requested` or `interview_requested` may expose one manual cue to re-enter `prepare-role-interviews`; a `completed` `screen_attended` checkpoint exposes only the manual `debrief_after_screen` cue to re-enter a private conversation. This artifact does not capture or persist debrief notes. Neither cue starts a module, transfers execution context, or bypasses vacancy/fact intake, and the debrief cue never sends or schedules follow-up. `interview_requested` is a neutral observed request, not a guaranteed recruiter-screen stage. `declined` blocks preparation, and any `stop_decision` source blocks preparation regardless of state; its action must be `record_stop_decision` and its rail is terminal. `accepted` and `deferred` remain checkpoints with no preparation authorization. Keep the ordinary CSV route and ordinary recruiter-reply route unchanged when the explicit checkpoint/receipt pair is absent.

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

When a request explicitly asks to expand a recruiter/referral network, find recruiters, or prepare for a first recruiter screen, route to the private `recruiter-target-shortlist-v1` flow before ordinary outreach prose. `route_recruiter_request` is the deterministic local handoff: with three to six candidate-supplied targets and a valid `recruiter_network_expansion_plan`, it runs builder → validator → renderer and returns `case_state=ready`, `selected_module=optimize-professional-profile`, `next_action=review_recruiter_target_shortlist`, a validated offline artifact, and private in-memory `rendered_html` with placeholders and internal IDs removed. If the bounded target set or context is missing, return `case_state=needs_intake`, `next_action=ask_one_intake_question`, and one localized intake question; do not invent identities, contact details, or URLs. The rendered artifact is a private review surface only. It must preserve `draft_only=true`, `consent=not_granted`, `authorization_required=true`, `no_message_action=true`, and `no_calendar_action=true` on every row. Only `advance` rows may hand off to `recruiter_outreach_lab`; all four decisions remain visible in the subsequent `recruiter_target_decision_gate` for manual review. Compound intent matching must not intercept ordinary technical interview preparation or unrelated uses of “network”.

After the shortlist is validated, `route_recruiter_decision_gate` may build `recruiter-target-decision-gate-v1`. It binds the full shortlist snapshot and reconciles `advance|clarify|pause|stop` counts. Its legacy `screen_context` input is bounded context only: reject contact-shaped text, local paths, URLs, and similar private payloads. A validated gate returns the artifact plus private in-memory `rendered_html`; invalid intake remains artifact-free. It is never a preparation handoff; callers with generic context receive `collect_screen_intake` and must continue through the target-specific bridge below. The gate itself never starts preparation or performs an external action.

Before that manual handoff, `route_recruiter_screen_intake` may build `recruiter-target-screen-intake-v1` for one target. The bridge must match the target and gate snapshot, require `stated_stage`, `V-###` vacancy requirements, `F-###` candidate facts, non-unknown company evidence, and exactly four checks (`target_context`, `proof_packet`, `low_friction_ask`, `screen_readiness`). A validated artifact returns its private in-memory `rendered_html`, including for a blocked/clarify state; malformed or non-advance input that cannot build an artifact remains artifact-free. Only an `advance` target with four `pass` checks returns `manual_prepare_role_interviews_review`; `clarify|pause|stop` returns `collect_screen_intake` or `stop_and_record` and an observable measurement event.

After a completed `screen_attended` checkpoint, `route_recruiter_screen_debrief` may build `private-recruiter-screen-debrief-v1` only when the checkpoint and receipt are valid and the linked target-specific intake remains `ready`. The bridge records exactly three coverage topics (`requirement`, `scope`, `team_context`), bounded unknown topics, supported fact IDs, and a manual `continue_review|pause|stop` decision. A validated artifact returns its private in-memory `rendered_html` for ready, incomplete, and terminal stop states. Complete coverage returns `case_state=ready` with `manual_prepare_next_stage_review`; incomplete coverage returns `case_state=needs_intake` with `collect_debrief_context`; a stop decision returns terminal `case_state=stopped` with `record_stop_decision` and never requests more context. The replay fingerprint makes reprocessing idempotent, and no raw transcript, contact, message, calendar, automatic preparation, score, or outcome prediction is retained.

`route_recruiter_next_stage_review` consumes that debrief only with a manually selected forward transition from the closed recruiter-stage taxonomy (`recruiter_screen`, `first_interview`, `technical_screen`, `hiring_manager`, `technical_deep_dive`, `take_home`, `system_design`, `behavioral_loop`, `panel`, `offer_stage`) and builds `private-recruiter-next-stage-review-v1`. A validated artifact returns the private in-memory `rendered_html` for ready, blocked, and terminal stop states. It returns a private `ready|blocked` checklist, maps blocked reviews to `case_state=needs_intake`, maps stop decisions to terminal `case_state=stopped`, rejects same-stage and backward transitions plus stale dates, and preserves the manual-only `prepare-role-interviews` boundary. The rendered header shows `current stage → target stage` in localized copy without identifiers.

## Recruiter reply and send-now routing

When neither an explicit private recruiter-practice request nor an explicit private recruiter-reply triage request is present, inbound recruiter replies, recruiter screen invitations, proposed times, and user requests to send, reply, confirm, accept, schedule, book, or create a calendar item route to `optimize-professional-profile` first so the response includes `recruiter_reply_triage`. Use `awaiting_authorization` only after the exact recipient, finalized draft, action, and target are known; otherwise keep the safe next step as triage or clarification. In all of these cases set `authorization_required: true` because the user is asking for an external action. For a proposed time, keep `proposed_time_state=do_not_accept_or_propose_time_without_exact_authorization`, `no_calendar_action=true`, and `draft_only=true`; do not report that a message was sent, a screen was scheduled, a time was accepted, or a calendar event was created. A prior approval or general send instruction is insufficient unless immediately before execution it names the exact action, exact target, and exact final content or asset identity when content or assets apply.

## Ready module execution

If the chosen state is `ready`, execute the selected module rather than returning a routing-only answer. For the explicit private recruiter-practice or private recruiter-reply triage branches, the validated private artifact is the execution proof; do not emit a router contract, `module_execution_packet`, or internal identifiers. Otherwise, outside the normal local LinkedIn artifact branch, add one `module_execution_packet` row with `candidate_id`, `selected_module`, `execution_depth`, `delivered_sections`, `evidence_ids`, `candidate_next_practice`, `authorization_gate`, and `causality_boundary=descriptive_only_no_guaranteed_outcome`. In the normal LinkedIn artifact branch, the validated dossier and renderer receipt are the execution proof and stay out of client-visible contract rows.

For a `ready prepare-role-interviews` route, include the useful core sections from the interview skill in the same response: `competency_map`, `likely_questions`, `truthful_story_bank`, `practice_answer_coaching`, `role_practice`, `mock_interview`, `scorecard`, `interviewer_questions`, `follow_up_draft`, `first_interview_conversion_plan`, `recruiter_screen_brief`, `recruiter_bridge_script`, `vacancy_candidate_gap_map`, `objection_response_map`, `question_bank`, and `follow_up_lifecycle`. Use stable `V-###`, `F-###`, and `Q-###` IDs. If those sections cannot be delivered from the available vacancy and candidate facts, mark the case `needs_intake` or `blocked_on_evidence` instead of `ready`.
