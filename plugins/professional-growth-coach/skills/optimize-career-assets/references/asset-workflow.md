# Truthful asset workflow

## Inputs and fact matrix

Collect candidate facts, their source, evidence label, and a stable candidate fact ID before drafting. Keep each fact's scope, date, and confidentiality status. Read the supplied target vacancy as evidence, not proof that the candidate has a requirement. Missing source, scope, metric, or result remains `unknown:`.

## Master CV and tailoring

Create a master CV recommendation from supported facts. For each vacancy-tailored bullet, map the rewritten claim to a candidate fact ID or label it recommendation. Use impact-first writing: supported action, supported context, then supported result. If the result is absent, use no metric or a `[confirm: result]` placeholder. Do not translate adjacent experience into Terraform or Argo CD experience.

Use vacancy terminology only when it truthfully names the candidate's work. A truthful transferable phrasing is preferable to keyword stuffing. A recommendation can say `inferred: recommendation=complete a candidate-owned Terraform lab before claiming Terraform familiarity`; it cannot state that the lab or skill already exists.

## Application packet

For a supplied vacancy, assemble a review packet after the fact matrix and before portfolio planning. Keep it draft-only and traceable:

- `matched_evidence` lists each vacancy requirement with the supporting candidate fact IDs or `unknown:` if no support exists.
- `role_requirements` assigns stable requirement IDs from the supplied vacancy; map support as `V-### -> F-###` wherever possible.
- `unsupported_or_missing_claims` names requirements, outcomes, metrics, certifications, work authorization, or tools that cannot be claimed yet.
- `cv_bullets` contains only fact-backed bullets or confirmation placeholders.
- `recruiter_summary` is a concise draft positioning note with fact IDs and no guarantee of fit, interview, or response.
- `message_angle` states the truthful outreach or cover-letter angle without implying permission to send.
- `application_claim_review_matrix` reviews every material CV bullet, recruiter-summary claim, and message angle before the packet is used. Use semicolon rows with `application_claim_review_matrix=claim_to_asset_readiness_gate`, `claim_id=AC-###`, `asset_surface`, `vacancy_requirement_ids`, `candidate_fact_ids`, `claim_text`, `evidence_state`, `confidence`, `missing_proof`, `blocked_claims`, `decision`, `reviewer_note`, `draft_only=true`, and `no_external_action=true`.
- `first_interview_prep_handoff` lists vacancy requirement IDs, candidate fact IDs, and gaps to pass to `prepare-role-interviews` once the interview stage is known.
- `tracking_event` is a proposed local event for `track-career-outcomes`; leave submission, response, interview, and offer states unknown until observed.
- `approval_gate` records `draft_only=true`, `consent=not_granted`, and `causality_boundary=no_outcome_guarantee`.

Approve a claim with `decision=use` only when it cites candidate fact IDs and the evidence state is supported. Claims with partial proof, missing scope, conflicting evidence, unknown facts, unsupported requirements, or confidentiality concerns must be `revise`, `hold_for_confirmation`, or `remove`. The matrix is a review tool, not authorization to apply, upload, send, or publish.

## Portfolio and export

Portfolio evidence plans name the candidate fact ID, the intended demonstration, and evidence that the candidate owns the material or has documented rights-holder permission explicitly covering public disclosure. Candidate approval alone cannot authorize employer or third-party material. Secrets and customer data are always forbidden, even with candidate approval or rights-holder permission; never include credentials, tokens, private keys, or customer data.

Record content eligibility separately from execution authorization. Ownership or public-disclosure permission does not authorize execution. Immediately before a share, publication, upload, or export, obtain exact action-and-target authorization under the skill's action gate.

Recommend a simple export: conventional headings, readable fonts, selectable text, a single-column layout where practical, and a manual text-extraction check. These are formatting recommendations, not a promise of behavior in an opaque ATS.

## Consistency check

Compare LinkedIn and CV title, employer, dates, scope, skills, metrics, and public portfolio links. Mark agreement with the source labels. Mark unresolved differences as `unknown: (conflicting)` and hold the affected rewrite for confirmation.
