# Measurement

Use outcome data to make better next decisions, not to overclaim causality.

## Funnel definitions

- `applications`: submitted applications with `application_date` inside the window.
- `responses`: in-window applications with a valid, non-empty `response_date` no later than `as_of`.
- `interviews`: in-window applications with a valid, non-empty `interview_date` no later than `as_of`.
- `offers`: in-window applications with a valid, non-empty `offer_date` no later than `as_of`.
- `response_rate`, `interview_rate`, `offer_rate`: outcome count divided by applications, returning `0` when applications are zero.
- `days_to_first_interview`: minimum days from application to interview in the window, or `null`.
- Window boundaries are inclusive: for `window_days=N`, include application dates from `as_of - (N - 1)` through `as_of`.
- The largest valid window is `as_of.toordinal()`: the inclusive days from `0001-01-01` through `as_of`. Reject any larger decimal integer before constructing a `timedelta`; it exits 2 with deterministic JSON and no traceback.

## Canonical row contract

The canonical header is:

```text
application_id,candidate_id,application_date,response_date,interview_date,interview_stage,offer_date,currency,role,geography,source,referral,asset_version,intervention_id,confounders,simultaneous_interventions,benchmark_consent
```

- `application_id` and `candidate_id` are mandatory on every nonempty row. `application_id` must be unique; any duplicate makes the file invalid instead of being silently merged or double-counted.
- Dates are empty or exact `YYYY-MM-DD`. Reject malformed dates, any date after `as_of`, outcome dates without an application date, and backward event chronology.
- Missing `application_date` with no outcome dates is ignored with a warning. Missing outcome dates mean the outcome was not observed.
- `simultaneous_interventions` and `benchmark_consent` accept only `true`, `false`, or empty. Empty is false.
- A missing required header or unreadable/missing file is invalid input. Invalid input exits 2 with one JSON error and no traceback.

## Experiment rules

One controlled change at a time is more interpretable, but never proves causality. Always log `intervention_id`, target `role`, `geography`, application `source`, `referral` status, `asset_version`, declared `confounders`, and `simultaneous_interventions`.

Warnings use only in-window rows for currency and intervention claims. Warn for missing application dates, samples under 10 applications, unknown interview stages, multiple in-window currencies, interventions, explicit confounders, simultaneous interventions, changed role mix, changed geography, changed application source, referral effects, asset-version changes, and benchmark use without consent.

Never perform FX conversion and never compare cross-currency offer values as equivalent. The CLI reports funnel counts and rates only; it makes no causal attribution.

## Explicit recruiter receipt export

`export_private_recruiter_outcome.py` is a manual adapter for the one mapping
that is semantically safe without a second artifact: a validated
`reply_received` receipt becomes a CSV `response_date`. The caller must provide
`candidate_id`, `application_id`, `application_date`, and `as_of`; optional
role, geography, currency, asset-version, referral, confounder, and consent
fields are copied only as bounded caller-supplied CSV values. The adapter uses
the canonical header and a deterministic
`recruiter-receipt-sha256-...` `intervention_id` derived from the receipt's
structural fields, source artifact ID, and application ID. Repeating the same
pair is a no-op. When `--force` is used after review, existing rows for
distinct applications are preserved and only the same application's row is
replaced.

The adapter rejects `contact_received`, `referral_received`,
`screen_requested`, `interview_requested`, and `stop_decision`; none of those
events proves a response or interview. Do not map a requested screen to
`interview_date`, and do not map a stop to `response_date`. Screen-attended
events remain in the follow-through/debrief artifacts until a separately
reviewed adapter with explicit confirmation exists. The bridge never copies
raw receipt prose or source IDs, combines candidates, changes the summarizer,
or performs an external action. Symlinked/non-regular output targets (including
a symlinked immediate parent) and spreadsheet formula prefixes in optional text
fields are rejected before write.

## LinkedIn outreach diagnostics

Use `source=linkedin_outreach` for rows driven by a LinkedIn outreach sequence, and store the LinkedIn `measurement_event` ID in `intervention_id` (for example `LI-FIRST-002`). `outreach_diagnostics` is a coaching interpretation layered over the deterministic JSON; it does not add or change CLI counts.

Each diagnostic row includes `measurement_event`, `outreach_source`, `sequence_step`, `bottleneck`, `next_experiment`, `stop_condition`, and `causality_boundary=descriptive_only_no_causal_claim`. When the corresponding LinkedIn `outreach_funnel` row is supplied, copy its `sequence_step`, `success_signal`, and stop condition. Without that row, set `sequence_step=unknown:` and ask for the matching outreach-funnel record. A response, recruiter screen, or interview after a LinkedIn outreach intervention remains descriptive only; never say the message, profile edit, or recruiter bridge caused it.

The coach recommendation should convert the narrowest observed bottleneck into one reversible next experiment. If LinkedIn outreach produces applications or contacts but no qualified response, reduce generic volume and improve recipient fit, personalization trigger, and proof asset before sending more. If responses appear but no recruiter screen follows, revise the recruiter bridge around a fact-checked 30-second summary, one qualification question, and one low-friction next-step ask. If recruiter screens appear but no interview follows, stop changing outreach copy and route the next cycle to interview practice. Stop the sequence after a decline, closed role, missing recipient context, unconfirmed candidate proof, withdrawn interest, or the predefined follow-up limit.

## Operating review

`operating_review` is the weekly coaching decision layer. It does not alter CLI counts and must not claim causal lift. Include one canonical row with `review_window`, `primary_bottleneck`, `decision`, `pause`, `repeat`, `fix`, `prepare`, `measure_next`, `evidence_required`, `authorization_gate`, and `causality_boundary=descriptive_only_no_causal_claim`.

The decision comes from the narrowest observed funnel bottleneck after data-quality and consent gates. With zero responses, pause generic application or outreach volume and route the proof/positioning gap to `optimize-professional-profile` before expanding volume. With responses but no recruiter screens, fix the recruiter conversation bridge: fact-checked 30-second summary, one qualification question, and one clear next-step ask. With recruiter screens or interviews but no offer, stop changing outreach copy and route the next cycle to `prepare-role-interviews`. With multiple candidates lacking unanimous consent, stop aggregate diagnosis and rerun isolated summaries only. Always name what to pause, what to repeat unchanged, what to fix, what to prepare, what evidence is still required, and what will be measured in the next window.

## Weekly strategy decision ladder

The `weekly_strategy_decision` layer converts the operating review into the coach's next-week strategy choice without changing the CLI counts. Include one `weekly_strategy_decision=coach_funnel_strategy_review` row with `candidate_id`, `review_window`, `source_summary`, `current_strategy`, `funnel_health`, `primary_bottleneck`, `decision`, `decision_rationale`, `next_experiment`, `metric_to_watch`, `evidence_required`, `confounders`, `privacy_boundary=single_candidate_only_no_benchmark_without_consent`, `authorization_gate=exact_action_and_target_required_before_external_action`, `causality_boundary=descriptive_only_no_causal_claim`, `draft_only=true`, and `no_external_action=true`.

Also include five `weekly_strategy_branch=next_cycle_decision_rule` rows for `continue`, `revise`, `pause`, `research`, and `stop`. Each branch must define the observed trigger, minimum evidence, next safe action, blocked action, metric to log, review gate, and the same privacy, authorization, causality, draft-only, and no-external-action boundaries. Use `continue` only when a clean, stable strategy has enough comparable observations. Use `revise` when one bottleneck is visible and the next experiment is reversible. Use `pause` when samples are too small, data quality is weak, or multiple changes confound the readout. Use `research` when the role, market, source, or target segment assumption is not evidenced enough to choose a funnel fix. Use `stop` when consent, safety, confidentiality, fit, or candidate-interest boundaries make the next action unsafe.

## Coach mode

Do not aggregate multiple candidates unless every in-window row has explicit consent recorded as `benchmark_consent=true`. Without unanimous consent, return the exact-field zero-count safety summary and a warning. Then run the same CLI once per candidate by appending `--candidate-id CANDIDATE_ID`, keep each ten-field JSON result in that candidate's private record, and report the results separately. Never add, average, compare, or otherwise combine those isolated rates. With unanimous consent, aggregation is allowed but must preserve anonymity and cannot imply guaranteed outcomes.

The bundled `summarize_outcomes.py` CLI rejects any nonempty row missing `candidate_id` or `application_id`. Multiple candidates without unanimous in-window consent receive a zero-count safety summary rather than combined rates. `--candidate-id` must name an existing candidate and scopes funnel counts plus data-quality, currency, intervention, and confounder warnings to that candidate while preserving the exact top-level summary fields.
