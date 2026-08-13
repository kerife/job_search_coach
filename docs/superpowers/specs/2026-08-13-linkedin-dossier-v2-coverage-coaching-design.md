# LinkedIn dossier v2 coverage and coaching design

## Status

Approved for implementation. This design supersedes only the coverage,
authorization, and priority-copy portions of `executive-career-dossier-v1`.
The v1 schema, validator, renderer, fixtures, and installed behavior remain
unchanged until the implementation plan is approved and completed.

## Problem

The current dossier can render an honest partial analysis, but it compresses
profile evidence into broad dimensions. A client cannot reliably tell which
LinkedIn sections were inspected, which were absent, and which still need
read-only inspection authorization. The three priorities also omit the named
profile section and enough conversational context to feel like a coach is
speaking directly to the client.

## Decision

Create `executive-career-dossier-v2` as a versioned contract. Do not mutate v1
in place. V2 adds a complete section-decision ledger and contextual coaching
priorities while preserving the evidence, privacy, scoring, print, and
no-external-action boundaries already enforced by v1.

The client-facing report package uses two independently validated data
contracts:

1. `executive-career-dossier-v2` owns LinkedIn coverage, authorization,
   evidence, profile scoring, and coach priorities.
2. `career-market-learning-dossier-v1` owns current vacancies, directional
   evidence alignment, gaps, and learning decisions.

The main v2 HTML may render a snapshot of up to five validated vacancy cards,
the actual-sample matrix, and learning decisions, but those values remain bound
to the second contract.
Market alignment never changes the seven-dimension LinkedIn score. Chat may
return both private artifact links; the main dossier remains understandable on
its own.

## Alternatives considered

### Expand v1 in place

Rejected. It would make current fixtures and installed artifacts ambiguous and
would mix a breaking schema change into an established release contract.

### Put all market research directly in the LinkedIn schema

Rejected. Vacancy freshness, employer qualification, eligibility, and course
sources have different evidence lifecycles from a profile inspection.

### Separate contracts with one composed client summary

Selected. It keeps each validator bounded while satisfying the expectation of
one decision-led report.

## Canonical LinkedIn section ledger

V2 contains exactly these 17 section keys, exactly once and in this order:

1. `photo`
2. `banner`
3. `name`
4. `profile_url`
5. `headline`
6. `location`
7. `contact_info`
8. `about`
9. `experience`
10. `skills`
11. `featured`
12. `certifications`
13. `education`
14. `recommendations`
15. `activity`
16. `analytics`
17. `job_preferences`

The report names the section, never its private value. In particular, the
artifact never renders a profile URL, contact detail, private analytics value,
job-preference value, name, or raw profile text.

Each ledger row contains:

- `section`: one canonical key;
- `availability`: `inspected_present`, `inspected_absent`,
  `candidate_supplied`, or `unavailable`;
- `evidence_state`: `verified`, `candidate_reported`, `inferred`, or
  `unknown`;
- `reason`: fixed localized reason text or a closed reason enum mapped to fixed
  copy;
- `inspection_request`: absent unless `availability=unavailable`.

An unavailable row has exactly one inspection request:

- `access_type=read_only_visible_section_inspection`;
- `decision=pending_response|declined_for_session|authorized_inspection_failed`;
- `scope=current_session_only`;
- `carry_forward=false`.

The serialized ledger is a status record, not proof of consent. The positive
authorization event exists only in the current conversation turn and is never
written to the JSON or HTML. After an explicit client answer, the orchestrator
immediately attempts read-only inspection of that one named section. Success
replaces the row with `inspected_present` or `inspected_absent` and removes the
request. Failure leaves the row unavailable with
`decision=authorized_inspection_failed` and a fixed failure reason. A copied
report therefore cannot act as reusable authorization.

Authorization is section-specific and applies only to the current session. It
does not authorize editing, messaging, connecting, following, applying,
exporting, posting, uploading, downloading, or retaining raw profile content.
Authorization is never inferred from a previous report, a serialized field, or
another section. The validator enforces the persisted state matrix; the skill
orchestrator enforces that the positive answer came from the active
conversation before attempting inspection.

`inspected_absent` means the section was inspected and was not present; it does
not create another authorization request. Pending or declined inspection does
not invalidate a partial report and does not score the section as zero.

## Conversation behavior

The artifact shows every unavailable section and its current-session decision.
The chat response asks at most one question: the highest-priority pending
inspection authorization that can materially change the recommendation. After
the client answers, the next pending section may be requested. The agent never
answers the authorization question on the client's behalf.

Priority is deterministic: inspect priorities in rank order and select the
first pending `target_section`; if none of the three priorities targets a
pending section, select the first pending section in canonical ledger order.
Never emit this authorization question together with the existing rank-one
content question.

When no section is inspectable or supplied, keep the existing rule: ask one
useful intake or inspection-authorization question and do not create an empty
dossier.

## Contextual coach priorities

`priorities` remains exactly three items. Every item adds:

- `target_section`: one canonical LinkedIn section;
- `coach_observation`: evidence-bound, conversational explanation;
- `why_it_matters`: bounded client consequence without outcome prediction;
- `coach_prompt`: one direct next prompt to the client;
- `client_template`: one closed template ID plus one to five enumerated field
  keys; the renderer owns the localized blank labels;
- `done_when`: observable private review criterion;
- `evidence_ids`: same-section evidence only;
- `privacy_boundary`: fixed no-raw-text/no-private-values boundary.

Spanish copy follows this shape:

> En la sección **Experiencia**, mencionas una capacidad relevante, pero aún
> no aparece un ejemplo que permita entender el resultado. Completa esta
> plantilla para que podamos convertirlo en una evidencia revisable.

The equivalent English copy uses the same coach-to-client structure. The
renderer displays natural evidence paraphrases and section labels, never
internal IDs or raw enum values. Templates are static copyable text, not forms,
editable controls, local storage, or persisted answers.

Each v2 evidence item adds `profile_section`, containing one canonical section
or `null` when the evidence is not attributable to a single LinkedIn section.
Same-section priority binding uses this field. Projection to v1 removes it and
all v2-only priority fields without mutating the source object.

## Information architecture

The selected visual direction combines the decision-led Superdesign variant
with the conversational coach-card variant:

1. private header, verdict, evidence date, and honest coverage state;
2. complete per-section coverage and authorization ledger;
3. exactly three section-named coach priority cards with blank templates;
4. existing profile score, visual review, safe copy studio, and boundaries;
5. in this first increment, one bounded market-evidence-unavailable state with
   no percentage, vacancy card, or paid-learning decision;
6. in the later composed release, exactly five validated market cards in the
   complete state or the real one-to-four-card limited state, with learning
   decisions derived only from the separate market contract;
7. evidence, methodology, limitations, and no-external-action footer.

At 320px, the ledger becomes one stacked row-card per section rather than a
wide table. Important decisions are not hidden inside closed `details`
elements. Print preserves each ledger row, priority, vacancy, and learning
decision atomically where practical.

The Superdesign drafts are layout references only. Their fabricated metrics,
employer claims, course claims, outcome promises, JavaScript, and unsupported
authorization controls are explicitly rejected.

## Privacy and safety

- Keep candidate isolation and generic private filenames.
- Keep raw profile text, identity, URLs, contacts, private analytics, and local
  paths out of artifacts and diagnostics.
- Inspection authorization is not consent for analytics; dated aggregate
  analytics keeps its separate explicit consent gate.
- No profile or market recommendation authorizes an external action.
- No generated text promises search ranking, replies, interviews, offers,
  compensation, or time-to-hire.
- No remote assets, network requests, forms, external scripts, or relaxed CSP.

## Failure behavior

- Invalid or incomplete v2 input fails closed with bounded non-echoing
  diagnostics.
- One repair is allowed before existing localized Markdown fallback behavior.
- A market artifact failure leaves the LinkedIn dossier valid and renders an
  honest `market_evidence_unavailable` state; it never fabricates five cards or
  pads a limited sample.
- A LinkedIn inspection failure preserves prior validated findings and records
  only a fixed unavailable reason.

## Acceptance criteria

1. The schema and validator require all 17 section rows exactly once.
2. Every unavailable row carries a non-reusable current-session request state;
   every other row forbids it, and a positive answer is never serialized.
3. Pending and declined rows never enter the score denominator as zero.
4. Chat asks no more than one pending authorization question per turn.
5. Exactly three priorities name their section, use coach-style prose, and
   provide one to five blank template fields.
6. Same-section evidence binding is validated.
7. EN and ES renders expose no internal IDs, raw enums, identity, profile URL,
   contact detail, raw text, private analytics, or local path.
8. Representative 320px, dark, forced-colors, reduced-motion, high-contrast,
   and print contracts pass static and renderer tests; empirical browser QA is
   reported separately and is not inferred from static checks.
9. Existing v1 fixtures and behavior remain valid.
10. Source, installed cache, provenance, privacy, static, plugin, and root
    release gates pass before publication.

## First-increment boundary

This v2 increment ships coverage, authorization-state rendering, and coach
priorities only. It does not implement vacancy scoring or learning decisions.
Those surfaces remain unavailable until the independent
`career-market-learning-dossier-v1` contract is validated and bound to the v2
snapshot. Generic public HTTPS validation is not proof that a vacancy,
employer, ATS, or course source is official.
