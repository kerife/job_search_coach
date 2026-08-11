# Client report

This is the validated Markdown compatibility path. The bundle or audited evidence is the decision ledger; this reference defines how to translate it into a readable fallback or expanded report without exposing internal contracts. For a normal audit with local execution, use [html-dossier.md](html-dossier.md) instead.

An explicit private recruiter-practice request does not use this LinkedIn client report. It belongs to the separate private recruiter practice session branch and must not replace or change normal LinkedIn dossier delivery.

An explicit private recruiter-reply triage request also does not use this LinkedIn client report. It belongs to the closed private decision-card branch, which accepts only an identity-free summary and one supplied fact, asks exactly one intake question when either is missing, and never exposes raw content, internal identifiers, external action, or calendar detail. It must not replace or change normal LinkedIn dossier or debug delivery when that explicit private request is absent. A ready handoff is manual input only for one recruiter-screen question, with `candidate_answer_state=unanswered` and `score_state=unknown`; it does not auto-start preparation or create a `module_execution_packet`. Clarify-first and stop cards omit it.

## Markdown delivery modes

- `normal` -> compact evidence index
- `debug | eval | detail_requested` -> full legacy appendix

Both Markdown modes start with the same complete client report. Use `normal` only when local execution is unavailable or the HTML workflow has failed twice after its single repair attempt. Select the expanded branch only when the request or run explicitly names `debug`, `eval`, or `detail_requested`. A request explicitly labelled normal stays normal even if it also asks to skip presentation or return raw internal rows. A normal Markdown fallback is, in order: the localized H1, all eight localized H2 sections, the localized appendix H2, the compact evidence index, a compact `Routing receipt`, and, when live inspection was used, a compact `Live source summary`. Begin with the H1 and finish the client layer before composing any appendix source rows. Never put a preface, status note, evidence label row, JSON, YAML, canonical contract row, or router block before the report H1. A `linkedin_rendered_client_report_sample` row is only an appendix source and never replaces the rendered Markdown.

The Markdown fallback says briefly that the HTML artifact could not be generated and never includes a file link, rejected dossier JSON, raw validation values, traceback, or local error path. It preserves candidate isolation, natural client language, and the no-action boundary. Debug, eval, and detail modes keep the existing canonical appendix and validator contract unchanged.

## Localized structure

Use the bundle locale and this map exactly. The H1 is `Diagnóstico ejecutivo de LinkedIn` for `es` and `LinkedIn Executive Diagnostic` for `en`. The appendix H2 is `Apéndice de evidencia` for `es` and `Evidence appendix` for `en`.

| Key | Spanish H2 | English H2 |
| --- | --- | --- |
| `verdict` | Veredicto | Verdict |
| `score` | Calificación | Score |
| `priorities` | Las tres decisiones prioritarias | Three priority decisions |
| `copy` | Copy listo para revisar | Copy ready for review |
| `do_not_change` | No cambies todavía | Do not change yet |
| `plan` | Plan privado de siete días | Private seven-day plan |
| `evidence_needed` | Evidencia pendiente | Evidence needed |
| `boundaries` | Límites del diagnóstico | Diagnostic boundaries |

Start at byte 0 with the localized H1. Render the eight H2 sections once, in map order, then the localized appendix H2 once. Do not add other H2 headings before the appendix.

## Positive report recipe

### Verdict

Write one or two plain-language sentences that identify the bundle's primary gap and lowest-risk decision. Use “lower-risk” in English or “de menor riesgo” in Spanish for that judgment; certainty words such as “safe,” “certain,” `seguro`, or `segura` conflict with the required outcome boundary. Use only supported observations and facts. Do not claim a profile change will improve ranking, responses, interviews, salary, hiring, or time to hire.

### Score

Render one localized five-column Markdown table with exactly these domains in this order: `visual`, `headline`, `about`, `experience`, `skills`, `proof`, `completeness`. Translate domain and state labels using the validator's locale map. For each `score_ledger.domains[]` row:

- copy `state`, `raw_score`, and every `evidence_id` exactly;
- use an em dash for a `not_scored` score; never turn unavailable evidence into zero;
- add a short factual reason derived from the observation state or reason code.

After the table, render the localized overall score, coverage, and confidence lines using `score_ledger.overall_score`, `scored_weight`, `not_scored_weight`, and `confidence`. Do not recompute or improve the supplied values.

### Three priorities

Render exactly three numbered H3 blocks, ordered by `priorities[].rank`. Localize only the visible section and field labels. Copy these bundle values exactly: `section`, `diagnosed_gap`, `action_type`, all `evidence_ids`, `timebox`, `done_when`, and `impact_basis`. Priority weights, order, timeboxes, and review windows are coach judgment and must always use `COACH_HEURISTIC`.

### Three copy blocks

First render the localized primary-copy-category line from `eval_expectations.primary_copy_category`. Then render exactly one H3 for each bundle `copy_blocks[]` item; the set must be `headline`, `about_opening`, and `experience_bullet`.

Copy `copy_id`, `state`, `audience`, `problem`, `fact_ids`, `evidence_ids`, and `claim_boundary` exactly. Derive the visible `Claims` list from the referenced facts:

- `ready`: include each referenced `claim_token` whose fact is `verified` or `candidate_reported`;
- `requires_confirmation`: include each referenced `claim_token` whose fact is `unknown` or `inferred`;
- `omit`: use `none` or `ninguno` for both facts and claims when the arrays are empty.

Write a short, useful `Copy` sentence. Ready copy may use only supported facts. Confirmation copy must explicitly keep the unconfirmed capability or scope out of public copy. Omit copy must not expose a blocked claim or unsupported outcome.

### Do not change yet

Render the `blocked_claims[]` values, in order, as no more than three localized bullet items. Put the exact code in backticks after the localized blocked-claim label, followed by a brief explanation. Never repeat a blocked value as ready copy.

### Private seven-day plan

Use only private review work. Each bullet must be `localized label: ACTION|target` from these closed sets:

- `PROFILE_REVIEW`: `headline`, `about_opening`, or `experience_example`;
- `COPY_VALIDATE`: `headline`, `about_opening`, or `experience_example`;
- `EVIDENCE_REQUEST`: `pending_fact` or `visual_boundary`;
- `PROOF_PREPARE`: `experience_example` or `pending_fact`.

End with the localized sentence that no external action is performed. Do not include outreach, messages, applications, scheduling, publishing, uploads, connections, courses, or public actions.

### Evidence needed

Create one numbered localized H3 question for every distinct unconfirmed fact that appears in a `requires_confirmation` copy block, and no others. Each question must contain the localized fields for a meaningful question, the exact `fact_id`, and `copy:<section>` as the decision it can change. If there are no confirmation-copy facts, include a short sentence saying no decision-changing question is pending and no H3 question blocks. Never request extra visual evidence when the bundle policy is `NO_EXTRA_VISUAL_REQUEST`.

### Boundaries

End the client layer with a concise statement that the diagnostic estimates profile clarity and credibility, does not predict ranking, recruiter response, interviews, salary, hiring, or time to hire, and performs no external action. Preserve candidate isolation, confidentiality, protected-trait boundaries, and authorization naming the exact action, exact target, and exact final content or asset identity when content or assets apply.

## Appendix recipe

In normal mode, add only a compact evidence index in prose or ordinary bullets, followed by a compact `Routing receipt`. Keep the complete post-appendix material under 250 words. The evidence index may summarize inspected/unavailable domains, evidence IDs, and the availability of technical detail. The routing receipt may summarize the selected module, readiness, delivery, and ordered later-module handoff. Neither may contain `candidate_id=`, any `linkedin_...=` token, semicolon-delimited canonical rows, `coach_case_brief`, `coach_executive_review`, or `module_execution_packet` rows.

A normal Markdown fallback after live inspection uses a compact `Live source summary` after the evidence appendix; it never requires a canonical `approval_gates` row before recommendations. Include the capture date, inspected and unavailable sections, redaction boundary, read-only scope, raw-profile non-retention, evidence promotion rule, and `no external action`. Expanded modes retain `linkedin_live_evidence_snapshot` as the first `approval_gates` row.

In `debug`, `eval`, or `detail_requested` mode, put the full legacy appendix after the same client report. Use H3 headings in this exact order: `coach_brief`, `executive_diagnosis`, `visibility_gaps`, `positioning`, `rewrites`, `networking_drafts`, `content_plan`, `experiment_plan`, `approval_gates`, `audit_priority_matrix`, `keyword_evidence_matrix`, `outreach_funnel`, `proof_asset_matrix`, `linkedin_funnel_events`. Every section needs at least one canonical evidence-labelled row, and every row needs exactly one `candidate_id` matching the current candidate. Read `profile-audit.md`, `search-positioning.md`, `networking-and-content.md`, and `experiments.md` for those legacy row contracts.

## Source and safety policy

A current official source may stand alone when it directly supports a profile-quality criterion. Official category coverage counts only a category-specific registered locator. Dated secondary guidance is optional and must be identified as secondary with its publisher and document title when used. Secondary sources never satisfy official category coverage. Publisher provenance is limited to one line and 120 characters; document titles are limited to one line and 240 characters. Neither provenance field may contain secrets or private data. Coach-selected weights, priority order, windows, and timeboxes are `COACH_HEURISTIC`; never present them as LinkedIn measurements or causal evidence.

Use exactly one evidence label for every material appendix row: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. Keep unavailable evidence unscored, never infer protected traits from visual material, and never expose raw profile text, private analytics, contact details, full profile URLs, credentials, confidential employer/customer material, or another candidate's facts. Drafts remain private until the candidate reviews them. Inspection authorization never authorizes editing, messaging, connecting, posting, publishing, uploading, applying, sharing, or scheduling. Immediately before execution, require the exact action, exact target, and exact final content or asset identity when content or assets apply.

## Limits and validation

Keep the client report at or below 800 words excluding score-table rows. Keep the full normal payload at or below 1,100 words. Before returning a report backed by a bundle, run the real validator and repair every error:

Deterministic scanning is bounded, and an independent fresh-context policy review is required before returning the report.

```bash
python3 plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py REPORT.md BUNDLE.json
```

For `debug`, `eval`, or `detail_requested`, add `--appendix-mode` with the matching mode. The validator is authoritative for localized labels, score reconciliation, decision matching, privacy, safety, word limits, and appendix shape.
