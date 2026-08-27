---
name: track-career-outcomes
description: Use when measuring job-search applications, responses, interviews, offers, funnel rates, experiments, or intervention outcomes.
---

# Track Career Outcomes

Measure job-search outcomes descriptively without claiming causality from uncontrolled changes. A descriptive funnel summary does not prove causality. Read [measurement.md](references/measurement.md) before summarizing experiments or comparing candidates. Use [outcomes.csv](assets/outcomes.csv) as the canonical CSV shape and `../../scripts/summarize_outcomes.py` for deterministic, validated summaries.

## Private recruiter-conversion observation receipt

The conversion receipt is a candidate-supplied observation only: one dated event in one declared source namespace, with no candidate identity claim and no aggregation. Map events exactly: `contact_received` and `reply_received` → `clarify_context_before_reply`; `referral_received` → `prepare_fact_checked_summary`; `screen_requested` and `interview_requested` → `route_to_prepare-role-interviews`; `stop_decision` → `record_stop_decision`. This is descriptive measurement, with no causality, fit, score, offer, or outcome proof. It preserves the normal CSV and `summarize_outcomes.py` route unchanged. The only next step is a manual next step for the candidate; it has no auto-start, no module packet, no send, no schedule, and no calendar item, and does not retain raw event prose.

### Follow-through checkpoint (candidate-supplied, manual)

When a separately supplied `private-recruiter-conversion-outcome-v1` receipt is followed by a `private-recruiter-followthrough-checkpoint-v1`, validate the receipt first and require exact source fields and event/action identity. The checkpoint is replay-safe: reprocessing the same receipt and checkpoint is idempotent; reprocessing the same receipt/checkpoint pair idempotently must not append a second event, change the CSV, aggregate candidates, or advance a route. Use the validator's pure `replay_fingerprint(checkpoint, receipt)` helper as the no-persistence replay key before any local event handling; equal keys are the same pair, while a changed receipt or checkpoint must be handled as a new pair. The key contains only validated structural fields and never raw event prose or candidate identity. A completed `screen_requested` or `interview_requested` observation may offer only a manual, explicit handoff to `prepare-role-interviews`; a completed `screen_attended` observation offers only the manual `debrief_after_screen` cue to re-enter a private conversation; this artifact does not capture or persist debrief notes. These cues do not start preparation, transfer an execution packet, send, or schedule follow-up. `accepted` and `deferred` remain manual checkpoints, while `declined` and any `stop_decision` source block interview preparation and route only to recording the stop. Unknown or non-completed measurement events stay unknown. The ordinary CSV measurement path and ordinary recruiter-reply routes remain unchanged when this explicit pair of private artifacts is absent. No auto-start, send, schedule, calendar action, score, causality, outcome guarantee, or candidate aggregation is allowed.

The rendered receipt and checkpoint make that continuity legible with a static
three-stage rail for non-terminal routes: recorded source, bounded route, and
manual action. A `record_stop_decision` route is terminal and uses one recorded
stage instead of a continuation rail. States are textual as well as visual and
remain safe in narrow, print, forced-color, and high-contrast modes. This is a
reading aid only; it does not change the checkpoint contract or authorize the
next module.

## Required boundaries

Every interpretation uses `verified:`, `candidate-reported:`, `inferred:`, or `unknown:` labels. Every nonempty CSV row requires stable, unique `application_id` and stable `candidate_id` values. Reject a duplicate `application_id`; do not silently double-count or merge it. Keep candidates isolated by `candidate_id`. Coach-mode aggregation or anonymized benchmarking is allowed only when every in-window row has explicit consent recorded as `benchmark_consent=true`. Without unanimous consent, return the zero-count safety summary, then run the CLI once per candidate with `--candidate-id CANDIDATE_ID` and report those summaries separately; never combine their rates.

Do not claim a headline, CV rewrite, LinkedIn post, course, recruiter message, LinkedIn outreach sequence, or other intervention caused a response, interview, offer, or compensation change. Even a controlled design supports a bounded experiment readout, not proof of causality. Mark unknown interview stages, simultaneous interventions, explicit confounders, seasonality, role mix, geography, source, referral changes, asset-version changes, market changes, and samples under 10 in-window applications as warnings.

Never perform FX conversion. If multiple currencies appear inside the selected window, warn and keep them separate. Never compare offer values across currencies as if equivalent, even if a dated exchange rate is supplied to the narrative.

The window includes both `as_of - (window_days - 1)` and `as_of`. A positive window cannot exceed the inclusive number of calendar days from `0001-01-01` through `as_of`; reject larger integers before date arithmetic with exit 2 and deterministic JSON. Validate all supplied dates before summarizing: reject malformed or future dates and reject event chronology that moves backward. Missing `application_date` rows are ignored with a warning. `response_date`, `interview_date`, and `offer_date` count only for applications whose `application_date` is inside the window.

## Required response

Return these sections:

```text
data_quality
funnel_summary
experiment_readout
outreach_diagnostics
operating_review
warnings
next_measurement_step
```

For deterministic counts, run:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py OUTCOMES.csv --window 30 --as-of YYYY-MM-DD
```

For a file containing multiple candidates without unanimous in-window benchmark consent, the aggregate command returns the zero-count safety summary. Produce isolated outputs with one command per candidate:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py OUTCOMES.csv --window 30 --as-of YYYY-MM-DD --candidate-id CANDIDATE_ID
```

Keep each command's result under that candidate's private record. Do not add, average, compare, or otherwise combine the isolated rates without unanimous consent.

Report the JSON fields exactly: `window_days`, `applications`, `responses`, `interviews`, `offers`, `response_rate`, `interview_rate`, `offer_rate`, `days_to_first_interview`, and `warnings`.

When `source=linkedin_outreach` or `intervention_id` starts with a LinkedIn `measurement_event` such as `LI-`, include `outreach_diagnostics`. Use the existing CSV fields only: map `measurement_event` from `intervention_id`, identify `outreach_source`, record the supplied or `unknown:` `sequence_step`, name the observed `bottleneck`, propose one `next_experiment`, state the `stop_condition`, and set `causality_boundary=descriptive_only_no_causal_claim`. If the linked LinkedIn `outreach_funnel` is supplied, use its `sequence_step`, `draft_type`, `success_signal`, and stop condition; otherwise keep those fields `unknown:` and ask for the matching outreach-funnel row. Choose the next experiment from observed bottlenecks: no qualified replies means improve recipient/context quality before more volume; replies without screens means tighten the fact-checked recruiter bridge and qualification question; screens without interviews means route to `prepare-role-interviews`.

Always include `operating_review` as the professional coaching decision layer over the deterministic summary. It is one semicolon-delimited row with `review_window`, `primary_bottleneck`, `decision`, `pause`, `repeat`, `fix`, `prepare`, `measure_next`, `evidence_required`, `authorization_gate`, and `causality_boundary=descriptive_only_no_causal_claim`. Use `verified:` for direct CLI/window facts, `inferred:` for the coach decision, and `unknown:` when evidence is missing. Pick one reversible next-cycle decision: no responses means pause generic volume and route proof/profile gaps to `optimize-professional-profile`; responses without recruiter screens means fix the fact-checked recruiter bridge before more volume; recruiter screens or interviews without offers means route to `prepare-role-interviews`; multi-candidate data without unanimous consent means stop aggregate diagnosis and run isolated summaries only. The `authorization_gate` must remain draft-only until the candidate approves the exact action and target.

For coach-mode weekly review, add a separate `weekly_strategy_decision` layer after `operating_review`. Include one `weekly_strategy_decision=coach_funnel_strategy_review` row with `candidate_id`, `review_window`, `source_summary`, `current_strategy`, `funnel_health`, `primary_bottleneck`, `decision`, `decision_rationale`, `next_experiment`, `metric_to_watch`, `evidence_required`, `confounders`, `privacy_boundary=single_candidate_only_no_benchmark_without_consent`, `authorization_gate=exact_action_and_target_required_before_external_action`, `causality_boundary=descriptive_only_no_causal_claim`, `draft_only=true`, and `no_external_action=true`. Then include five `weekly_strategy_branch=next_cycle_decision_rule` rows for `branch=continue`, `branch=revise`, `branch=pause`, `branch=research`, and `branch=stop`. Each branch states `trigger_signal`, `minimum_evidence`, `next_safe_action`, `blocked_action`, `metric_to_log`, `review_gate`, and the same privacy, authorization, causality, draft-only, and no-external-action boundaries. This decision ladder makes the next week auditable: continue only when the current experiment has enough clean signal, revise when a single bottleneck is visible, pause when evidence quality is poor, research when market/role assumptions are unknown, and stop when consent, safety, or interest boundaries fail.

Valid input exits `0` and writes only that JSON object to stdout. Invalid CLI or CSV input exits `2`, writes a deterministic `{"error":"..."}` object to stderr, writes nothing to stdout, and never exposes a traceback. The CSV reader rejects symlinked/non-regular inputs, invalid UTF-8, and files larger than 256 KiB before parsing; input paths and candidate identifiers are not echoed in those diagnostics.
