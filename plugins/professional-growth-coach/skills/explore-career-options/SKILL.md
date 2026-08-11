---
name: explore-career-options
description: Use when comparing evidence-backed, realistic career transitions or deciding what market evidence is needed before a high-compensation career-path recommendation.
---

# Explore Career Options

Preserve current employment by default (`preserve_current_employment_by_default`). A path decision is a research and positioning decision, never a separation instruction; staying and growing is valid and `no_resignation_recommendation=true`.

Compare plausible next-role paths from one candidate's evidence. This module does not independently research or assert current salary, demand, or highest-paying rankings.

## Evidence and scope

Every material item begins with exactly one canonical prefix: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. Optional qualifiers after the colon are allowed, for example `verified: (dated source)`. Do not use slash compounds, and do not promote a prompt or CV fact above `candidate-reported:` without an inspectable source.

Keep the candidate's geography, work authorization, language, current compensation, target compensation, employment type, and transition constraints separate. Missing English level, eligibility, outcome metrics, or requirements evidence is `unknown:`. Compare only transitions supported by the candidate's documented scope, skills, outcomes, and environment boundaries; do not infer production ownership from tool names or recommend an unrealistic seniority or domain jump.

Read [path-scoring.md](references/path-scoring.md) before scoring or recommending paths.

## Market-evidence gate

Do not independently assert current salary, demand, or rankings. If current-market evidence is needed, emit this concrete request and select the indicated follow-up:

```text
evidence_request: research-professional-market: provide dated, comparable market briefs for each proposed role and geography, including source_date, source_state, compensation_observation, primary-source or source hierarchy, seniority, currency, compensation basis, sample context, recurring requirements, demand signals, eligibility, and confidence.
```

Only comparable market briefs may support `compensation` or `demand`. They must be dated, comparable market briefs for the same or clearly normalized seniority, geography, currency, compensation basis, and employment arrangement, with multiple active compatible observations for a current range or recurrence. Stale, expired, or unavailable sources are historical context only and cannot support a current market score. Without them, those scores must not exceed low confidence and a final recommendation must be conditional/scenario-based; do not make a current-market final decision without a market brief. A single anecdote cannot establish a highest-paying role, a compensation range, or market demand. Do not call any role `highest-paying` from a single anecdote.

Separate, rather than blend, Mexico employee pay, Mexico-based international contractor/EOR pay, US work-authorized employee pay, and remote geography/eligibility. US-remote is not proof of US work authorization, employer-of-record availability, contractor eligibility, tax eligibility, time-zone fit, or English fit.

## Compare paths

When the candidate asks for the highest-paying, best-paid, fastest better-paid, or top-compensation path, add one `highest_pay_claim_audit=block_highest_paying_rank_until_comparable_market_evidence` row per candidate before `high_value_role_opportunity_matrix`. Required fields are `candidate_id`, `user_request`, `pay_rank_decision=block`, `market_evidence_state`, `required_comparable_briefs`, `blocked_claims`, `allowed_claim`, `geography_arrangement_boundary`, `single_anecdote_policy`, `next_research_action`, `no_salary_claim=true`, and `draft_only=true`. Use this as the explicit refusal-to-rank gate: block highest-paying rankings, current ranges, demand rankings, offer timing, fastest-better-offer claims, and cross-scenario pay comparisons until multiple active, fresh, compatible market briefs exist for each role/seniority/geography/currency/basis/component/arrangement. `allowed_claim` may only be conditional or scenario-based and must route the next step to `research-professional-market`. Single anecdotes never establish compensation, demand, ranking, or realistic transition.

Before `path_comparison`, add exactly four `high_value_role_opportunity_matrix` rows. This is the coach's bounded high-compensation opportunity surface: it compares realistic adjacent paths without claiming current pay, demand, or highest-paying rank. Required fields are `candidate_id`, `high_value_role_opportunity_matrix=role_opportunity_gate`, `path`, `target_seniority`, `candidate_evidence_fit`, `transferable_assets`, `missing_evidence`, `market_evidence_status`, `compensation_boundary`, `demand_boundary`, `geography_or_arrangement_scenarios`, `learning_or_certification_gate`, `portfolio_or_proof_asset`, `research_request`, `decision=prioritize|research|defer|reject`, `no_salary_claim=true`, and `draft_only=true`. Include at least one `prioritize`, one `research`, one `defer`, and one `reject` decision across the four rows. For technical infrastructure candidates, realistic rows may include Senior Platform Engineer/Kubernetes Infrastructure Engineer, Senior DevOps Engineer, OpenShift Platform Engineer/Consultant, and Staff/Principal SRE or AI infrastructure bridge only when candidate evidence supports the transition. `compensation_boundary` must state that pay/range is unknown until `research-professional-market` returns dated comparable market briefs. `learning_or_certification_gate` must name specific evidence or learning only when it addresses a real gap; do not prescribe generic certifications as a shortcut to higher pay. `research_request` must name the exact role and separate geography/employment scenarios to research next.

Immediately after the opportunity matrix and before `path_comparison`, add exactly four `market_research_execution_plan=role_geography_evidence_collection_plan` rows. This is the operational handoff to `research-professional-market`, not a salary claim. Required fields are `candidate_id`, `plan_rank=1..4`, `target_path`, `research_module=research-professional-market`, `role_queries`, `geography_arrangement_scope`, `source_priority`, `minimum_observations`, `comparability_rules`, `eligibility_questions`, `output_required`, `decision_after_research`, `blocked_until_complete`, `no_salary_claim=true`, and `draft_only=true`. Cover the highest-leverage researched paths across the evaluated candidates, keeping Mexico employee, Mexico EOR/contractor, US work-authorized employee, and international remote scenarios separate. `source_priority` must start with direct employer vacancy pages and may use official labor data or transparent salary studies as context. `minimum_observations` must require multiple active compatible independent observations before any current range or demand conclusion. `blocked_until_complete` must block salary ranges, pay ranks, demand comparisons, and offer-speed claims until comparable market briefs exist.

For each realistic path, use the six dimensions: `compensation`, `demand`, `transferability`, `gap_cost`, `geography_fit`, and `evidence_confidence`. State score bases and uncertainty rather than manufacturing precision. `transferability` comes from evidence-backed adjacent responsibilities and demonstrated outcomes. `gap_cost` is limited to evidenced missing requirements, learning/time/cost uncertainty, and the transferability gap; it is not generic certificate shopping.

Return this form, with a label on every material claim:

```text
Candidate: <candidate_id>
Evidence
- verified: <inspectable candidate or dated market evidence>
- candidate-reported: <candidate-supplied fact>
- inferred: <transition conclusion; basis and uncertainty>
- unknown: <missing/conflicting candidate or market evidence>

path_comparison
- inferred: path=<path>; compensation=<score and confidence>; demand=<score and confidence>; transferability=<score and confidence>; gap_cost=<score and confidence>; geography_fit=<score and confidence>; evidence_confidence=<overall confidence>

evidence_request
- unknown: <concrete market request or why none is needed>
recommendation
- inferred: <conditional/scenario-based path, rationale, and candidate evidence gaps>
```

Do not predict time to offer, interview volume, or offer timing. Do not promise hiring, guaranteed pay increases, compensation, or demand outcomes. When evidence is insufficient, recommend the next safe evidence-gathering action rather than a false ranking.
