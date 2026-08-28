---
name: recommend-career-learning
description: Use when recommending courses, certifications, labs, portfolio projects, or no-learning-next actions for a target role based on evidenced skill gaps.
---

# Recommend Career Learning

Prioritize learning only when it is likely to create a stronger hiring signal than applying, rewriting assets, networking, or building proof from existing work. Read [learning-roi.md](references/learning-roi.md) before recommending paid or time-intensive learning. Read [evidence-projects.md](references/evidence-projects.md) when a project, lab, portfolio artifact, or work sample may prove the gap better than a course or certification.

## Evidence rules

Every material claim starts with exactly one canonical prefix: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. Optional qualifiers after the colon are allowed. Do not use slash compounds. Use stable IDs for target requirements, candidate facts, vacancy observations, and learning options.

Do not recommend certificate collecting. A learning option needs repeated vacancy evidence, not a single influencer post, generic “hot skill” claim, or vague career advice. For real current recommendations, browse current official primary provider sources and current matching employer vacancies when current source evidence was not supplied.

Record a separate official-source row for every provider option with these explicit fields: `provider`, `option`, `source_title`, `source_date`, `source_state`, official provider `url`, `geography`, `availability`, `role`, `seniority`, `current_cost`, `currency`, `tax`, `duration`, `prerequisite`, `renewal`, `maintenance`, and `unknowns`. Do not combine renewal and maintenance. For Mexico-facing advice, state whether Mexico eligibility or access is verified; an online or public page alone does not establish Mexico eligibility. Every unavailable or unstated value is `unknown:` rather than inferred from memory.

For structured runs, keep provider rows in the closed `learning-option-research-v1` artifact and validate it with `scripts/validate_learning_option_research.py` before any ROI composition. The artifact is identity-free, source-snapshot bound, synthetic-fixture safe, and always `no_external_action=true`; stale or unavailable sources remain blocked from current recommendations. Set its own `evidence_mode` to `synthetic` or `live`: synthetic mode requires every provider row to be synthetic, while live mode requires active provider rows and public current URLs. This provider mode is distinct from vacancy-market evidence.

The v2 recommendation gate treats an active provider source as fresh only when
`source_date` is within 90 calendar days of the dossier `as_of_date`, inclusive.
If the source is older, a paid option must remain `consider` with an explicit
provider-source refresh gate; it cannot be `recommended` until refreshed.

For market-linked runs, compose `career-market-learning-dossier-v2` only after
validating both the v1 market dossier and the exact learning-research snapshot.
Return three to five ranked decisions tied to recurring vacancy signals; use a
candidate-owned project or lab before paid learning when it can produce the
needed proof, and keep a paid option at `consider` when budget or current
provider evidence is unknown. Preserve the provider mode as
`learning_evidence_mode`; it must not be inferred from the market mode. The v2
builder selects one option per gap deterministically in this precedence order:
candidate-owned project, lab, free resource, course, certification, then
no-learning, with stable option ID as the tie-breaker. The v2 artifact is
draft-only, includes a fixed
five-day proof sprint when a project is selected, and never performs an external
action.

Map role and seniority to exact vacancy evidence, and label that context separately from provider-verified facts. Do not compress mixed target roles into one invented role. Preserve mixed stated and unspecified seniority, or use `unknown:` when the fixtures do not state seniority. Do not infer seniority from a bridge-role recommendation.

Current prices, exam fees, course costs, certification rules, provider duration, prerequisites, and availability must come from a current dated official source or official provider page, or be `unknown:`. Label provider option time as `provider-verified` or `provider duration unknown`. Label candidate work, preparation, or project time as `candidate-estimated`. Do not hard-code prices. Do not make stale price claims or invented outcomes.

## ROI decision

For each gap, separate:

- a real capability gap supported by repeated vacancies;
- a terminology mismatch or keyword mismatch where the candidate already has adjacent evidence;
- a knowledge gap where learning may be useful;
- a demonstrable-proof gap where a portfolio/project alternative, lab, or artifact is a better signal;
- a professional-experience gap, such as production Terraform, production Argo CD, production SLO, SaaS quota, or enterprise deal experience, where a certificate cannot honestly replace experience;
- a low-return gap where the best option is `do_nothing_now` or `do nothing now`.

Compare at least one learning option with a cheaper or faster proof alternative when the candidate can plausibly demonstrate the skill. Include opportunity cost: time away from applications, interview preparation, LinkedIn/networking, current work, or higher-signal projects. Add a `decision_basis` that names why the option is recommended, deferred, or rejected, using vacancy recurrence, official provider source quality, candidate-owned evidence, budget/time fit, and experience boundaries. Add a `next_action_gate` that states the exact authorization or review required before enrollment, purchase, exam scheduling, publication, sharing, or external messaging. Do not promise interviews, offers, salary increases, recruiter ranking, or ATS outcomes.

Before listing course or certification recommendations, include a short executive investment matrix using this contract: `learning_investment_decision=course_certification_roi_gate`. Use three to five ranked rows with these fields in order: `candidate_id`, `learning_investment_decision`, `decision_rank`, `target_role`, `gap_type`, `option_type`, `option_name`, `provider_or_owner`, `source_gap_ids`, `market_evidence_state`, `cost_time_band`, `expected_signal_boundary`, `portfolio_or_no_learning_alternative`, `overbuying_risk`, `decision`, `why_this_before_courses`, `next_action_gate`, `outcome_boundary`, `draft_only`, and `no_external_action`. Include at least one course or certification option and at least one cheaper proof, lab, role-search, or `no_learning_yet` alternative. The matrix is a coach decision gate, not a shopping list: it must rank what to do, defer, omit, or research first; name the overbuying risk; preserve exact action authorization; and keep `outcome_boundary=not_an_interview_offer_salary_or_roi_prediction`.

When a project, lab, work sample, or `do_nothing_now` beats a certification/course, include a short `#### Coach decision` block before the option rows. It must name exactly one `recommended_next_action`, `why_now`, `why_not_certificate_now` or provider-specific equivalent such as `why_not_capa_now`, `first_deliverable`, `acceptance_criteria`, and `next_action_gate`. The first deliverable must be inspectable, such as a repo, README, runbook, dashboard, rollback log, architecture diagram, account plan, or case writeup. Acceptance criteria must map to vacancy IDs and candidate fact IDs and include concrete proof checks. If a project beats a certificate, state that the certificate may corroborate knowledge but does not prove the requested artifact or professional experience. Do not publish or share without exact authorization.

## Required response

Return these exact fields for every option, in this order: gap, frequency_in_target_jobs, proof_needed, option, provider, current_cost, duration, prerequisite, opportunity_cost, decision_basis, next_action_gate, expected_signal, confidence. Start every `expected_signal` value with `bounded hypothesis`.

```text
gap
frequency_in_target_jobs
proof_needed
option
provider
current_cost
duration
prerequisite
opportunity_cost
decision_basis
next_action_gate
expected_signal
confidence
```

Include a `do_nothing_now` option when evidence is weak, cost/time is disproportionate, or the candidate already has stronger proof. If a course or certificate is recommended, explain why its expected signal beats a project, lab, direct application, or networking action.

## Safety and action gates

Drafting a plan is allowed. Confidence from a single source or one active vacancy must not exceed low confidence. Do not claim a certificate causes interviews, offers, salary increases, time-to-hire improvement, or hiring ROI. Use bounded hypothesis language. Never predict an interview. Never predict a job. Never predict an offer. Never predict salary. Never predict time-to-hire. Never predict ROI. An explicit refusal to predict is allowed, but do not follow the refusal with a percentage, hiring-speed range, weeks-sooner estimate, or other unsupported forecast. Do not enroll, purchase, schedule an exam, submit reimbursement, publish a portfolio artifact, message a provider, or share candidate work without exact action-and-target authorization immediately before execution. Portfolio or project recommendations still require candidate isolation, candidate-owned evidence project checks, ownership, documented rights-holder permission when applicable, public-disclosure permission, secrets review, customer data review, and confidentiality review.
