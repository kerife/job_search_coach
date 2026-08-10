# Path scoring

Use each score as an explained comparison, not as a claim of current market fact. Every material statement begins with `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`; optional qualifiers after the colon identify status such as `(dated source)` or `(missing)`. A score may be qualitative (`low`, `medium`, `high`) only when its basis and evidence confidence are stated.

## Required dimensions

- `compensation`: Compare only dated, comparable market briefs with `source_date`, `source_state`, `compensation_observation`, `employer_or_publisher`, `source_id`, `independent_observation_id`, `comparability_check`, `range_method`, `conversion_basis`, seniority, geography, currency, compensation basis, employment arrangement, sample context, source hierarchy, and confidence. A current range requires multiple active compatible observations with distinct source and observation identifiers plus a disclosed range method. Prefer a primary-source vacancy or employer source, then transparent government or salary-study evidence. If a brief is absent or incomparable, use `unknown:` and low confidence; do not rank a path highest-paying from a single anecdote.
- `demand`: Use dated active demand signals and recurring requirements in comparable market briefs. A stale, expired, unavailable, or single vacancy is low-confidence context, not a demand ranking. Provider-specific requirements remain source-specific unless repeated across active compatible sources.
- `transferability`: Map candidate evidence to the proposed role's evidenced requirements. Distinguish adjacent experience from missing production scope, domain expertise, language, eligibility, or seniority evidence. An unrealistic transition is `unknown:` or a low-transferability scenario, not an aspirational recommendation.
- `gap_cost`: List only evidence-backed missing requirements and the uncertainty of learning, time, and cost to address them. Explain the transition burden; do not prescribe generic certificates without recurring market requirements and a candidate-specific rationale.
- `geography_fit`: Keep Mexico employee, Mexico-based international contractor/EOR, US work-authorized employee, and remote geography/eligibility as distinct scenarios. Check work authorization, employer-of-record or contractor availability, tax/contract eligibility, language, and time zone. Do not compare their compensation as interchangeable.
- `evidence_confidence`: Assess recency, source quality, comparability, candidate-evidence completeness, and conflicts. A current-market compensation or demand score cannot exceed low confidence until dated, comparable market briefs exist.

## Decision rules

1. Start with the candidate's evidence and label any missing outcomes, English, work authorization, desired arrangement, geography, current compensation, and target compensation `unknown:`.
2. Generate only realistic adjacent paths. Identify the concrete candidate evidence that supports each transition and the requirement evidence that challenges it.
3. If salary, demand, or a ranking affects the choice, request `research-target-job-market` with roles and distinct geography/employment scenarios. Do not independently assert current salary, demand, or a highest-paying ranking.
4. Reject a single anecdote as proof of compensation, demand, or the highest-paying path. Do not infer a current range or time to offer from it.
5. Provide a conditional/scenario-based recommendation when market or candidate evidence is incomplete. Do not promise a better offer, a guaranteed pay increase, interview volume, or offer timing.

## Comparable market-brief minimum

Each brief must name role, seniority, geography, currency, compensation basis, employment arrangement, `source_date`, sample context, source hierarchy (with primary-source preference), `employer_or_publisher`, `source_id`, `independent_observation_id`, `comparability_check`, `range_method`, `conversion_basis`, range or unavailable value, demand signals, recurring requirements, eligibility constraints, and confidence. Flag unmatched currency, seniority, geography, basis, source independence, conversion basis, or employment arrangement as not comparable rather than normalizing it silently.
