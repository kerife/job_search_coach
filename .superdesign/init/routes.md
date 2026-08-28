# Routes

## Routing model

This plugin exposes no HTTP routes, SPA routes, framework page files, or router configuration. The UI surfaces are offline HTML artifacts rendered by Python commands. The logical paths below are documentation handles only, **not runtime URLs**.

| Logical artifact | Renderer entry | Template | Layout |
| --- | --- | --- | --- |
| `/executive-career-dossier` | `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py` (v1) or `render_executive_career_dossier_v2.py` (v2) | `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html` | `ExecutiveCareerDossierDocument` |
| `/recruiter-practice-session` | `plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py` | `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html` | `RecruiterPracticeSessionDocument` |
| `/private-recruiter-reply-triage` | `plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py` | `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html` | `PrivateRecruiterReplyTriageDocument` |
| `/private-recruiter-followthrough-checkpoint` | `plugins/professional-growth-coach/scripts/render_private_recruiter_followthrough_checkpoint.py` | `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html` | `PrivateRecruiterFollowthroughCheckpointDocument` |
| `/private-recruiter-conversion-outcome` | `plugins/professional-growth-coach/scripts/render_private_recruiter_conversion_outcome.py` | `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html` | `PrivateRecruiterConversionOutcomeDocument` |
| `/recruiter-target-shortlist` | `plugins/professional-growth-coach/scripts/render_recruiter_target_shortlist.py` | `plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.html` | `RecruiterTargetShortlistDocument` |
| `/recruiter-target-decision-gate` | `plugins/professional-growth-coach/scripts/render_recruiter_target_decision_gate.py` | `plugins/professional-growth-coach/assets/recruiter-target-decision-gate-v1.html` | `RecruiterTargetDecisionGateDocument` |
| `/recruiter-target-screen-intake` | `plugins/professional-growth-coach/scripts/render_recruiter_target_screen_intake.py` | `plugins/professional-growth-coach/assets/recruiter-target-screen-intake-v1.html` | `RecruiterTargetScreenIntakeDocument` |
| `/private-recruiter-screen-debrief` | `plugins/professional-growth-coach/scripts/render_private_recruiter_screen_debrief.py` | `plugins/professional-growth-coach/assets/private-recruiter-screen-debrief-v1.html` | `PrivateRecruiterScreenDebriefDocument` |
| `/private-recruiter-next-stage-review` | `plugins/professional-growth-coach/scripts/render_private_recruiter_next_stage_review.py` | `plugins/professional-growth-coach/assets/private-recruiter-next-stage-review-v1.html` | `PrivateRecruiterNextStageReviewDocument` |

## Key artifact summaries

- **Executive career dossier:** a private strategic LinkedIn analysis with an executive verdict, scorecard, priorities, copy studio, evidence/limits, and printable document treatment. The v2 renderer keeps the verdict and recruiter scan together, then adds a localized reading-path landmark with sticky, nearest-target fragment links through coverage, priorities, market evidence, and first-conversation preparation; hash and keyboard navigation update the active state, while the no-script fallback is static and keyboard-visible. Its unavailable-market state includes a static next-research panel with bounded scope, a five-employer sample target, official employer/ATS source priority, and access-date requirement; it stays read-only. With dated context it renders separate vacancy cards with location/arrangement/source context, alignment coverage/band, per-vacancy access/publication freshness, and a passive accessible link whose name includes the vacancy title. Unknown dates remain explicitly unconfirmed; optional learning provenance stays separate. Eligibility and hiring fit are never inferred.
- **Recruiter practice session:** one-question private recruiter-screen rehearsal with state, prompt, rehearsal cues, evidence boundaries, and feedback states.
- **Private recruiter reply triage:** a closed decision card that communicates safe next steps and, when applicable, a manual preparation handoff.
- **Follow-through checkpoint:** a compact candidate-supplied state, next measurement event, date, and safe-next-step receipt.
- **Conversion outcome:** a compact candidate-supplied observed-event receipt with evidence count and safe-next-step boundary.
- **Recruiter target shortlist:** a private three-to-six-target review batch; explicit network intent runs builder → validator → renderer and returns a validated artifact plus private HTML, while missing context yields one intake question. First-conversation wording (`initial interview`, `first call`, `entrevista inicial`, `primera llamada`) and defined articles, including `I have an interview with the recruiter` / `tengo una entrevista con la reclutadora`, route to the same intake. Explicit `never`/`nunca` non-completion wording, including `never went`, `didn't go`, `never went through`, `never spoke`, named future weekday/month dates, `nunca fui`, `no fui`, `no me presenté`, `no hablé`, and `nunca pasé por`, routes to screen preparation instead of post-screen debrief, while `had no trouble/questions` and a completed screen followed by `not yet ready for the next stage` remain post-screen language. Action synonyms such as `respond`, `email`, `contestar`, `enviar`, and `mandar` preserve the authorization requirement on fallback routes. The rail labels the current item as the current review surface while retaining `aria-current="step"` without implying completed progress.
- **Recruiter target decision gate:** a private decision brief bound to a validated shortlist snapshot; it reconciles four decision states, shows the next safe input, and exposes only a manual `prepare-role-interviews` review handoff.
- **Recruiter target screen intake:** a target-specific, four-check bridge that requires vacancy requirements, candidate fact IDs, company evidence, and a stated stage before any manual interview-preparation review.
- **Private recruiter screen debrief:** a post-`screen_attended` structured coverage brief that records unknowns and a manual next-stage decision without retaining raw conversation text.
- **Private recruiter next-stage review:** an explicit forward-stage checklist derived from a debrief; its header shows current stage → target stage, and blocked reviews list only the structured topics to clarify. It remains ready/blocked and manual-only.

Both compact receipt routes use the same static continuity semantics (`recorded`
then `pending` then `blocked`) and expose exactly one current step to assistive
technology; terminal stop receipts remain recorded.

The five recruiter target artifacts use a separate shared orientation rail with
closed localized labels: shortlist, decision gate, screen intake, screen
debrief, and next-stage review. Exactly one item, the rendered artifact's
surface, carries `aria-current="step"`; the rail is non-interactive and makes no
claim that other surfaces are complete. It is rendered by
`scripts/recruiter_continuity_rail.py` and must remain identity-free and
offline-safe in screen, print, responsive, and forced-colors modes.

Practice and triage routes now share that state vocabulary for their private
handoffs, so users can scan evidence already recorded and the one safe next
step without losing the read-only boundary.

No router config file exists, so there is no router source to include. All renderer CLIs keep local artifact paths out of successful receipts by default; a trusted caller that needs a verified local link must pass `--include-artifact-path`. Unknown arguments use the same fixed opaque diagnostic boundary and never echo rejected values.

For the recruiter handoff chain, route functions return `artifact` plus
private in-memory `rendered_html` only when a validated artifact exists. The
decision gate, screen intake, post-screen debrief, and next-stage review share
this contract; invalid intake remains artifact-free but includes fixed
`evidence_gaps` and one localized `intake_question` so the next safe input is
clear. Recovery copy is route-specific: screen intake asks for stage,
`V-###` requirements, `F-###` facts, company evidence, and four checks; debrief
intake first carries a validated checkpoint, either supported receipt event
(`screen_requested` or `interview_requested`), and target intake forward and
asks only for structured coverage; full debrief recovery asks for
checkpoint, receipt, intake, and structured coverage; next-stage asks
for a valid debrief and forward stage. A complete debrief with an invalid
non-terminal stage returns `select_forward_stage` with taxonomy-derived
`allowed_next_stages` instead of repeating the debrief request; `offer_stage`
is terminal and returns `record_terminal_stage` with no allowed stage. Recovery
text never echoes rejected values. The HTML is a review surface, not a public
serialization format, and keeps IDs, snapshots, contact details, URLs, and
external actions out of the rendered document.

The embedded recruiter snapshots are closed contracts in both JSON Schema and
runtime validation: unknown fields in shortlist, gate, intake, receipt,
checkpoint, or debrief envelopes are rejected. Schema conditionals mirror the
decision/event/safe-action rules and the forward-stage matrix; hashes, dates,
and cross-artifact equality still require the runtime validator. Schema
acceptance alone never authorizes preparation or an external action.
