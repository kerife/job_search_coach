---
name: optimize-job-search-assets
description: Use when drafting or auditing a truthful CV, vacancy-tailored application materials, ATS-oriented improvements, or a portfolio evidence plan.
---

# Optimize Job Search Assets

Turn supplied candidate facts and a target vacancy into reviewable drafts. Read [asset-workflow.md](references/asset-workflow.md), [ats-and-truthfulness.md](references/ats-and-truthfulness.md), and [candidate-fact-matrix.md](assets/candidate-fact-matrix.md) before drafting. Preserve candidate isolation and minimize personal data.

## Evidence rules

Every material item begins with exactly one canonical prefix: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. Optional qualifiers after the colon are allowed, for example `verified: (CV)` or `unknown: (unavailable)`. Never use slash compounds. A candidate fact receives a stable candidate fact ID. Every rewritten claim must map to a candidate fact ID or be labeled recommendation. Never upgrade a candidate-reported fact to verified.

Do not invent experience, skills, Terraform, Argo CD, metrics, scope, seniority, employers, outcomes, certifications, work authorization, or portfolio artifacts. A missing requirement is a genuine skill gap, not a keyword to stuff. Reconcile LinkedIn and CV wording; where they conflict, label `unknown: (conflicting)` and do not choose a version without confirmation.

## Draft and diagnose

Use impact-first bullets: state the supported action, context, and result only where the fact matrix supports it. When a result or metric is absent, retain the action and context or use a confirmation placeholder; do not create a number or invented metrics. Tailor terminology to the supplied vacancy only where it truthfully describes an existing fact. Treat vacancy requirements as candidate-reported only when supplied by the candidate; otherwise mark the vacancy source appropriately.

ATS feedback is an audit, not a score. Separate formatting, terminology, evidence, and genuine skill gap findings. Do not claim compatibility with an opaque ATS or promise an ATS score, ranking, interview, or outcome. Give plain-text export recommendations such as a readable heading hierarchy, conventional section names, selectable text, and a human review after export.

For portfolio ideas, propose only evidence plans whose material the candidate owns or whose rights holder has granted documented permission that explicitly covers public disclosure. Candidate approval alone cannot authorize employer or third-party material. Name the fact ID demonstrated and record the ownership or permission evidence plus a confidentiality review. Secrets and customer data are always forbidden, even with candidate approval or rights-holder permission. Never include credentials, tokens, private keys, or customer data in a portfolio.

Content eligibility does not authorize execution. Even when ownership or documented rights-holder permission makes material eligible, retain the separate action gate and obtain exact action-and-target authorization immediately before any external share, publication, upload, or export.

## Application packet

When a target vacancy is supplied, create a draft-only application packet that a coach could review before any external action. Include `candidate_id`, `target_vacancy_id`, `packet_goal`, `vacancy_source_state`, `role_requirements`, `matched_evidence`, `unsupported_or_missing_claims`, `cv_bullets`, `recruiter_summary`, `message_angle`, `application_claim_review_matrix`, `first_interview_prep_handoff`, `tracking_event`, and `approval_gate`. Set `draft_only=true`, `consent=not_granted`, and `causality_boundary=no_outcome_guarantee` until the user gives exact action-and-target authorization.

The packet is a planning artifact, not an application. The recruiter summary must cite supported fact IDs, name missing requirements plainly, avoid fit guarantees, and never imply the user is authorized to send it. Create the `first_interview_prep_handoff` only from supplied vacancy requirements and candidate fact IDs; route to `prepare-role-interviews` for stage-specific coaching after the vacancy and interview stage are known. Create the `tracking_event` as a proposed local record for `track-job-search-outcomes`; do not mark an application submitted or response received without evidence.

Add one `application_claim_review_matrix=claim_to_asset_readiness_gate` row for each material CV bullet, recruiter-summary claim, and message angle. Each row includes `claim_id`, `asset_surface`, `vacancy_requirement_ids`, `candidate_fact_ids`, `claim_text`, `evidence_state`, `confidence`, `missing_proof`, `blocked_claims`, `decision`, `reviewer_note`, `draft_only=true`, and `no_external_action=true`. Use `decision=use` only when the claim cites candidate fact IDs and has supported evidence; unsupported, conflicting, unknown, or missing-proof claims must be `revise`, `hold_for_confirmation`, or `remove`.

## Required response

Return these exact sections, with labels on material claims:

```text
fact_matrix
ats_gap_map
master_cv_recommendations
vacancy_tailored_draft
application_packet
portfolio_evidence_plan
consistency_report
```

## Action gate

Drafting, local analysis, and authorized read-only inspection are allowed. Immediately before any CV or LinkedIn edit, application, upload, message, share, publication, or external export, obtain explicit action-and-target authorization. A request for optimization, a draft approval, or earlier general consent does not authorize execution. Do not edit, apply, upload, message, share, publish, or export without exact action-and-target authorization.
