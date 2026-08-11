---
name: research-professional-market
description: Use when collecting current, dated job-market evidence for a target role or comparing market evidence across distinct employment geographies.
---

# Research Professional Market

Collect dated market evidence for a supplied role, skill, or comparison list. This skill produces research inputs for `explore-career-options`; it must not choose the candidate's career path, recommend resignation, and does not recommend or rank career paths. Preserve current employment by default (`preserve_current_employment_by_default`); `no_resignation_recommendation=true`.

## Evidence and research rules

Market demand and compensation are time-sensitive: browse current sources for every request. Every material item begins with exactly one canonical prefix: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. Optional qualifiers after the colon are allowed, for example `verified: (employer vacancy)`. Do not use slash compounds.

Read [source-policy.md](references/source-policy.md) before researching. Read [market-brief.md](references/market-brief.md) before returning a brief.

Start with current employer vacancy pages for the supplied role. Use government sources and transparent salary studies only as secondary context. Record each source URL, `as_of_date`, `source_date`, `source_age_days`, `freshness_window_days`, `freshness_status`, and `source_state`: `active`, `stale`, `expired`, or `unavailable`. `active` means the direct source was reachable and role-matched at the stated crawl date; `stale` means the observation is old for this decision; `expired` means the employer identifies the vacancy as closed; `unavailable` means the cited direct source cannot be verified (for example, HTTP 404). Record publication date when visible, otherwise crawl date and an explicit `unknown:` publication date. Do not treat a search-result timestamp as a publication date. Use `freshness_window_days=90` by default for vacancy compensation unless the request defines a stricter or broader decision window.

For every source, record a `compensation_observation`: the source-specific raw amount and basis, or `unknown`. Also record `compensation_components`, `component_gaps`, `employer_or_publisher`, `source_id`, `independent_observation_id`, `comparable_group_id`, `comparability_status`, `comparability_check`, `range_method`, `conversion_basis`, geography, currency, compensation basis, seniority, employment arrangement, and sample context. Keep Mexico employee, Mexico-based international contractor/EOR, US work-authorized employee, and remote international arrangements separate. Remote is not a geography or proof of work authorization, contractor/EOR availability, tax eligibility, or benefit eligibility.

Never derive a current range from one source. A current market range is reproducible only from multiple active compatible observations: at least two active compatible observations that are also fresh, each with an inspectable `compensation_observation`, distinct `source_id`, distinct `independent_observation_id`, compatible `compensation_components`, the same `comparable_group_id`, and a disclosed multi-source `range_method`. Never treat `comparable_group_id` alone as proof of comparability. Never merge values with incompatible currency, compensation basis, seniority, geography, employment arrangement, eligibility, or compensation components such as annual base, total compensation, equity, bonus, OTE, commission, hourly rate, or benefits. A stale, expired, or unavailable observation may remain as historical context but cannot support a current range, demand, or recurrence. When evidence is missing, not active, stale, from a single source, or otherwise not comparable, return `range=unknown`, set `range_method=not_applicable`, reduce confidence, and add a warning that names the incompatibility. Set `conversion_basis=none` unless the request provides a dated conversion basis and its limitations are disclosed; do not convert currencies merely to make figures appear comparable.

Demand signals are only dated active observations, such as current, role-matched vacancies or an official dated labor-market series. They are not claims of broad demand, interview volume, hiring speed, or likelihood of offer. Recurring requirements require more than one active, role-matched vacancy; otherwise report the observed requirement as provider-specific with low confidence rather than calling it recurring. Do not collapse AWS/EKS evidence with Azure/AKS evidence, or any other provider-specific requirement, unless that exact requirement repeats across active compatible sources.

## Output

Return one labeled brief per requested role and employment geography. Include exactly these fields:

```text
market_brief
- verified: role=<role>; geography=<market and eligibility/arrangement>; currency=<currency or unknown>; compensation basis=<base/total/hourly/unknown>; seniority=<level>; as_of_date=<YYYY-MM-DD>; source_date=<publication or crawl date>; source_age_days=<integer or unknown>; freshness_window_days=<integer>; freshness_status=<current/stale/unknown>; source_state=<active/stale/expired/unavailable>; compensation_observation=<raw source amount and basis, historical amount, or unknown>; compensation_components=<base/bonus/equity/OTE/commission/hourly/benefits disclosed or unknown>; component_gaps=<missing components>; employer_or_publisher=<employer or publisher>; source_id=<stable source identifier>; independent_observation_id=<stable observation identifier>; comparable_group_id=<stable group for compatible observations>; comparability_status=<compatible_multi_observation/compatible_single_observation/incompatible_arrangement_and_components/incompatible_ote_and_sales_motion/not_comparable>; comparability_check=<plain-language compatibility decision>; range_method=<multi-source method or not_applicable>; conversion_basis=<none or dated conversion source and date>; sample_context=<source count, source type, and employment context>; range=<only multiple active fresh compatible independent observations, otherwise unknown>; demand_signals=<active dated observations only>; recurring_requirements=<requirements repeated across active matching sources, otherwise unknown>; confidence=<high/medium/low>; source URL=<URL>
- unknown: warning=<why evidence is missing, stale, single-source, or not comparable>
```

If no comparable compensation evidence exists, leave `range=unknown`; preserve each source as context rather than manufacturing a cross-market range. Return the brief to `explore-career-options`, which may combine it with candidate evidence and make only its own conditional path analysis.
