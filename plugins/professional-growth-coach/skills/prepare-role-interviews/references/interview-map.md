# Vacancy-to-interview map

## Intake

Require the exact vacancy text or a stable vacancy requirement list, company evidence, candidate fact matrix, and stated interview stage. Assign each requirement `V-###`; preserve its source and evidence label. For company evidence, record `source_date` and `source_state` (`active`, `stale`, `unavailable`, or `synthetic`). `synthetic` evidence is a test fixture, not a current claim.

## Private recruiter-practice branch

Use this branch only for an explicit private recruiter-practice request. With an identity-free vacancy summary and at least one supplied candidate fact, create the separate private recruiter practice session for one recruiter-screen question. Do not use the full interview map, a normal LinkedIn dossier, or the LinkedIn client report for this branch. If the vacancy summary or candidate fact is absent, ask one concise question for the missing input and wait; do not derive it from profile text or a prior conversation.

A dossier-to-practice handoff has two sources: the validated dossier may supply
only candidate evidence and selected-question context, while a separate
identity-free vacancy summary supplies the requirement. Do not infer or invent
a vacancy requirement from dossier text or provenance. The handoff remains
draft-only, needs manual re-entry, and never auto-starts a practice session.
The rendered practice session includes a static continuity rail showing the
supplied evidence, rehearsal, and pending next version; it is a reading aid,
not an execution control or authorization.
It also begins with a first-conversation readiness card showing the
recruiter-screen stage, evidence confirmation state, private-only boundary, and
manual next step. The card is derived from validated session state and must not
expose internal references, raw answers, or external-action controls.

### Recruiter-reply triage composition

`private-recruiter-triage-practice-handoff-v1` may compose exactly one private
rehearsal only from a validated `private-recruiter-reply-triage-v2` in
`ready_for_private_prep` with `handoff_allowed=true` and one `verified` fact.
Recalculate the triage snapshot first; the source, packet, and re-entry snapshot
must match, and the selected `F-001`, `Q-001`, and permitted preparation scope
must still be the exact validated references. Do not convert `clarify_first`,
`stop`, candidate-reported evidence, snapshot drift, or any mismatched reference
into a practice session.

The composed session is private and unanswered: it is
`ready_to_practice`, has `observed_answer=null`, and keeps pre-answer feedback
and scoring unknown. Preserve only the validated question, fixed scope-specific
guidance, verified-fact summary, and exact snapshot provenance. Never copy raw
reply material, identifiers, URLs, calendar or time details, or a prior answer.
The handoff is `draft_only=true`, has no external actions, does not save locally,
and never auto-starts practice. It is a manual re-entry cue for a later explicit
private rehearsal request; it is not an execution control, authorization, or
prediction about interview readiness or outcome.

For this validated triage route, render one static localized first-answer
outline directly after the claim boundary and before route or handoff panels.
It may reuse only the fixed three-step coaching for the validated question kind;
it does not collect or save an answer, update evidence, or initiate an external
action.

### Triage wrapper to private HTML

File delivery is an explicit, two-stage manual action. First compose a validated
v2 triage into `private-recruiter-triage-practice-handoff-v1` with
`build_private_recruiter_triage_practice_handoff.py --input TRIAGE.json --output HANDOFF.json`.
Then independently validate and render only that wrapper with
`render_private_recruiter_triage_practice_handoff.py HANDOFF.json --output PRACTICE.html`.
The renderer must verify the wrapper's exact snapshot provenance and nested
practice-session contract before it projects HTML; a direct practice session is
not a substitute for the wrapper route.

Both private outputs are written atomically with mode `0600`. The renderer emits
only the minimal receipt `artifact_kind=private_recruiter_triage_practice_handoff_html`
and `ui_locale`; it never reveals the output path, snapshot, source IDs, raw
reply, answer, feedback, score, or an action outcome. The HTML remains a private
draft with a visible manual re-entry boundary. It never starts practice, saves an
answer, sends, schedules, uploads, or authorizes an external action. A legacy v1
triage is readable only on its legacy route: recreate a validated v2 triage
manually before composing or rendering this private wrapper.

The sequence is one-question/one-answer. Before the candidate answers, feedback and any score remain `unknown` (`score_state=unknown`); after the observed answer, feedback may reference only the observed answer and the rubric. In `feedback_available`, keep `score=unknown` and use `score_state=categorical` with only the rubric labels `solid`, `confirm`, or `do_not_assert`; numeric scores are invalid. Keep the answer ephemeral and no-save-by-default. The client-facing result contains only the private-session summary and verified local artifact link, never internal identifiers or raw vacancy or candidate-fact text. No external action is performed.

In feedback_available, visible feedback uses fixed bilingual guidance selected
only by the validated question kind and supplied categorical label. The most
cautious present label governs one separate next-private-rehearsal decision:
do_not_assert > confirm > solid. This is evidence-bounded coaching, not semantic
verification, readiness scoring, or an interview-outcome claim; the raw answer
and feedback statement remain omitted from the artifact.

## Traceability map

For every likely question, capture `question ID=Q-###`, `vacancy requirement ID=V-###`, stage, rationale, answer candidate fact ID(s), and the actual `question_text="...?"`. A question without a vacancy requirement ID is `unknown: (untraceable)` and must be omitted or clearly treated as optional candidate-led clarification. The one-question mock repeats the same IDs and exact text as `mock_question="...?"`; do not score it until the candidate responds.

For recruiter screens, add exactly one `interview_asset_integration_plan=linkedin_learning_proof_to_screen_practice` row near the traceability matrix. This row is the bridge from profile, learning, and proof assets into private screen practice. Required fields are `source_profile_asset`, `source_learning_asset`, `source_proof_asset`, `target_stage=recruiter screen`, `target_question_ids`, `target_requirement_ids`, `candidate_fact_ids`, `asset_use_decision=use_private_practice_only|defer_until_verified|block`, `profile_claim_to_rehearse`, `proof_artifact_to_prepare`, `learning_gap_to_bridge`, `red_line_claims`, `practice_task`, `review_gate`, `outcome_boundary=not_an_interview_offer_salary_or_roi_prediction`, `draft_only=true`, and `no_external_action=true`. Use it to explicitly connect LinkedIn/profile wording, proof artifacts, and learning/portfolio gaps to the screen question without claiming unsupported experience. Do not publish, send, schedule, share, or treat an artifact as public proof without exact action-and-target authorization and the required ownership, secrets, confidentiality, and public-disclosure review.

| Stage | Map question to | Preparation boundary |
| --- | --- | --- |
| recruiter screen | motivation, scope, logistics | Never claim company process; ask it. |
| hiring-manager | ownership, priorities, collaboration | Use stories only with candidate fact ID support. |
| technical screen | named technical requirements and constraints | Do not claim technical experience absent from facts. |
| technical deep dive | named technology and operating practice | Do not claim tools or incidents absent from facts. |
| take-home | supplied exercise requirement or constraint | Do not complete, submit, or invent an exercise. |
| system design | stated architecture/reliability requirements | State assumptions and unknown constraints. |
| behavioral loop | competency and behavioral evidence | Use fact-bounded STAR outline, not invented results. |
| panel | supplied panel evidence and vacancy requirements | Keep panel composition and process `unknown:` when absent. |
| offer-stage | decision, scope, and written-offer clarifications | Do not promise acceptance or assert compensation. |

Prepare one requested stage per response. Mark all other stages `not applicable because <reason>`, including technical screen, take-home, and panel when they are not requested. Do not infer a company process from a job title, market convention, another employer, or a “typical” process; when company evidence is unavailable, the process stays `unknown:`.

## Recruiter-screen and objection map

`first_interview_conversion_plan` is required for recruiter-screen preparation. It is a one-page plan to obtain a recruiter screen, not a hiring prediction or promise. Include:

- `conversion_goal`: phrase as "obtain a recruiter screen" or "earn a first recruiter conversation"; never "secure an interview".
- `role_fit_thesis`: map the strongest vacancy requirements as `V-### -> F-### -> caveat`.
- `three_proof_points`: at most three proof points, ordered by relevance and recency, each with candidate fact IDs.
- `screening_risks`: evidence gaps, each with a truthful bridge and a confirmation question.
- `candidate_asks`: process, range, eligibility, scope, timing, and decision questions; do not assert unavailable answers.
- `next_state`: one of `not_contacted`, `application_submitted`, `recruiter_contacted`, `screen_scheduled`, `screen_complete`, `waiting`, or `closed`, with evidence and date when supplied.
- `next_safe_action`: either evidence collection or a draft-only outreach/follow-up step; external action still needs exact action-and-target authorization immediately before execution.

`first_screen_prep_packet` is required after the conversion plan and before the recruiter screen brief. It is the private candidate prep sheet for the first recruiter conversation. Required fields are `source_packet_id`, `screen_objective`, `sixty_second_opener`, `story_menu`, `objection_responses`, `recruiter_questions`, `close_and_next_step`, `post_screen_follow_up_boundary`, `practice_drill`, `red_line_claims`, and `draft_only_gate`. The opener and story menu must cite `V-###` and `F-###` evidence, keep unsupported motivation or logistics as `unknown:`, and name what the candidate should ask rather than inventing employer process. `objection_responses` covers likely concerns such as production scope, unverified tools, compensation, eligibility, work authorization, notice period, bridge-candidate status, or missing proof. The packet must tell the coach to wait for candidate input before scoring, revising, or adding missing facts. It is private prep, not an outreach send, calendar confirmation, fit claim, or interview outcome promise.

`recruiter_screen_brief` records `candidate-reported:` opening pitch, why-now/why-this-role, scope, logistics, compensation handling, and location/work authorization/notice period confirmation when candidate-supported; retain each supporting fact ID or evidence label. Draft `inferred:` recruiter questions and safe close. Any missing candidate detail is `unknown:`; compensation handling asks for process or ranges without claiming an amount.

`recruiter_bridge_script` is the practical recruiter-screen answer scaffold. It must include `opening_claim`, `evidence_anchor`, `scope_caveat`, `risk_bridge`, `thirty_second_pitch`, `proof_sequence`, `objection_bridge_sequence`, `recruiter_qualification_questions`, `advance_the_process_ask`, `screen_success_criteria`, `stop_condition`, `candidate_question`, `next_step_ask`, `red_line_claims`, and `draft_only_gate`. Use it to turn transferable evidence into a bounded answer, not to strengthen unsupported gaps. It must cite `V-###` and `F-###`, state when a bridge is not a production ownership claim or equivalent unsupported claim, ask for permission to proceed rather than assuming process advancement, and require exact action-and-target authorization before outreach or follow-up.

## Practice answer coaching

`practice_answer_coaching` is the senior-coach layer between the fact-bounded story bank and the mock question. For recruiter screens, coach a 30–45 second truthful answer that covers motivation, scope, fit, and gaps without pretending unsupported experience. For hiring-manager interviews, coach a 60–90 second answer that covers ownership, decisions, tradeoffs, collaboration, and limits.

Required fields: `answer_arc`, `opening_sentence`, `proof_beats`, `gap_bridge`, `candidate_confirmation_needed`, `red_line_phrases`, `practice_drill`, and `coach_revision_prompt`. `answer_arc` is setup -> relevant proof -> boundary -> role-facing bridge -> question/close. `gap_bridge` must name the unsupported requirement plainly and bridge only from cited facts. `red_line_phrases` lists claims the candidate must not say because they are unsupported. `coach_revision_prompt` asks the candidate to answer the linked `Q-###` using only cited facts and waits before feedback or scoring.

`vacancy_candidate_gap_map` has one row for every `V-###`: must-have/preferred when supplied, classification (`strength`, `transferable`, `gap`, or `unknown`), recency, proof needed, likely objection, and truthful bridge language. A bridge may connect only cited candidate fact IDs and must not represent adjacent experience as the requirement.

`objection_response_map` has objection, supporting evidence, candidate clarification, safe response, and unsupported-claim refusal. When evidence is absent, the safe response is `unknown:` plus a confirmation question; refuse to supply a stronger claim.

## Stage-aware question bank and follow-up lifecycle

`question_bank` rows contain stage, `question ID=Q-###`, requirement/process/constraint ID, core question, follow-up probe, expected signal, and candidate fact IDs. Use a process or constraint ID only when supplied; otherwise label it `unknown:` and ask it as a candidate-led clarification.

`follow_up_lifecycle` includes recruiter-screen thank-you, hiring-manager follow-up, clarification note, and overdue-process check-in. Each draft names a recipient, event reference, timing state, and draft-only gate. It remains `do not send` until exact action-and-target authorization immediately before execution.

## Story bounds

A story must use `STAR=` or `CAR=`, list the candidate fact ID beside every supported Situation, Task, Action, or Result claim, and preserve explicit unknowns. A fact may support preparation language but never beyond its stated scope. When no fact fits or a STAR field is missing, write `unknown: (candidate example needed)` and ask the candidate for a fact; do not invent a metric, technology, customer, team, or outcome.

`practice_answer_coaching` turns a likely question into a safe answer practice plan. Include `answer_arc`, `opening_sentence`, `proof_beats`, `gap_bridge`, `candidate_confirmation_needed`, `red_line_phrases`, `practice_drill`, and `coach_revision_prompt`, all tied to the same question ID, vacancy requirement ID, and candidate fact IDs. Use it to rehearse structure and gaps; wait for the candidate before scoring, revising unsupported facts, or adding missing outcomes.
