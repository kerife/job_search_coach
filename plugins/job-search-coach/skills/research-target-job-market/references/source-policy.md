# Source policy

## Source hierarchy

1. Current, direct employer vacancy pages: use for role title, seniority, geography, employment context, compensation disclosures, and observed requirements.
2. Government sources: use only for dated occupational context, with the occupation, geography, sample definition, and mismatch to the requested role disclosed.
3. Transparent salary studies: use only where the publisher states date, geography, currency, compensation basis, sample, and methodology. Mark them secondary.

Job-board reposts, snippets, crowdsourced salary pages, and undated articles are discovery leads rather than a sufficient basis for compensation or demand conclusions. A direct employer page is still only an observation, not a market-wide conclusion.

## Source state and observation record

Every cited source must have one `source_state` at its crawl date:

- `active`: direct source is reachable and shows a role-matched, open vacancy;
- `stale`: source remains reachable but its date is too old for the stated decision context;
- `expired`: employer source says the vacancy is closed or no longer accepting applications;
- `unavailable`: direct cited source cannot be verified, including an HTTP 404 or inaccessible official feed.

Record `as_of_date`, `source_age_days`, `freshness_window_days`, and `freshness_status` for every compensation observation. Default `freshness_window_days=90` for vacancy compensation unless the request defines another decision window. A compensation observation is current only when `source_state=active`, its publication or crawl date is recorded, and `source_age_days` is within the freshness window. If age cannot be computed, set `freshness_status=unknown`; it cannot contribute to a current range.

For every source, record `compensation_observation` as its raw source-specific amount and basis, or `unknown`. Also record `employer_or_publisher`, `source_id`, `independent_observation_id`, `comparability_check`, `range_method`, and `conversion_basis`. A stale, expired, or unavailable observation may be retained only as explicitly historical context. It cannot support a current range, demand, or recurrence.

## Comparability checklist

Before presenting a compensation range, confirm that the included observations match or are explicitly normalized for:

- role and seniority;
- geography and actual eligibility;
- currency;
- compensation basis (for example, annual base versus total compensation or hourly contractor rate);
- compensation components (base, bonus, commission, OTE, equity, benefits, hourly rate, and disclosed/missing split);
- employment arrangement (Mexico employee, Mexico-based international contractor/EOR, US work-authorized employee, or a specified remote international arrangement);
- source_date, source_state, source_age_days, freshness_status, and sample_context;
- a source-specific compensation_observation.
- source independence through distinct `source_id` and `independent_observation_id`;
- the disclosed `range_method`, or `not_applicable` when no range can be established;
- `conversion_basis=none` unless a dated conversion source and limits are supplied.

Assign each observation a `comparable_group_id`, `comparability_status`, and `comparability_check` so downstream path discovery can see which observations could be combined. Only multiple active, fresh, compatible observations in the same group with distinct sources and independent observations may produce a current market range. A shared `comparable_group_id` is necessary but not sufficient proof. If any item differs or is unknown, do not combine the observations. State `range=unknown`, retain each source in its own context, and add a `warning` saying the data are not comparable. One source cannot establish a range. Sources without a publication date need a crawl date and `unknown:` publication date. Stale, expired, and unavailable sources cannot support a current range, demand, or recurrence.

Keep provider-specific requirements source-specific unless the exact requirement repeats across active compatible sources. For example, AWS/EKS from one active source must not become a recurring requirement with Azure/AKS from a different or unavailable source.

## Confidence

`high` requires multiple current, direct, matching sources with disclosed bases and compatible context. `medium` requires some matching current evidence with stated limitations. `low` is required for one source, an indirect source, missing date/sample/basis, or unresolved eligibility/comparability. `unknown` is appropriate where no evidence exists.
