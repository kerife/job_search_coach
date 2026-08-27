---
name: prepare-role-interviews
description: Use when preparing for a stated interview stage using a supplied vacancy, candidate fact matrix, and company evidence.
---

# Prepare Role Interviews

Create focused, truthful practice from the exact vacancy, company evidence, candidate fact matrix, and interview stage. Read [interview-map.md](references/interview-map.md), [evaluation-rubrics.md](references/evaluation-rubrics.md), and [mock-interview-scorecard.md](assets/mock-interview-scorecard.md) before responding.

## Evidence and boundaries

Every material item begins with exactly one canonical prefix: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. Optional qualifiers after the colon are allowed, such as `verified: (vacancy)` or `unknown: (not supplied)`. Do not use slash compounds. Label each vacancy requirement with a stable vacancy requirement ID and each question with a question ID. A question must give its requirement ID and rationale; do not use generic questions unless the supplied vacancy supports their purpose.

Treat supplied company evidence as evidence, not process knowledge. Record `source_date` and `source_state` for company evidence. A synthetic item must say `synthetic`; it is not current company evidence. Do not invent a company process, interviewer, exercise, timeline, culture, technology, or decision criterion. If evidence is absent or conflicting, use explicit unknowns.

Use only supplied candidate facts. Every story and answer claim must cite its candidate fact ID. Do not invent candidate stories, metrics, technology, scope, outcomes, seniority, or experience. When a needed example is unsupported, mark it `unknown:` and provide a confirmation placeholder rather than a script to claim it. Do not send any message, schedule anything, submit an application, or take another external action.

Explicitly refuse requests to fill or strengthen unsupported gaps, make the candidate sound fully qualified, or convert adjacent evidence into vacancy experience. Do not produce a numeric readiness score, hiring prediction, or weighted total from an unobserved response. Do not describe even a “typical” company process when company-specific evidence is unavailable; state that the process is `unknown:` and prepare a question that asks about it.

## Stage-specific preparation

First identify the single stated stage. Prepare only the relevant stage and return a complete stage applicability list: mark that stage `requested`, and mark each of recruiter screen, hiring-manager, technical screen, technical deep dive, take-home, system design, behavioral loop, panel, and offer-stage `not applicable because <reason>` when it is not requested. For a recruiter screen, focus on truthful motivation, scope, logistics, and questions about the process. For a hiring-manager interview, focus on requirement ownership, priorities, tradeoffs, and collaboration. For a technical screen or technical deep dive, use only vacancy-relevant technical practice. For a take-home, prepare only the stated exercise constraints and factual explanation; do not complete or submit it. For system design, practice assumptions, constraints, reliability, and tradeoffs without claiming experience not in facts. For a behavioral loop, map stories to competencies. For a panel, map each supported question to the stated panel evidence; otherwise keep panel composition and process `unknown:`. For offer-stage questions, prepare decision and clarification questions, not compensation claims or acceptance promises.

Use technical, system, or design practice only when relevant to the vacancy and stage. A high-compensation nontechnical vacancy does not imply a technical deep dive or system design; mark those stages not applicable unless the supplied process evidence supports them.

## Private recruiter-practice session

An explicit private recruiter-practice request with an identity-free vacancy summary and at least one supplied candidate fact selects the separate private recruiter practice session. It is a narrow recruiter-screen rehearsal, not the full interview-preparation response and not a LinkedIn dossier. If either input is missing, ask one concise question for the missing identity-free vacancy summary or candidate fact; do not start a session from assumptions.

When a validated executive-career dossier supplies candidate evidence and
context, keep the vacancy requirement as a separate identity-free source. The
dossier-to-practice handoff binds only the selected dossier question and its
evidence to the practice projection; it must never invent, infer, or copy a
vacancy requirement from the dossier. The handoff is draft-only and requires
manual re-entry: it never starts a practice session automatically.

The session is one-question/one-answer: ask one grounded recruiter-screen question, wait for the observed answer, and keep score unknown before an observed answer. In `feedback_available`, keep `score=unknown` and use only the categorical observation labels (`solid`, `confirm`, or `do_not_assert`) via `score_state=categorical`; never emit a numeric score. Feedback uses only the answer and rubric. Treat the answer as ephemeral and no-save-by-default; do not reuse it unless the candidate explicitly supplies it again. Return only the private summary and local artifact link; omit IDs and raw vacancy/fact text. No external action.

In feedback_available, visible feedback uses fixed bilingual guidance selected
only by the validated question kind and supplied categorical label. The most
cautious present label governs one separate next-private-rehearsal decision:
do_not_assert > confirm > solid. This is evidence-bounded coaching, not semantic
verification, readiness scoring, or an interview-outcome claim; the raw answer
and feedback statement remain omitted from the artifact. The static private
rail marks its final state `pending` for `solid` or `blocked` for
`confirm`/`do_not_assert`; it never auto-starts preparation or performs
external action.

An explicit private recruiter-reply triage request is not a practice request: it first produces the separate closed private decision card from an identity-free recruiter-reply summary and one supplied candidate fact. If either input is missing, ask exactly one concise intake question; do not infer it from raw content, a profile, or a recruiter message. Its local handoff can identify whether private preparation is available, but it does not start a practice session automatically. Do not expose raw reply content, internal identifiers, a draft/send action, proposed time, or calendar detail. When ready, the handoff is only a manual re-entry cue for one recruiter-screen question using the identity-free summary plus verified fact; clarify-first and stop states omit it.

The ready re-entry receipt is **manual input only** to a later, explicit `prepare-role-interviews` request. It does not auto-start preparation, does not create a `module_execution_packet`, and does not emit router rows. It carries no candidate answer: `candidate_answer_state=unanswered` and `score_state=unknown` until the candidate supplies a response in that later session. Never treat the receipt as an execution packet or as permission to reuse a prior answer.

An explicit follow-through checkpoint is also manual input only. Validate its linked conversion receipt before using it, and process the same receipt/checkpoint pair idempotently: replay must not create a duplicate route, CSV row, packet, answer, score, or outcome claim. Only a `completed` `screen_requested` or `interview_requested` checkpoint may expose a manual cue to prepare the stated stage; the candidate must explicitly request preparation again and supply the vacancy and fact inputs required below. `declined` checkpoints, and every checkpoint sourced from `stop_decision`, block preparation and record the stop instead. `accepted` and `deferred` do not authorize preparation. Never infer a stage, answer, identity, or readiness from a checkpoint.

## Required response

Return these exact sections:

```text
competency_map
likely_questions
vacancy_question_traceability_matrix
truthful_story_bank
practice_answer_coaching
role_practice
mock_interview
scorecard
interviewer_questions
follow_up_draft
first_interview_conversion_plan
first_screen_prep_packet
recruiter_screen_brief
recruiter_bridge_script
vacancy_candidate_gap_map
objection_response_map
vacancy_requirement_drill_matrix
question_bank
answer_revision_ladder
follow_up_lifecycle
```

In `competency_map`, map each competency to a vacancy requirement ID, evidence status, and stage, and record any refusal to fill unsupported gaps. In `likely_questions`, include `question ID`, `vacancy requirement ID`, stage, rationale, answer-fact IDs, and the actual `question_text="..."`. Immediately after `likely_questions`, include `vacancy_question_traceability_matrix`: one row for every `Q-###` with `question ID`, `vacancy requirement ID`, `candidate fact IDs`, `vacancy_signal`, `candidate_evidence_state`, `gap_or_risk`, `expected_recruiter_signal`, `practice_acceptance_test`, and `generic_advice_boundary=not_generic`. This matrix is the anti-generic coaching proof: it must show why the question exists for this exact vacancy, what candidate facts can and cannot answer it, what recruiter signal the answer should produce, and how the candidate will know the answer stayed truthful. In `truthful_story_bank`, provide an actual fact-bounded `STAR=` or `CAR=` outline whose every material claim cites a candidate fact ID; use `unknown: (candidate example needed)` placeholders for unsupported Situation, Task, Action, or Result fields. `practice_answer_coaching` must include the same question and vacancy requirement IDs, an `answer_arc`, `opening_sentence`, `proof_beats`, `gap_bridge`, `candidate_confirmation_needed`, `red_line_phrases`, `practice_drill`, and `coach_revision_prompt`; it must cite candidate fact IDs and wait for candidate input where claims are missing. `role_practice` must contain the complete stage applicability list with a reason for every non-requested stage. `mock_interview` must include the same question and requirement IDs plus the actual `mock_question="..."`, ask exactly one question, and wait for the candidate response before feedback.

For a recruiter screen, `first_interview_conversion_plan` must appear before `first_screen_prep_packet`, and `first_screen_prep_packet` must appear before `recruiter_screen_brief`. The conversion plan is a candidate-facing plan to obtain a recruiter screen, never a promise to secure an interview. Include `conversion_goal`, `role_fit_thesis`, `three_proof_points`, `screening_risks`, `candidate_asks`, `next_state`, and `next_safe_action`, all tied to `V-###` and `F-###` evidence where available. Keep it draft-only and include the exact action-and-target authorization gate for any outreach or follow-up.

`first_screen_prep_packet` is the practical private prep sheet for the candidate's first recruiter conversation. Include `source_packet_id`, `screen_objective`, `sixty_second_opener`, `story_menu`, `objection_responses`, `recruiter_questions`, `close_and_next_step`, `post_screen_follow_up_boundary`, `practice_drill`, `red_line_claims`, and `draft_only_gate`. Cite `V-###` and `F-###` evidence; use `unknown:` where motivation, logistics, compensation, location, work authorization, notice period, or proof details are not supplied. The packet must tell the coach to wait for candidate input before scoring, revising, or adding missing facts. It is not an outreach send, a calendar confirmation, a fit claim, or an outcome promise.

For recruiter screens, include exactly five `interview_risk_control_sheet=recruiter_screen_red_line_control` rows before `role_practice`. Cover `risk_theme=production_scope`, `compensation`, `work_authorization`, `availability`, and `confidentiality`. Required fields are `risk_theme`, `trigger_question`, `safe_answer_boundary`, `evidence_to_use`, `evidence_to_avoid`, `candidate_confirmation_needed`, `recovery_phrase`, `practice_drill`, `red_line_guardrail`, and `draft_only=true`. This is the candidate's “do not overclaim under pressure” sheet: cite `V-###`, `F-###`, or explicit `unknown` evidence; give a safe recovery phrase; and never claim production ownership, salary expectations, work authorization, availability, or confidential proof unless supplied facts support it.

`recruiter_screen_brief` must contain: opening pitch, why-now/why-this-role, scope, logistics, compensation handling, location/work authorization/notice period confirmation, recruiter questions, and a safe close. Each material line uses a canonical evidence prefix; compensation handling is a candidate clarification or `unknown:`, never a compensation claim. `recruiter_bridge_script` converts the brief into a recruiter-safe spoken/written answer: include `opening_claim`, `evidence_anchor`, `scope_caveat`, `risk_bridge`, `thirty_second_pitch`, `proof_sequence`, `objection_bridge_sequence`, `recruiter_qualification_questions`, `advance_the_process_ask`, `screen_success_criteria`, `stop_condition`, `candidate_question`, `next_step_ask`, `red_line_claims`, and `draft_only_gate`. It must include `V-###` and `F-###` evidence, state when a bridge is not a production ownership claim or equivalent unsupported claim, ask for permission to proceed rather than assuming process advancement, and require exact action-and-target authorization before outreach. `vacancy_candidate_gap_map` must map every `V-###`, including must-have/preferred when supplied, to `strength`, `transferable`, `gap`, or `unknown`, plus recency, proof needed, likely objection, and truthful bridge language. `objection_response_map` must give the objection, evidence, candidate clarification, safe response, and an unsupported-claim refusal. `vacancy_requirement_drill_matrix` must include at least three recruiter-screen rows that map `requirement_id=V-###` to `question_id=Q-###`, `fact_ids=`, `practice_task=`, `likely_objection=`, `unsupported_claim_refusal=`, `red_line_guardrail=`, `stage=recruiter screen`, and `draft_only=true`; each drill must be a practice task that can be executed privately, not generic advice, an outcome promise, or a send action. `question_bank` must give stage, question ID, requirement/process/constraint ID, core question, follow-up probe, expected signal, and fact IDs. `answer_revision_ladder` is the post-answer coaching protocol: include rows for `step=observe`, `step=diagnose`, `step=revise`, and `step=repeat`. Each row must cite the relevant `Q-###`, `V-###`, and `F-###`/gap IDs; state `input_needed`, `coach_action`, `candidate_action`, `evidence_rule`, `red_line_guardrail`, `score_gate`, and `next_drill`. It must wait for the candidate's actual answer before scoring, preserve `unknown:` for missing facts, and never make the answer sound stronger than the evidence.

Use the weighted scorecard from the asset: show criterion, weight, observed evidence, score 0–4 or `unknown:`, and weighted total only after responses. Feedback must cite the question ID and observable rubric criterion. `interviewer_questions` must include an actual `question_text="..."` tied to an uncertainty, requirement, or dated company evidence, not invented company process. The `follow_up_draft` (follow-up draft) must contain a non-empty `subject="..."` and `body="..."`; every candidate claim in the body cites its candidate fact ID. It is a draft only, must state `do not send`, and needs exact action-and-target authorization immediately before any external follow-up. `follow_up_lifecycle` must separately provide recruiter-screen thank-you, hiring-manager follow-up, clarification note, and overdue-process check-in; each entry requires recipient, event reference, timing state, and a draft-only gate. Do not draft a send action without exact action-and-target authorization immediately before execution.
