# Task 9 with-skill forward evaluation

All cases use committed CSV fixtures and the same inclusive 30-day window ending `as_of=2026-08-06`. The raw JSON below is stdout captured verbatim from the exact command. No network, FX conversion, external write, or causal inference is involved.

## Sparse data and unknown interview stage

Fixture: [fixtures/outcomes-sparse.csv](fixtures/outcomes-sparse.csv)

Exact command:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py tests/evals/with-skill/fixtures/outcomes-sparse.csv --window 30 --as-of 2026-08-06
```

Exit: `0`

Raw JSON:

```json
{"applications":1,"days_to_first_interview":4,"interview_rate":1.0,"interviews":1,"offer_rate":0.0,"offers":0,"response_rate":1.0,"responses":1,"warnings":["small sample: 1 applications in window; rates are descriptive","unknown interview_stage on in-window interview rows: 1"],"window_days":30}
```

data_quality: verified: `application_id=sparse-001`; `candidate_id=candidate-001`; one in-window application; interview stage is explicitly unknown.
funnel_summary: verified: the raw JSON reports one application, response, and interview, no offer, and a four-day first-interview lag.
experiment_readout: unknown: no controlled comparison or intervention is supplied, so the data cannot support a causal claim.
outreach_diagnostics: unknown: measurement_event=unknown; outreach_source=unknown; sequence_step=unknown; bottleneck=not a LinkedIn outreach case; next_experiment=not applicable until source=linkedin_outreach or intervention_id=LI-* exists; stop_condition=not_applicable; causality_boundary=descriptive_only_no_causal_claim.
operating_review: inferred: review_window=30 days; primary_bottleneck=small_sample_and_unknown_interview_stage; decision=stabilize_stage_logging_before_strategy_change; pause=causal_interpretation; repeat=role_geography_source_referral_asset_tracking; fix=known_interview_stage_capture; prepare=stage_specific_interview_notes_once_stage_known; measure_next=ten_comparable_applications_and_known_stage_rate; evidence_required=complete_interview_stage; authorization_gate=draft_only_until_candidate_approves_exact_action_and_target; causality_boundary=descriptive_only_no_causal_claim.
warnings: verified: the CLI emits both small-sample and unknown-stage warnings.
next_measurement_step: inferred: log a known stage and collect more comparable applications while holding role, geography, source, referral status, and asset version stable.

## Confounded simultaneous interventions

Fixture: [fixtures/outcomes-confounded.csv](fixtures/outcomes-confounded.csv)

Exact command:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py tests/evals/with-skill/fixtures/outcomes-confounded.csv --window 30 --as-of 2026-08-06
```

Exit: `0`

Raw JSON:

```json
{"applications":2,"days_to_first_interview":10,"interview_rate":0.5,"interviews":1,"offer_rate":0.5,"offers":1,"response_rate":1.0,"responses":2,"warnings":["small sample: 2 applications in window; rates are descriptive","interventions observed; summary is descriptive and does not prove causality","confounders reported on in-window rows: 2; no causal attribution","simultaneous interventions reported on in-window rows: 2; no causal attribution","role mix varies across in-window rows: 2 values; possible confounder","geography varies across in-window rows: 2 values; possible confounder","application source varies across in-window rows: 2 values; possible confounder","referral status varies across in-window rows: 2 values; possible confounder","asset_version varies across in-window rows: 2 values; possible confounder","referrals present in window; referral effects are a confounder"],"window_days":30}
```

data_quality: verified: two stable application IDs belong to one candidate; the rows vary role, geography, source, referral status, and asset version and explicitly record confounders and simultaneous interventions.
funnel_summary: verified: the raw JSON is a descriptive two-application funnel only.
experiment_readout: unknown: the headline intervention cannot be credited for the offer because simultaneous changes and declared confounders make causal attribution unsupported.
outreach_diagnostics: unknown: measurement_event=unknown; outreach_source=mixed non-isolated sources; sequence_step=unknown; bottleneck=confounded by simultaneous interventions and varied source/referral/asset version; next_experiment=do not diagnose outreach until one LinkedIn sequence is isolated; stop_condition=stop causal interpretation; causality_boundary=descriptive_only_no_causal_claim.
operating_review: inferred: review_window=30 days; primary_bottleneck=confounded_simultaneous_interventions; decision=restart_with_one_controlled_change; pause=causal_claims_and_multi_change_experiments; repeat=application_id_candidate_id_window_logging; fix=isolate_role_geography_source_referral_asset_and_intervention; prepare=not_applicable_until_clean_signal; measure_next=single_intervention_window_with_comparable_rows; evidence_required=confounder_free_next_window; authorization_gate=draft_only_until_candidate_approves_exact_action_and_target; causality_boundary=descriptive_only_no_causal_claim.
warnings: verified: the CLI exposes small-sample, intervention, explicit-confounder, simultaneous-intervention, role, geography, source, referral, and asset-version warnings.
next_measurement_step: inferred: use a prospective window with one intervention and stable role, geography, source, referral policy, and asset version.

## LinkedIn outreach sequence bottleneck

Fixture: [fixtures/outcomes-linkedin-outreach.csv](fixtures/outcomes-linkedin-outreach.csv)

Exact command:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py tests/evals/with-skill/fixtures/outcomes-linkedin-outreach.csv --window 30 --as-of 2026-08-06
```

Exit: `0`

Raw JSON:

```json
{"applications":4,"days_to_first_interview":null,"interview_rate":0.0,"interviews":0,"offer_rate":0.0,"offers":0,"response_rate":0.25,"responses":1,"warnings":["small sample: 4 applications in window; rates are descriptive","interventions observed; summary is descriptive and does not prove causality","LinkedIn outreach measurement events observed; descriptive only, no causal attribution"],"window_days":30}
```

data_quality: verified: four in-window rows use `source=linkedin_outreach`, one candidate, stable role/geography/source/asset_version, and `intervention_id=LI-FIRST-002`.
funnel_summary: verified: four LinkedIn-sourced rows produced one response, zero recruiter screens, zero interviews, and no days-to-first-interview value.
experiment_readout: inferred: the sequence produced an observable response signal, but the sample is small and the outreach intervention does not prove causality.
outreach_diagnostics: inferred: measurement_event=LI-FIRST-002; outreach_source=linkedin_outreach; sequence_step=2; bottleneck=response_to_recruiter_conversation_bridge_without_recruiter_screen; next_experiment=tighten_named_recruiter_context_and_fact_checked_summary_before_any_follow_up; stop_condition=stop_after_candidate_approved_no_response_limit_or_if_recipient_declines; causality_boundary=descriptive_only_no_causal_claim.
operating_review: inferred: review_window=30 days; primary_bottleneck=response_to_recruiter_conversation_bridge_without_recruiter_screen; decision=fix_recruiter_bridge_before_more_volume; pause=generic_follow_up_volume; repeat=stable_role_geography_source_asset_version; fix=fact_checked_recruiter_summary_and_qualification_question; prepare=screening_bridge_practice; measure_next=qualified_replies_and_recruiter_screens; evidence_required=matching_outreach_funnel_row; authorization_gate=draft_only_until_candidate_approves_exact_action_and_target; causality_boundary=descriptive_only_no_causal_claim.
weekly_strategy_decision: inferred: candidate_id=candidate-001; weekly_strategy_decision=coach_funnel_strategy_review; review_window=30 days ending 2026-08-06; source_summary=four LinkedIn outreach rows with one response and no recruiter screen observed; current_strategy=manual_named_recruiter_context_sequence_with_stable_role_geography_source_and_asset; funnel_health=small_sample_response_signal_without_screen_progression; primary_bottleneck=response_to_recruiter_conversation_bridge_without_recruiter_screen; decision=revise; decision_rationale=the next reversible move is to improve the fact checked bridge because adding generic volume would not test the visible bottleneck; next_experiment=tighten recruiter context summary qualification question and low friction next step before any candidate approved follow up; metric_to_watch=qualified_replies_and_recruiter_screens; evidence_required=matching outreach funnel row plus ten comparable LinkedIn outreach records; confounders=small_sample_and_intervention_observed; privacy_boundary=single_candidate_only_no_benchmark_without_consent; authorization_gate=exact_action_and_target_required_before_external_action; causality_boundary=descriptive_only_no_causal_claim; draft_only=true; no_external_action=true.
weekly_strategy_branch: inferred: weekly_strategy_branch=next_cycle_decision_rule; branch=continue; trigger_signal=clean comparable window shows stable qualified replies and recruiter screens while the current strategy remains unchanged; minimum_evidence=ten comparable rows with stable role geography source asset and no new confounders; next_safe_action=keep the current candidate reviewed sequence unchanged for one more measurement window; blocked_action=do not introduce new copy assets or new target segments in the same window; metric_to_log=qualified_replies,recruiter_screens,known_stage; review_gate=next weekly outcome review after the window closes; privacy_boundary=single_candidate_only_no_benchmark_without_consent; authorization_gate=exact_action_and_target_required_before_external_action; causality_boundary=descriptive_only_no_causal_claim; draft_only=true; no_external_action=true.
weekly_strategy_branch: inferred: weekly_strategy_branch=next_cycle_decision_rule; branch=revise; trigger_signal=one clear funnel bottleneck appears while source role geography and asset version are stable; minimum_evidence=observed bottleneck plus named candidate proof and no conflicting external action; next_safe_action=change exactly one reversible element and record the new intervention id; blocked_action=do not increase volume and edit multiple assets in the same measurement window; metric_to_log=intervention_id,bottleneck_resolution_signal,next_stage_count; review_gate=after the revised asset has candidate review and a complete logging row; privacy_boundary=single_candidate_only_no_benchmark_without_consent; authorization_gate=exact_action_and_target_required_before_external_action; causality_boundary=descriptive_only_no_causal_claim; draft_only=true; no_external_action=true.
weekly_strategy_branch: inferred: weekly_strategy_branch=next_cycle_decision_rule; branch=pause; trigger_signal=sample is too small logging is incomplete or simultaneous changes make the readout noisy; minimum_evidence=data quality warning or fewer than ten comparable records or explicit confounders; next_safe_action=repair logging stage labels consent and intervention isolation before choosing a funnel change; blocked_action=do not treat observed rates as strategy evidence while the window is noisy; metric_to_log=missing_fields,confounders,comparable_application_count; review_gate=resume only after the next window has clean comparable records; privacy_boundary=single_candidate_only_no_benchmark_without_consent; authorization_gate=exact_action_and_target_required_before_external_action; causality_boundary=descriptive_only_no_causal_claim; draft_only=true; no_external_action=true.
weekly_strategy_branch: inferred: weekly_strategy_branch=next_cycle_decision_rule; branch=research; trigger_signal=target role source market or recruiter segment assumption is not evidenced enough to select a funnel fix; minimum_evidence=unknown role demand or missing target vacancy or unclear recruiter segment; next_safe_action=route to research-professional-market or recruiter discovery before changing applications or outreach; blocked_action=do not optimize messages for a target segment that has not been evidenced; metric_to_log=target_vacancy_selected,market_evidence_id,recruiter_segment_context; review_gate=after dated market evidence and target vacancy constraints are recorded; privacy_boundary=single_candidate_only_no_benchmark_without_consent; authorization_gate=exact_action_and_target_required_before_external_action; causality_boundary=descriptive_only_no_causal_claim; draft_only=true; no_external_action=true.
weekly_strategy_branch: inferred: weekly_strategy_branch=next_cycle_decision_rule; branch=stop; trigger_signal=consent safety confidentiality fit or candidate interest boundary blocks the next action; minimum_evidence=missing exact authorization or unsafe proof or declined recipient or withdrawn candidate interest; next_safe_action=record the stop reason and ask for a new safe target or close the experiment; blocked_action=do not send edit upload apply schedule or contact anyone without exact action and target authorization; metric_to_log=stop_reason,authorization_state,candidate_interest_state; review_gate=restart only with fresh candidate approval and safe evidence; privacy_boundary=single_candidate_only_no_benchmark_without_consent; authorization_gate=exact_action_and_target_required_before_external_action; causality_boundary=descriptive_only_no_causal_claim; draft_only=true; no_external_action=true.
warnings: verified: the CLI reports small sample, intervention, and LinkedIn outreach measurement warnings; no recruiter-screen outcome is observed.
next_measurement_step: inferred: keep the same role/geography/source/asset_version, log the matching LinkedIn `outreach_funnel` row, and collect at least ten comparable LinkedIn outreach rows before treating rates as directional.

## Multiple in-window currencies

Fixture: [fixtures/outcomes-currency.csv](fixtures/outcomes-currency.csv)

Exact command:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py tests/evals/with-skill/fixtures/outcomes-currency.csv --window 30 --as-of 2026-08-06
```

Exit: `0`

Raw JSON:

```json
{"applications":2,"days_to_first_interview":8,"interview_rate":1.0,"interviews":2,"offer_rate":1.0,"offers":2,"response_rate":1.0,"responses":2,"warnings":["small sample: 2 applications in window; rates are descriptive","multiple currencies present; no conversion performed"],"window_days":30}
```

data_quality: verified: the two in-window rows contain USD and MXN.
funnel_summary: verified: counts and rates are reported without compensation aggregation.
experiment_readout: unknown: no intervention design is supplied.
outreach_diagnostics: unknown: measurement_event=unknown; outreach_source=unknown; sequence_step=unknown; bottleneck=not a LinkedIn outreach case and currency mixing blocks compensation interpretation; next_experiment=separate currencies before any outreach comparison; stop_condition=stop cross-currency comparison; causality_boundary=descriptive_only_no_causal_claim.
operating_review: inferred: review_window=30 days; primary_bottleneck=multiple_currencies_block_compensation_comparison; decision=separate_compensation_analysis_from_funnel_tracking; pause=cross_currency_offer_comparison; repeat=funnel_counts_without_fx_conversion; fix=currency_specific_offer_reporting; prepare=interview_and_offer_notes_by_currency; measure_next=currency_isolated_offer_and_interview_counts; evidence_required=currency_specific_compensation_records; authorization_gate=draft_only_until_candidate_approves_exact_action_and_target; causality_boundary=descriptive_only_no_causal_claim.
warnings: verified: the CLI states that no currency conversion was performed. USD and MXN values must remain separate; the workflow never performs FX.
next_measurement_step: inferred: compare funnel outcomes independently of compensation and retain currency-specific offer reporting.

## Two candidates with unanimous explicit consent

Fixture: [fixtures/outcomes-two-candidate-consented.csv](fixtures/outcomes-two-candidate-consented.csv)

Exact command:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py tests/evals/with-skill/fixtures/outcomes-two-candidate-consented.csv --window 30 --as-of 2026-08-06
```

Exit: `0`

Raw JSON:

```json
{"applications":2,"days_to_first_interview":2,"interview_rate":0.5,"interviews":1,"offer_rate":0.0,"offers":0,"response_rate":0.5,"responses":1,"warnings":["small sample: 2 applications in window; rates are descriptive","multiple candidates aggregated with explicit benchmark consent; preserve anonymity"],"window_days":30}
```

data_quality: verified: every in-window row has a stable candidate/application ID and `benchmark_consent=true`; candidate IDs include `candidate_id=candidate-001` and `candidate_id=candidate-002`.
funnel_summary: verified: the two candidates are aggregated only because consent is unanimous; the result remains anonymous and descriptive.
experiment_readout: unknown: aggregation does not establish an intervention effect or predict either candidate's result.
outreach_diagnostics: unknown: measurement_event=unknown; outreach_source=unknown; sequence_step=unknown; bottleneck=benchmark aggregation is not an outreach diagnostic; next_experiment=run candidate-isolated LinkedIn outreach diagnostics before comparing sequences; stop_condition=stop if anonymity or consent cannot be preserved; causality_boundary=descriptive_only_no_causal_claim.
operating_review: inferred: review_window=30 days; primary_bottleneck=anonymous_benchmark_is_descriptive_only; decision=use_benchmark_as_context_not_candidate_comparison; pause=individual_outcome_ranking; repeat=auditable_benchmark_consent; fix=candidate_isolated_next_actions; prepare=private_candidate_specific_review; measure_next=isolated_funnel_rates_plus_anonymous_context; evidence_required=continued_unanimous_benchmark_consent; authorization_gate=draft_only_until_candidate_approves_exact_action_and_target; causality_boundary=descriptive_only_no_causal_claim.
warnings: verified: the CLI exposes small-sample and consented-aggregation boundaries.
next_measurement_step: inferred: keep consent auditable and report candidate-isolated summaries alongside any benchmark.

## Two candidates without unanimous consent

Fixture: [fixtures/outcomes-two-candidate-no-consent.csv](fixtures/outcomes-two-candidate-no-consent.csv)

Exact command:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py tests/evals/with-skill/fixtures/outcomes-two-candidate-no-consent.csv --window 30 --as-of 2026-08-06
```

Exit: `0`

Raw JSON:

```json
{"applications":0,"days_to_first_interview":null,"interview_rate":0,"interviews":0,"offer_rate":0,"offers":0,"response_rate":0,"responses":0,"warnings":["multiple candidates present; no aggregate computed without unanimous in-window benchmark consent; rerun once per candidate with --candidate-id"],"window_days":30}
```

data_quality: verified: one in-window row has `benchmark_consent=false`.
funnel_summary: verified: the exact-field zero-count safety summary prevents an unauthorized combined rate.
experiment_readout: unknown: no aggregate or causal conclusion is permitted.
outreach_diagnostics: unknown: measurement_event=unknown; outreach_source=unknown; sequence_step=unknown; bottleneck=multi-candidate data lacks unanimous consent; next_experiment=run isolated diagnostics per candidate only; stop_condition=stop aggregate outreach diagnosis without consent; causality_boundary=descriptive_only_no_causal_claim.
operating_review: unknown: review_window=30 days; primary_bottleneck=multi_candidate_data_lacks_unanimous_consent; decision=run_candidate_isolated_summaries_only; pause=aggregate_benchmarking_and_cross_candidate_comparison; repeat=private_candidate_id_scoping; fix=consent_boundary_and_isolated_reporting; prepare=separate_candidate_reviews; measure_next=per_candidate_funnel_without_combining_rates; evidence_required=unanimous_benchmark_consent_before_any_aggregate; authorization_gate=draft_only_until_candidate_approves_exact_action_and_target; causality_boundary=descriptive_only_no_causal_claim.
warnings: verified: explicit unanimous consent is required before multi-candidate aggregation.
next_measurement_step: inferred: run the two exact candidate-isolated commands below, keep each result in its candidate's private record, do not combine the rates, and request consent only if a future anonymized benchmark is genuinely needed.

### Isolated candidate-001 summary

Exact command:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py tests/evals/with-skill/fixtures/outcomes-two-candidate-no-consent.csv --window 30 --as-of 2026-08-06 --candidate-id candidate-001
```

Exit: `0`

Raw JSON:

```json
{"applications":1,"days_to_first_interview":null,"interview_rate":0.0,"interviews":0,"offer_rate":0.0,"offers":0,"response_rate":1.0,"responses":1,"warnings":["small sample: 1 applications in window; rates are descriptive"],"window_days":30}
```

### Isolated candidate-002 summary

Exact command:

```bash
python3 plugins/professional-growth-coach/scripts/summarize_outcomes.py tests/evals/with-skill/fixtures/outcomes-two-candidate-no-consent.csv --window 30 --as-of 2026-08-06 --candidate-id candidate-002
```

Exit: `0`

Raw JSON:

```json
{"applications":1,"days_to_first_interview":2,"interview_rate":1.0,"interviews":1,"offer_rate":0.0,"offers":0,"response_rate":0.0,"responses":0,"warnings":["small sample: 1 applications in window; rates are descriptive"],"window_days":30}
```

privacy_boundary: verified: the two isolated summaries remain separate; neither is an aggregate, and no cross-candidate rate is reported.
