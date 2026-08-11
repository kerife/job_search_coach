# Task 6 with-skill forward evaluations

Read-only synthetic evaluations of `optimize-career-assets`. No application, profile edit, upload, message, export, or publication was performed.

## Technical: Terraform and Argo CD vacancy

Fixture: `fixtures/assets-technical.md`

### Raw full output

```text
fact_matrix
candidate-reported: F-001 Python automation; F-002 Linux support; F-003 Kubernetes learning lab.
unknown: (unavailable) Terraform and Argo CD facts.
ats_gap_map
inferred: formatting=unknown until the source CV is supplied.
candidate-reported: terminology=Kubernetes may be used only for F-003 learning-lab scope.
inferred: evidence=every new bullet must cite F-001, F-002, or F-003.
unknown: (unavailable) genuine skill gap=Terraform and Argo CD are absent; do not insert them as experience.
master_cv_recommendations
inferred: recommendation=retain only supported Python, Linux, and learning-lab language; use [confirm: result] rather than a metric.
vacancy_tailored_draft
candidate-reported: [F-001] Automated [confirm: supported Linux task] with Python.
candidate-reported: [F-003] Completed a Kubernetes learning lab [confirm: scope].
application_packet
candidate-reported: candidate_id=C-TECH target_vacancy_id=V-TECH packet_goal=prepare reviewable draft for technical vacancy.
candidate-reported: vacancy_source_state=supplied synthetic fixture; role_requirements=V-TECH Python/Linux/Kubernetes plus Terraform/Argo CD requirements.
candidate-reported: matched_evidence=V-TECH -> F-001 Python automation; V-TECH -> F-002 Linux support; V-TECH -> F-003 Kubernetes lab.
unknown: (unavailable) unsupported_or_missing_claims=Terraform, Argo CD, production Kubernetes scope, metrics, and deployment outcomes cannot be claimed.
candidate-reported: cv_bullets=[F-001] Automated supported Linux work with Python; [F-003] Completed Kubernetes learning lab [confirm: scope].
candidate-reported: recruiter_summary=draft note can present Python automation and Linux support with Kubernetes learning-lab evidence; do not claim Terraform or Argo CD.
inferred: message_angle=position the candidate around Python/Linux automation and transparent Kubernetes learning scope, not unavailable Terraform or Argo CD experience.
- inferred: candidate_id=C-TECH; target_vacancy_id=V-TECH; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-001; asset_surface=cv_bullet; vacancy_requirement_ids=V-TECH; candidate_fact_ids=F-001,F-002; claim_text=Automated supported Linux work with Python; evidence_state=supported; confidence=medium; missing_proof=confirmed result metric; blocked_claims=Terraform Argo CD production Kubernetes and deployment outcomes; decision=use; reviewer_note=usable only as Python Linux automation scope; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-TECH; target_vacancy_id=V-TECH; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-002; asset_surface=cv_bullet; vacancy_requirement_ids=V-TECH; candidate_fact_ids=F-003; claim_text=Completed Kubernetes learning lab with scope placeholder; evidence_state=partial; confidence=medium; missing_proof=lab scope and recency confirmation; blocked_claims=production Kubernetes ownership metrics Terraform and Argo CD; decision=revise; reviewer_note=keep learning lab label visible until confirmed; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-TECH; target_vacancy_id=V-TECH; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-003; asset_surface=recruiter_summary; vacancy_requirement_ids=V-TECH; candidate_fact_ids=F-001,F-002,F-003; claim_text=Draft note can present Python automation Linux support and Kubernetes learning lab evidence; evidence_state=partial; confidence=medium; missing_proof=confirmed vacancy priority and lab scope; blocked_claims=Terraform Argo CD fit promise interview promise and production scope; decision=revise; reviewer_note=name missing requirements plainly before recruiter use; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-TECH; target_vacancy_id=V-TECH; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-004; asset_surface=message_angle; vacancy_requirement_ids=V-TECH; candidate_fact_ids=F-001,F-002,F-003; claim_text=Position around Python Linux automation and transparent Kubernetes learning scope; evidence_state=partial; confidence=medium; missing_proof=target recruiter context; blocked_claims=Terraform Argo CD experience and response promise; decision=revise; reviewer_note=outreach angle only and not permission to send; draft_only=true; no_external_action=true.
inferred: first_interview_prep_handoff=send V-TECH requirements plus F-001 through F-003 and missing Terraform/Argo CD gaps to prepare-role-interviews after an interview stage is known.
inferred: tracking_event=proposed local application draft record only; application_date, response_date, interview_stage, and offer_state remain unknown.
unknown: approval_gate=draft_only=true consent=not_granted causality_boundary=no_outcome_guarantee; exact action-and-target authorization is required before apply, upload, message, share, or export.
portfolio_evidence_plan
inferred: recommendation=create a new Terraform/Argo CD learning lab only if the candidate owns it; complete a confidentiality review and do not claim it exists now.
consistency_report
unknown: (unavailable) LinkedIn and CV have not been supplied for comparison.
```

## Non-technical

Fixture: `fixtures/assets-non-technical.md`

### Raw full output

```text
fact_matrix
candidate-reported: F-101 Scheduled retail shifts; F-102 assisted inventory counts; F-103 used Excel for basic tracking.
unknown: (unavailable) CRM experience, sales results, team size, and revenue facts.
ats_gap_map
inferred: formatting=unknown until the source CV is supplied.
candidate-reported: terminology=use scheduling, inventory, and Excel only for F-101 through F-103.
inferred: evidence=any sales, management, or CRM claim lacks a candidate fact ID.
unknown: (unavailable) genuine skill gap=the vacancy's CRM requirement is absent from F-101 through F-103.
master_cv_recommendations
inferred: recommendation=use action/context bullets for F-101 through F-103 and retain [confirm: result] where outcomes are unavailable.
vacancy_tailored_draft
candidate-reported: [F-101] Supported retail shift scheduling [confirm: scope].
candidate-reported: [F-102] Assisted inventory counts using [F-103] Excel tracking.
application_packet
candidate-reported: candidate_id=C-RETAIL target_vacancy_id=V-RETAIL packet_goal=prepare reviewable draft for non-technical vacancy.
candidate-reported: vacancy_source_state=supplied synthetic fixture; role_requirements=V-RETAIL scheduling, inventory, Excel, CRM, sales, and management requirements.
candidate-reported: matched_evidence=V-RETAIL -> F-101 scheduling; V-RETAIL -> F-102 inventory support; V-RETAIL -> F-103 Excel tracking.
unknown: (unavailable) unsupported_or_missing_claims=CRM ownership, sales results, revenue, management scope, and team size cannot be claimed.
candidate-reported: cv_bullets=[F-101] Supported retail shift scheduling [confirm: scope]; [F-102] Assisted inventory counts using [F-103] Excel tracking.
candidate-reported: recruiter_summary=draft note can present scheduling, inventory, and Excel evidence; it must name CRM as a gap if the vacancy requires it.
inferred: message_angle=position the candidate around retail operations support and Excel tracking while separating CRM and sales-result gaps.
- inferred: candidate_id=C-RETAIL; target_vacancy_id=V-RETAIL; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-101; asset_surface=cv_bullet; vacancy_requirement_ids=V-RETAIL; candidate_fact_ids=F-101; claim_text=Supported retail shift scheduling with scope placeholder; evidence_state=partial; confidence=medium; missing_proof=scope and result confirmation; blocked_claims=management ownership team size revenue and sales results; decision=revise; reviewer_note=do not upgrade support work into manager ownership; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-RETAIL; target_vacancy_id=V-RETAIL; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-102; asset_surface=recruiter_summary; vacancy_requirement_ids=V-RETAIL; candidate_fact_ids=F-101,F-102,F-103; claim_text=Draft note can present scheduling inventory and Excel evidence while naming CRM as a gap; evidence_state=partial; confidence=medium; missing_proof=CRM status confirmation; blocked_claims=CRM ownership sales quota revenue and team leadership claims; decision=revise; reviewer_note=safe only if the gap remains explicit; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-RETAIL; target_vacancy_id=V-RETAIL; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-103; asset_surface=message_angle; vacancy_requirement_ids=V-RETAIL; candidate_fact_ids=F-101,F-102,F-103; claim_text=Position around retail operations support and Excel tracking; evidence_state=supported; confidence=medium; missing_proof=target employer context; blocked_claims=CRM sales-result management and response promise; decision=use; reviewer_note=keep transferable support framing; draft_only=true; no_external_action=true.
inferred: first_interview_prep_handoff=send V-RETAIL requirements plus F-101 through F-103 and CRM gap to prepare-role-interviews after an interview stage is known.
inferred: tracking_event=proposed local application draft record only; application_date, response_date, interview_stage, and offer_state remain unknown.
unknown: approval_gate=draft_only=true consent=not_granted causality_boundary=no_outcome_guarantee; exact action-and-target authorization is required before apply, upload, message, share, or export.
portfolio_evidence_plan
inferred: recommendation=create a sample inventory tracker only if the candidate owns it and after confidentiality review; do not present it as employer work.
consistency_report
unknown: (unavailable) LinkedIn and CV titles, dates, skills, and public links have not been supplied for comparison.
```

## Junior

Fixture: `fixtures/assets-junior.md`

### Raw full output

```text
fact_matrix
candidate-reported: F-201 completed spreadsheet coursework; F-202 coordinated volunteer event check-in; F-203 maintained a volunteer attendance list.
unknown: (unavailable) employment history, outcome metrics, and professional analytics-tool experience.
ats_gap_map
inferred: formatting=unknown until the source CV is supplied.
candidate-reported: terminology=spreadsheet and coordination language may describe F-201 through F-203.
inferred: evidence=professional analyst and quantified-impact claims lack a candidate fact ID.
unknown: (unavailable) genuine skill gap=the vacancy's professional SQL requirement is absent from F-201 through F-203.
master_cv_recommendations
inferred: recommendation=keep coursework and volunteer work visibly separated from employment and use [confirm: result] instead of metrics.
vacancy_tailored_draft
candidate-reported: [F-202] Coordinated volunteer event check-in [confirm: event scope].
candidate-reported: [F-203] Maintained a volunteer attendance list [confirm: tool and scope].
application_packet
candidate-reported: candidate_id=C-JUNIOR target_vacancy_id=V-JUNIOR packet_goal=prepare reviewable draft for junior vacancy.
candidate-reported: vacancy_source_state=supplied synthetic fixture; role_requirements=V-JUNIOR spreadsheet, coordination, attendance tracking, professional SQL, and analyst experience requirements.
candidate-reported: matched_evidence=V-JUNIOR -> F-201 spreadsheet coursework; V-JUNIOR -> F-202 event coordination; V-JUNIOR -> F-203 attendance tracking.
unknown: (unavailable) unsupported_or_missing_claims=professional analyst employment, SQL, quantified impact, and analytics-tool work cannot be claimed.
candidate-reported: cv_bullets=[F-202] Coordinated volunteer event check-in [confirm: event scope]; [F-203] Maintained volunteer attendance list [confirm: tool and scope].
candidate-reported: recruiter_summary=draft note can present coursework and volunteer coordination separately from employment; it must not imply professional analyst experience.
inferred: message_angle=position the candidate around entry-level coordination and spreadsheet evidence, with SQL and employment scope framed as gaps.
- inferred: candidate_id=C-JUNIOR; target_vacancy_id=V-JUNIOR; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-201; asset_surface=cv_bullet; vacancy_requirement_ids=V-JUNIOR; candidate_fact_ids=F-202,F-203; claim_text=Coordinated volunteer event check-in and maintained volunteer attendance list; evidence_state=partial; confidence=medium; missing_proof=event scope tool and dates; blocked_claims=professional analyst employment SQL metrics and analytics tool work; decision=revise; reviewer_note=keep volunteer label visible; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-JUNIOR; target_vacancy_id=V-JUNIOR; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-202; asset_surface=recruiter_summary; vacancy_requirement_ids=V-JUNIOR; candidate_fact_ids=F-201,F-202,F-203; claim_text=Draft note can present coursework and volunteer coordination separately from employment; evidence_state=partial; confidence=medium; missing_proof=coursework details and volunteer scope; blocked_claims=professional analyst experience SQL and quantified impact; decision=revise; reviewer_note=avoid implying paid analyst work; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-JUNIOR; target_vacancy_id=V-JUNIOR; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-203; asset_surface=message_angle; vacancy_requirement_ids=V-JUNIOR; candidate_fact_ids=F-201,F-202,F-203; claim_text=Position around entry-level coordination and spreadsheet evidence; evidence_state=partial; confidence=medium; missing_proof=target role context; blocked_claims=SQL employment scope and interview promise; decision=revise; reviewer_note=message angle remains draft only; draft_only=true; no_external_action=true.
inferred: first_interview_prep_handoff=send V-JUNIOR requirements plus F-201 through F-203 and SQL/professional-experience gaps to prepare-role-interviews after an interview stage is known.
inferred: tracking_event=proposed local application draft record only; application_date, response_date, interview_stage, and offer_state remain unknown.
unknown: approval_gate=draft_only=true consent=not_granted causality_boundary=no_outcome_guarantee; exact action-and-target authorization is required before apply, upload, message, share, or export.
portfolio_evidence_plan
inferred: recommendation=build a spreadsheet exercise only if the candidate owns it and after confidentiality review; do not claim professional SQL experience.
consistency_report
unknown: (unavailable) LinkedIn and CV education, volunteer dates, and employment labels have not been supplied for comparison.
```

## Career transition

Fixture: `fixtures/assets-career-transition.md`

### Raw full output

```text
fact_matrix
candidate-reported: F-301 handled customer-support requests; F-302 documented issue details; F-303 escalated support cases using the supplied process.
unknown: (unavailable) data-analysis employment, SQL, dashboard, metric, and portfolio facts.
ats_gap_map
inferred: formatting=unknown until the source CV is supplied.
candidate-reported: terminology=communication, issue documentation, and escalation may describe F-301 through F-303.
inferred: evidence=data-analysis, SQL, and dashboard claims lack a candidate fact ID.
unknown: (unavailable) genuine skill gap=the target data-analysis requirement is absent from F-301 through F-303.
master_cv_recommendations
inferred: recommendation=present F-301 through F-303 as transferable support evidence without relabeling the work as data analysis.
vacancy_tailored_draft
candidate-reported: [F-301] Handled customer-support requests [confirm: channel and scope].
candidate-reported: [F-302] Documented issue details and [F-303] escalated cases through the supplied process.
application_packet
candidate-reported: candidate_id=C-TRANSITION target_vacancy_id=V-DATA packet_goal=prepare reviewable draft for career-transition vacancy.
candidate-reported: vacancy_source_state=supplied synthetic fixture; role_requirements=V-DATA support documentation, escalation, data-analysis, SQL, dashboard, metric, and portfolio requirements.
candidate-reported: matched_evidence=V-DATA -> F-301 support requests; V-DATA -> F-302 issue documentation; V-DATA -> F-303 escalation process.
unknown: (unavailable) unsupported_or_missing_claims=data-analysis employment, SQL, dashboard, metrics, and portfolio proof cannot be claimed.
candidate-reported: cv_bullets=[F-301] Handled customer-support requests [confirm: channel and scope]; [F-302] Documented issue details and [F-303] escalated cases through the supplied process.
candidate-reported: recruiter_summary=draft note can present support documentation and escalation evidence as transferable; it must not relabel the role as data analysis.
inferred: message_angle=position the candidate around transferable support documentation and escalation evidence, not unproven data-analysis employment.
- inferred: candidate_id=C-TRANSITION; target_vacancy_id=V-DATA; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-301; asset_surface=cv_bullet; vacancy_requirement_ids=V-DATA; candidate_fact_ids=F-301,F-302,F-303; claim_text=Handled support requests documented issue details and escalated cases through supplied process; evidence_state=partial; confidence=medium; missing_proof=channel scope dates and outcomes; blocked_claims=data-analysis employment SQL dashboard metrics and portfolio proof; decision=revise; reviewer_note=transferable support evidence only; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-TRANSITION; target_vacancy_id=V-DATA; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-302; asset_surface=recruiter_summary; vacancy_requirement_ids=V-DATA; candidate_fact_ids=F-301,F-302,F-303; claim_text=Draft note can present support documentation and escalation evidence as transferable; evidence_state=partial; confidence=medium; missing_proof=confirmed support scope and target requirement priority; blocked_claims=data analysis relabeling SQL dashboard and metric claims; decision=revise; reviewer_note=must not relabel support role as data analysis; draft_only=true; no_external_action=true.
- inferred: candidate_id=C-TRANSITION; target_vacancy_id=V-DATA; application_claim_review_matrix=claim_to_asset_readiness_gate; claim_id=AC-303; asset_surface=message_angle; vacancy_requirement_ids=V-DATA; candidate_fact_ids=F-301,F-302,F-303; claim_text=Position around transferable support documentation and escalation evidence; evidence_state=partial; confidence=medium; missing_proof=portfolio or lab evidence if targeting analyst roles; blocked_claims=unproven data-analysis employment and response promise; decision=revise; reviewer_note=separate transferable evidence from missing analyst proof; draft_only=true; no_external_action=true.
inferred: first_interview_prep_handoff=send V-DATA requirements plus F-301 through F-303 and data-analysis gaps to prepare-role-interviews after an interview stage is known.
inferred: tracking_event=proposed local application draft record only; application_date, response_date, interview_stage, and offer_state remain unknown.
unknown: approval_gate=draft_only=true consent=not_granted causality_boundary=no_outcome_guarantee; exact action-and-target authorization is required before apply, upload, message, share, or export.
portfolio_evidence_plan
inferred: recommendation=create a data-analysis evidence project only if the candidate owns it and after confidentiality review; do not claim the project or skill already exists.
consistency_report
unknown: (unavailable) LinkedIn and CV role titles, dates, support scope, and public-project links have not been supplied for comparison.
```

## Evaluation result

inferred: every rewritten claim above cites a candidate fact ID or is labeled recommendation. Each scenario separates formatting, terminology, evidence, genuine skill gaps, and an application_packet with draft_only=true consent=not_granted causality_boundary=no_outcome_guarantee. Each application_packet now includes application_claim_review_matrix rows that map CV bullets, recruiter summaries, and message angles to fact IDs, requirement IDs, evidence state, decision, blocked claims, and no_external_action=true. No opaque ATS score or hiring outcome is promised. Exact action-and-target authorization remains required before an edit, upload, export, application, message, or public share.
