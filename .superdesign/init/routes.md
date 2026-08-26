# Routes

## Routing model

This plugin exposes no HTTP routes, SPA routes, framework page files, or router configuration. The UI surfaces are offline HTML artifacts rendered by Python commands. The logical paths below are documentation handles only, **not runtime URLs**.

| Logical artifact | Renderer entry | Template | Layout |
| --- | --- | --- | --- |
| `/executive-career-dossier` | `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py` | `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html` | `ExecutiveCareerDossierDocument` |
| `/recruiter-practice-session` | `plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py` | `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html` | `RecruiterPracticeSessionDocument` |
| `/private-recruiter-reply-triage` | `plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py` | `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html` | `PrivateRecruiterReplyTriageDocument` |
| `/private-recruiter-followthrough-checkpoint` | `plugins/professional-growth-coach/scripts/render_private_recruiter_followthrough_checkpoint.py` | `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html` | `PrivateRecruiterFollowthroughCheckpointDocument` |
| `/private-recruiter-conversion-outcome` | `plugins/professional-growth-coach/scripts/render_private_recruiter_conversion_outcome.py` | `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html` | `PrivateRecruiterConversionOutcomeDocument` |

## Key artifact summaries

- **Executive career dossier:** a private strategic LinkedIn analysis with an executive verdict, scorecard, priorities, copy studio, evidence/limits, and printable document treatment. The v2 renderer keeps an honest unavailable-market state unless validated dated vacancy context is present, in which case it renders the separate comparison table and sanitized public sources.
- **Recruiter practice session:** one-question private recruiter-screen rehearsal with state, prompt, rehearsal cues, evidence boundaries, and feedback states.
- **Private recruiter reply triage:** a closed decision card that communicates safe next steps and, when applicable, a manual preparation handoff.
- **Follow-through checkpoint:** a compact candidate-supplied state, next measurement event, date, and safe-next-step receipt.
- **Conversion outcome:** a compact candidate-supplied observed-event receipt with evidence count and safe-next-step boundary.

No router config file exists, so there is no router source to include.
