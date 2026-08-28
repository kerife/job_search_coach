# Learning ROI

Use learning recommendations as an investment decision, not a shopping list. Do not recommend certificate collecting.

## Required evidence

- `gap`: the missing requirement, mapped to repeated vacancy evidence or a bounded hypothesis.
- `frequency_in_target_jobs`: count or qualitative recurrence across comparable target vacancies, with source IDs and `source_date`. Prefer multiple supplied or current matching vacancies.
- `proof_needed`: what the employer must believe after seeing the evidence.
- `option`: course, certification, lab, portfolio project, interview drill, or `do_nothing_now`.
- `provider`: official exam owner, official provider, course provider, project owner, or `none`.
- `current_cost`: dated official/provider cost with currency and tax treatment, or `unknown:` when not verified current.
- `duration`: `provider-verified` or `provider duration unknown` for a provider option; `candidate-estimated` for candidate work, preparation, or projects.
- `prerequisite`: required experience, exam prerequisite, account access, hardware, language, or `unknown:`.
- `opportunity_cost`: what the candidate gives up by spending time/money here.
- `decision_basis`: why this option is recommended, deferred, or rejected based on repeated vacancy evidence, official provider source quality, candidate-owned evidence, budget/time fit, and experience boundaries.
- `next_action_gate`: the authorization or review required before enrollment, purchase, exam scheduling, publication, sharing, or external messaging; use `no external action` for draft-only or do-nothing options.
- `expected_signal`: a `bounded hypothesis` explaining why this option might improve role evidence, or why it would not.
- `confidence`: high, medium, low, or unknown, based on source quality and repeatability.

## Decision rules

Recommend paid learning only when repeated comparable vacancies show the gap, current dated official source or official provider source data is available, and the candidate lacks a cheaper credible proof path. A single source, stale provider page, blog ranking, or unverified market claim cannot justify a purchase.

For the structured v2 artifact, a provider source is fresh only when its
`source_date` is no more than 90 calendar days before the dossier
`as_of_date` (the 90-day boundary is inclusive). An `active` source outside
that window cannot support `recommended`; keep the option at `consider` and
make the next gate an explicit provider-source refresh before enrollment.

Prefer `do_nothing_now` when the requirement is rare, unsupported by current target evidence, already covered by candidate facts, or lower leverage than applications, LinkedIn repositioning, interview preparation, or a portfolio project.

When the comparison yields a clear priority, especially when a project beats a certification, add a `Coach decision` block before the option rows. It contains one `recommended_next_action`, `why_now`, `why_not_*_now`, `first_deliverable`, `acceptance_criteria`, and `next_action_gate`. The decision must convert the comparison into the next job-search move, not a shopping list. The deliverable must be inspectable, and acceptance criteria must map to vacancy IDs and candidate fact IDs.

Before the investment matrix for high-compensation or transition recommendations, add one to three `learning_target_role_alignment=high_value_role_gap_alignment` rows. This is the executive bridge from “what should I learn?” to “which higher-value role evidence am I trying to strengthen?” Required fields are `candidate_id`, `source_investment_decision_ranks`, `target_role_family`, `compensation_evidence_state`, `role_requirement_recurrence`, `candidate_evidence_fit`, `highest_value_gap`, `learning_or_proof_priority`, `why_this_role_before_generic_learning`, `evidence_to_build`, `do_not_buy_yet`, `review_trigger`, `outcome_boundary=not_an_interview_offer_salary_or_roi_prediction`, `draft_only=true`, and `no_external_action=true`. Use `compensation_evidence_state=not_claimed` or `unknown:` unless current comparable compensation evidence was actually gathered. The row must cite vacancy IDs or supplied recurrence, candidate fact IDs or candidate evidence state, and the overbuying risk that prevents generic certificate shopping. It must choose whether the next move is a project, lab, portfolio proof, course, certification, role search, or no-learning action, and explain why that role family comes before generic learning.

When `recommended_next_action=candidate-owned evidence project`, add one `learning_proof_sprint_plan=project_to_hiring_signal_execution_plan` row and exactly five `learning_proof_sprint_day=day_checkpoint` rows before the option comparison. The plan row must include `candidate_id`, `source_decision`, `sprint_goal`, `target_gap`, `deliverable`, `vacancy_ids`, `candidate_fact_ids`, `review_model=daily_private_review_then_final_candidate_review`, `publication_gate=exact_action_and_target_authorization_after_ownership_secrets_confidentiality_and_public_disclosure_review`, `outcome_boundary=not_an_interview_offer_salary_or_roi_prediction`, `draft_only=true`, and `no_external_action=true`. Day rows must cover `day_number=1..5` and include `daily_goal`, `artifact_piece`, `proof_check`, `risk_check`, `acceptance_test`, `candidate_timebox`, `owner=candidate|candidate_with_coach_review`, `measurement_signal`, `next_safe_action`, `draft_only=true`, and `no_external_action=true`. Use the sprint to make the project immediately executable and reviewable without publishing, sharing, enrolling, paying, messaging, or claiming hiring ROI.

After the proof sprint, add exactly three `learning_evidence_reuse_map=proof_artifact_to_job_search_asset` rows for `target_asset=linkedin`, `target_asset=application_packet`, and `target_asset=interview`. Each row must map concrete sprint artifacts to one downstream job-search asset without taking external action. Required fields are `candidate_id`, `source_sprint_artifacts`, `reuse_goal`, `safe_claim`, `proof_boundary`, `required_review`, `blocked_claims`, `handoff_module`, `acceptance_test`, `authorization_gate=exact_action_and_target_authorization_before_publication_sharing_upload_or_message`, `outcome_boundary=not_an_interview_offer_salary_or_roi_prediction`, `draft_only=true`, and `no_external_action=true`. Use `handoff_module=optimize-professional-profile` for LinkedIn, `handoff_module=optimize-career-assets` for the application packet, and `handoff_module=prepare-role-interviews` for the interview. The map must state what can be reused privately, what must stay out of public copy, and what review is required before publication, upload, sharing, or messaging.

Every provider option needs `decision_basis` containing `official provider source`. Every candidate-owned artifact option needs `decision_basis` containing `candidate-owned evidence`. Every provider option needs `next_action_gate` containing `purchase or enrollment requires exact authorization`. Draft-only, bridge-role, and no-action options use a `next_action_gate` that starts with `no external action`.

For every provider option, treat the official-source row as a purchase/enrollment risk register, not just a citation. It must keep `current_cost`, `currency`, `tax`, `duration`, `prerequisite`, `renewal`, `maintenance`, `geography`, `availability`, and `unknowns` separate before any recommendation can mention paying, enrolling, registering, creating an account, scheduling an exam, or submitting reimbursement. Do not merge `renewal` and `maintenance`. Do not overclaim Mexico eligibility unless the official source explicitly verifies it; otherwise state `geography=unknown:`. If the provider source is stale, expired, unavailable, or missing a material field, the option can only be a bounded draft recommendation with the missing evidence named and a fresh-source review required before action.

Never promise a job, interview, offer, salary increase, ATS score, recruiter boost, exam pass, or payback date. never predict an interview. never predict a job. never predict an offer. never predict salary. never predict time-to-hire. never predict ROI. A refusal to predict is valid; a numeric or time forecast after that refusal is not. Use scenario language and confidence labels.

## Source states

- `active`: current page or official source accessible at evaluation time.
- `stale`: dated source is old or source age is unclear.
- `unavailable`: source cannot be accessed.
- `synthetic`: test fixture only, not current public evidence.

The provider artifact also declares `evidence_mode=synthetic|live`. Synthetic
rows remain fixture-only even when paired with a live vacancy market; v2 keeps
this distinction in `learning_evidence_mode` and shows the boundary to the
client.

If current cost, duration, prerequisites, or certification rules are unavailable, write `unknown:` and do not fill the gap from memory.

## Official source capture

For real recommendations, browse current official primary provider sources. Capture one row per provider option with these exact explicit fields:

`provider, option, source_title, source_date, source_state, official provider url, geography, availability, role, seniority, current_cost, currency, tax, duration, prerequisite, renewal, maintenance, unknowns`

Keep `renewal` and `maintenance` separate. For geography, state whether Mexico access or eligibility is verified; public or online delivery does not by itself prove eligibility. Write `unknown:` for every unavailable or unstated value. Do not hard-code prices. no stale price claims. no invented outcomes.
