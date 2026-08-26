---
name: optimize-professional-profile
description: Use when auditing a professional profile, reconciling profile and CV facts, drafting truthful positioning, or planning evidence-led growth conversations without external action.
---

# Optimize LinkedIn Career

Audit and draft; authorized read-only inspection is allowed, and LinkedIn actions may execute only under the shared authorization rule. Keep each candidate's facts isolated and minimize personal data.

When a recruiter-conversion receipt is supplied, treat it as a candidate-supplied observation only. Preserve its exact event-to-action mapping (`contact_received`/`reply_received` → `clarify_context_before_reply`; `referral_received` → `prepare_fact_checked_summary`; `screen_requested`/`interview_requested` → `route_to_prepare-role-interviews`; `stop_decision` → `record_stop_decision`). It carries no candidate identity claim, aggregation, causality (no causality), score, fit, or outcome proof. Offer only a manual next step: no auto-start, no module packet, no send, no schedule, and no calendar item. Ordinary LinkedIn and recruiter-reply routes remain unchanged when this explicit receipt is absent.

## Client-first delivery

Read [client-report.md](references/client-report.md) for every audit so the validated Markdown compatibility path stays available. Read [html-dossier.md](references/html-dossier.md) for every normal audit. Select exactly one branch:

- `normal + local execution -> executive dossier artifact branch`: when at least one authorized live or supplied section is inspectable, build and validate `executive-career-dossier-v2`, run `validate_executive_career_dossier_v2.py` and `render_executive_career_dossier_v2.py`, then return the receipt summary exactly once plus one absolute local file link. In this branch: (1) account for all 17 sections; (2) render available findings immediately; (3) record unavailable sections and their current-session request states; (4) ask only the first pending authorization question in chat; (5) on an explicit positive answer, inspect only that named section immediately without writing `authorized_for_session` or any session identifier; (6) never infer authorization, analytics consent, raw retention, or an external action; and (7) after the inspection attempt, regenerate a new collision-safe v2 artifact. no authorization carries forward, a positive answer is consumed immediately and never stored in the artifact, analytics needs separate explicit consent, and no inspection authorization permits an external action. Normal + local execution with at least one other supplied or inspectable section remains HTML even when the requested technology is unsupported: hold only that claim as unknown, omit it from copy and place it in do-not-change, and ask at most the rank-1 confirmation question. This artifact branch overrides broader conflict or blocking prose unless the unresolved claim makes the entire honest diagnostic impossible. When supported sections already permit an honest partial dossier, never substitute a standalone refusal or intake response: place the refusal or hold inside confirmation-or-omit and do-not-change, finish the HTML artifact, and keep at most the rank-1 question in chat. Fabricated analytics pressure never changes a normal + local supported case to refusal or Markdown: set analytics to `not_requested` or `unavailable`, omit requested numeric, company, and conversion values from dossier and chat, do not echo them even in a refusal, finish the artifact, and the receipt remains the complete client answer. Keep the complete response at most 180 words and preserve `action_state=not_executed` as an internal boundary, never client-visible contract text. v1 remains an accepted compatibility artifact for debug/eval fixtures.
- `normal + no local execution -> localized Markdown fallback`: use the complete compact report from `client-report.md`; do not claim that an artifact exists.
- `debug | eval | detail_requested -> existing Markdown + canonical appendix`: use the validated expanded path from `client-report.md` unchanged.

Follow [html-dossier.md](references/html-dossier.md) for the five-vacancy
handoff; preserve the profile on limited/unavailable evidence; remain read-only.

A second validation or render failure also uses the localized Markdown fallback after private cleanup. A normal request remains normal even when it asks to skip presentation or return raw/debug/internal rows. When there is no inspectable or supplied evidence, ask exactly one useful intake question rather than generating an empty report. With partial evidence, render available findings now and exclude unavailable sections instead of scoring them as zero. In coach mode, create one isolated temporary input and one generic artifact per candidate, never a combined dossier.

The artifact branch supersedes the root router and legacy normal rows. Do not append an evidence index, `Routing receipt`, `Live source summary`, canonical row, later-module handoff, duplicate question, or duplicate no-action sentence after the artifact link. A `linkedin_rendered_client_report_sample` row never substitutes for either the HTML dossier or the rendered Markdown fallback.

## Evidence first

Read [profile-audit.md](references/profile-audit.md) for every audit. Every internal evidence record and every material Markdown fallback or expanded-mode item must begin with exactly one prefix: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. The HTML dossier translates those states into natural localized language and hides internal IDs. Put status only after the colon in parentheses: `verified: (visible)`, `unknown: (unavailable)`, or `unknown: (conflicting)`. Never use slash compounds. A prompt, CV, or recalled profile is candidate-reported until inspected. Do not promote a candidate-reported fact to verified. When sources conflict, name the conflict, request confirmation, and do not rewrite that section.

Audit all inspectable sections listed in [profile-audit.md](references/profile-audit.md); mark the rest `unknown: (unavailable)`. Analytics are dated observations, not causal proof.

A normal Markdown fallback after live inspection uses a compact `Live source summary` after the evidence appendix; it never requires a canonical `approval_gates` row before recommendations. Summarize the capture date, inspected and unavailable sections, redaction boundary, read-only scope, raw-profile non-retention, evidence promotion rule, and `no external action`. The normal HTML dossier hides this technical summary. Expanded modes retain `linkedin_live_evidence_snapshot` as the first `approval_gates` row. That row records `capture_date`, `browser_source`, `source_url_state`, `inspected_sections`, `unavailable_sections`, `redaction_boundary`, `evidence_promotion_rule`, `browser_action_scope`, `consent`, `not_saved_raw_profile`, `next_capture_step`, and `no_external_action=true`. Never store or repeat raw profile text, contact details, private identifiers, cookies, session identifiers, tokens, or full URLs.

never invent LinkedIn algorithm rules, recruiter-ranking mechanics, causal impact, guaranteed outcomes, unsupported experience, unsupported skills, metrics, seniority, production scope, eligibility, or market demand. Do not infer production responsibility from a tool name.

## Position, then draft

Read [search-positioning.md](references/search-positioning.md) when proposing targets, titles, locations, skills, or keywords. Current keyword or employer-demand claims require dated current vacancies; otherwise label each keyword a hypothesis and route market research to `research-professional-market`. US-remote does not imply US work authorization, geography eligibility, tax/contract eligibility, or time-zone fit: ask and label these gaps.

Give precise, section-specific drafts that retain their evidence label. Use confirmation placeholders for unverified outcomes and never turn candidate-reported facts into verified facts. Before suggesting a public artifact, read [networking-and-content.md](references/networking-and-content.md): do not propose sanitized internal architectures, projects, screenshots, dashboards, or examples without an explicit confidentiality review.

## Coach-grade delivery (expanded modes only)

Every audit must include a professional coaching layer, not only safe evidence inventory. Start with `coach_brief`: a one-screen, candidate-facing plan before the evidence appendix. Its first row must be a readable `coach_opening` with `plain_english_decision`, `client_takeaway`, and `next_review_trigger`, so the candidate immediately understands the recommendation before seeing matrices. Immediately after it, add exactly one `linkedin_premium_coach_summary=client_ready_executive_summary` row that reads like a senior coach cover note: include `overall_verdict`, `score_snapshot`, `positioning_decision`, `primary_opportunity`, `biggest_risk`, `next_30_minutes`, `next_7_days`, `do_not_change_yet`, `success_criteria`, `evidence_confidence`, `outcome_boundary=not_a_job_interview_recruiter_response_or_search_ranking_prediction`, `no_external_action=true`, and `draft_only=true`. The summary must be human-readable and decisive, not a terse contract dump, and must never promise ranking, recruiter response, interviews, or external actions. The brief must also include `positioning_decision`, `why_this_now`, exactly three ranked `do_now` items, `confirm_next`, `defer_or_omit`, and `coach_checkpoint`; each item remains draft-only and evidence-labelled. Keep the exact required sections below, but make the first line of each major section decision-oriented and useful to a hiring coach. Use [profile-audit.md](references/profile-audit.md) for the full `executive_diagnosis` contract, including scorecard, dimensions, photo/banner visual review, authorized `linkedin_visual_evidence_scorecard` rows, and `linkedin_score_improvement_roadmap` stages. Each score stage connects low dimensions to action using `linked_low_score_dimensions`, `intervention_type`, `exact_candidate_action`, `copy_or_prompt`, `acceptance_criteria`, and `effort_level`. In `visibility_gaps`, separate `fix_now`, `confirm_before_using`, and `defer`. In `positioning`, include `decision_rationale` and a no-inflation route for unsupported target technologies. In `rewrites`, include `thirty_minute_edit_script`, `copy_ready_headline`, `copy_ready_about`, one `linkedin_premium_rewrite_pack=client_ready_copy_review_package` row, exactly five `linkedin_premium_rewrite_item=coach_review_copy_block` rows, and a `linkedin_edit_packet` row set covering at least `headline`, `about`, `experience`, and `skills`. The premium rewrite pack is the client-facing copy review package that turns the diagnosis into concrete profile and first-screen copy without publishing anything: include `source_cover_sheet=client_ready_one_page_linkedin_diagnosis`, `sections_included=headline,about_opening,experience_bullet,featured_proof_asset,recruiter_screen_answer`, coach verdict, copy strategy, primary copy risk, evidence to confirm, highest impact ready copy, client review sequence, privacy boundary, outcome boundary, the exact action, exact target, and exact final content or asset identity authorization gate, `no_external_action=true`, and `draft_only=true`. The five premium items must cover `headline`, `about_opening`, `experience_bullet`, `featured_proof_asset`, and `recruiter_screen_answer`; each item includes source priority, target section, copy goal, draft copy, evidence used, evidence missing, claim boundary, confidentiality boundary, coach note, acceptance test, candidate review question, publish readiness, and the same no-action gates. Each `linkedin_edit_packet` row includes `evidence_id`, `before_state`, `after_state`, `section_action`, `publish_readiness`, `risk_note`, `confirm_or_omit`, and `publish_checklist`. The edit packet is the section-by-section copy/paste package: show what changes, why it changes, what is ready now, and what must be confirmed or omitted before publishing. Also include conditional drafts named `if_<technology>_confirmed`, `if_<technology>_unconfirmed`, and `if_no_<technology>_experience` when the user asks about an unverified technology such as Jenkins. In `experiment_plan`, include `top_3_actions` with observable follow-up metrics.

If the target technology is not supported by inspected evidence, say plainly that it must stay out of headline and About claims until confirmed. Offer a truthful alternative built from supported CI/CD, automation, reliability, or platform evidence. Do not let the safety labels become the product; the output should read like an expert coach who is careful with evidence.

## Expanded appendix response

In an expanded mode, return these exact sections after the client report, with labels on material claims:

```text
coach_brief
executive_diagnosis
visibility_gaps
positioning
rewrites
networking_drafts
content_plan
experiment_plan
approval_gates
audit_priority_matrix
keyword_evidence_matrix
outreach_funnel
proof_asset_matrix
linkedin_funnel_events
```

Use [profile-audit.md](references/profile-audit.md) to build `audit_priority_matrix`: section, evidence status, target theme/query, supported proof, issue, priority, draft/change, and confirmation needed. Use [search-positioning.md](references/search-positioning.md) to build `keyword_evidence_matrix`: phrase/title variant, dated vacancy source, geography/arrangement, candidate fact ID or `unknown`, safe profile section, and decision `use|confirm|omit`.

Use [networking-and-content.md](references/networking-and-content.md) for `networking_drafts`, `outreach_funnel`, and `proof_asset_matrix`. That reference defines recruiter expansion, `recruiter_discovery_engine` rows with `discovery_query` and `discovery_signal`, target shortlists, target decision gates, executive first-contact strategy, outreach labs, first-interview 7-day plans, weekly first-interview coach plans, recruiter bridge/playbook, reply triage, first-screen conversion gates, screen handoff, first-screen prep, and proof assets. Keep those rows draft-only, evidence-labelled, small-batch, manually reviewed, and gated by the exact action, exact target, and exact final content or asset identity authorization rule.

For recruiter targeting, the shortlist row must explicitly include `shortlist_goal`, `ranking_method`, `batch_decision`, `top_priority_targets`, `recommended_draft_type`, and `do_not_contact_reason` before any draft variant is produced.

Use [experiments.md](references/experiments.md) for a 14/30/60/90-day measurement plan, `linkedin_intervention_registry`, `linkedin_funnel_cohort_snapshot`, and `linkedin_funnel_events`: dated candidate-isolated observations for profile view/search appearance, qualified contact, conversation, referral/application, recruiter screen, interview, source, version, and confounders. Make one attributable change at a time where practical; report observed results and uncertainty rather than attribution.

In an expanded mode, if browser inspection was used, `approval_gates` must include `linkedin_live_evidence_snapshot` first with `source_url_state`, `redaction_boundary`, `evidence_promotion_rule`, `browser_action_scope`, `not_saved_raw_profile`, inspected/unavailable sections, and no raw profile text.

## Action gate

Follow the central rule in [evidence-and-safety.md](../professional-growth-coach/references/evidence-and-safety.md). Non-negotiable: immediately before execution, require the exact action, exact target, and exact final content or asset identity when content or assets apply. Inspection, earlier approval, draft approval, and benchmark consent do not carry forward. Until exact authorization is obtained and execution succeeds, keep `action_state=not_executed` and do not perform a profile edit, connection request, message, post, publication, upload, application, sharing, or scheduling action.
