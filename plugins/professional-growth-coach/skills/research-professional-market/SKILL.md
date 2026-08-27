---
name: research-professional-market
description: Use when collecting current, dated job-market evidence for a target role or comparing market evidence across distinct employment geographies.
---

# Research Professional Market

Collect dated market evidence for a supplied role, skill, or comparison list. This skill produces research inputs for `explore-career-options`; it must not choose the candidate's career path, recommend resignation, and does not recommend or rank career paths. Preserve current employment by default (`preserve_current_employment_by_default`); `no_resignation_recommendation=true`.

## Evidence and research rules

Market demand and compensation are time-sensitive: browse current sources for every request. Every material item begins with exactly one canonical prefix: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. Optional qualifiers after the colon are allowed, for example `verified: (employer vacancy)`. Do not use slash compounds.

Read [source-policy.md](references/source-policy.md) before researching. Read [market-brief.md](references/market-brief.md) before returning a brief.

## Default five-vacancy research

When this skill supports a normal local profile dossier, run the default
five-vacancy research before returning market conclusions. Search SRE, Platform
Engineering, and DevOps families in Mexico or stated remote scope. Target at
most five active postings, with five distinct employers searched first; do not
pad the result with stale, duplicate, unrelated, or hypothetical postings.

For each employer, inspect official employer and employer-operated ATS sources
first. LinkedIn Jobs backup only is permitted when an active posting is
inspectable and the direct source is unavailable or does not expose the needed
role detail. A search-result snippet is discovery only, never evidence. Each
included posting needs active verification and access date, a public HTTPS
source, its observed eligibility gates, and a dated role-matched requirement
paraphrase. Keep raw vacancy text, cookies, session data, candidate identity,
and private browser data out of the artifact.

Return the closed `target-vacancy-research-v1` artifact with
`maximum_vacancies=5`, official-sources-first provenance, and
`no_external_action=true`. A complete result contains five active postings.
Use limited `1..4` when the bounded search returns some valid evidence and
state the exact limitation; use unavailable `0` when it returns none. Do not
manufacture an employer, a vacancy, a skill requirement, or a recurrence rate.
Report every recurring signal against the actual sample `k/N`, not a presumed
five-posting denominator. Keep `learning_state=not_evaluated` until a later
learning-decision increment consumes the validated market dossier.

Set `evidence_mode=live` for current research and `evidence_mode=synthetic`
only for clearly marked reproducible fixtures. Live artifacts reject reserved
example/test domains and any future `as_of_date`, source, access, or
publication date. Observational prose is identity-free: URLs, contact details,
and session-shaped identifiers are rejected before rendering, with bounded
diagnostics that do not echo their values. Synthetic mode does not upgrade
fixture evidence into a current-market claim. The field is required by the
v1 artifact contract, so existing producers must migrate before validation.

When composing `career-market-learning-dossier-v1` or derived v2, propagate
the validated mode unchanged. Older v1 artifacts without `evidence_mode` must
be rebuilt from their source research because their snapshot binding changes.

Learning-provider research has a separate `evidence_mode` in
`learning-option-research-v1`; propagate it as `learning_evidence_mode` in v2.
Do not let a live vacancy market upgrade synthetic provider rows into current
availability, price, or certification evidence.

Do not infer work-authorization, internal-mobility, EOR, or remote-eligibility
from a role title, employer, country, remote label, or source location. This is
read-only research: no apply, message, connect, follow, publish, enroll, or
purchase action. Browser session access does not broaden that boundary.

Start with current employer vacancy pages for the supplied role. Use government sources and transparent salary studies only as secondary context. Record each source URL, `as_of_date`, `source_date`, `source_age_days`, `freshness_window_days`, `freshness_status`, and `source_state`: `active`, `stale`, `expired`, or `unavailable`. `active` means the direct source was reachable and role-matched at the stated crawl date; `stale` means the observation is old for this decision; `expired` means the employer identifies the vacancy as closed; `unavailable` means the cited direct source cannot be verified (for example, HTTP 404). Record publication date when visible, otherwise crawl date and an explicit `unknown:` publication date. Do not treat a search-result timestamp as a publication date. Use `freshness_window_days=90` by default for vacancy compensation unless the request defines a stricter or broader decision window.

When composing a market dossier, carry `access_date` and `publication_date`
onto every vacancy card. The builder derives a bounded 90-day freshness
decision and reason; a missing publication date is rendered as
`unknown:`/“publication date: unknown” and can never become `current`. The
rendered public-source link keeps the vacancy title in its accessible name so
the evidence can be audited without exposing raw posting text or internal IDs.

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
