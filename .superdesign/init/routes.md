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

## Key artifact summaries

- **Executive career dossier:** a private strategic LinkedIn analysis with an executive verdict, scorecard, priorities, copy studio, evidence/limits, and printable document treatment. The v2 renderer keeps the verdict and recruiter scan together, then adds a localized reading-path landmark with sticky, nearest-target fragment links through coverage, priorities, market evidence, and first-conversation preparation; hash and keyboard navigation update the active state, while the no-script fallback is static and keyboard-visible. Its unavailable-market state includes a static next-research panel with bounded scope, a five-employer sample target, official employer/ATS source priority, and access-date requirement; it stays read-only. With dated context it renders separate vacancy cards with location/arrangement/source context, alignment coverage/band, per-vacancy access/publication freshness, and a passive accessible link whose name includes the vacancy title. Unknown dates remain explicitly unconfirmed; optional learning provenance stays separate. Eligibility and hiring fit are never inferred.
- **Recruiter practice session:** one-question private recruiter-screen rehearsal with state, prompt, rehearsal cues, evidence boundaries, and feedback states.
- **Private recruiter reply triage:** a closed decision card that communicates safe next steps and, when applicable, a manual preparation handoff.
- **Follow-through checkpoint:** a compact candidate-supplied state, next measurement event, date, and safe-next-step receipt.
- **Conversion outcome:** a compact candidate-supplied observed-event receipt with evidence count and safe-next-step boundary.

Both compact receipt routes use the same static continuity semantics (`recorded`
then `pending` then `blocked`) and expose exactly one current step to assistive
technology; terminal stop receipts remain recorded.

Practice and triage routes now share that state vocabulary for their private
handoffs, so users can scan evidence already recorded and the one safe next
step without losing the read-only boundary.

No router config file exists, so there is no router source to include. All renderer CLIs keep local artifact paths out of successful receipts by default; a trusted caller that needs a verified local link must pass `--include-artifact-path`. Unknown arguments use the same fixed opaque diagnostic boundary and never echo rejected values.
