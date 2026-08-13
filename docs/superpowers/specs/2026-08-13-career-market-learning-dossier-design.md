# Career market and learning dossier design

## Status

Proposed for client review. This is a new evidence contract and artifact; it
does not change current market or learning behavior until an implementation
plan is approved.

## Problem

The current LinkedIn dossier can record a small dated market sample, but it
does not prove that three current vacancies come from large recognized
employers, does not calculate a transparent evidence-alignment percentage, and
does not distinguish confirmed gaps from unknowns. It also has no auditable
course, certification, or study-topic decision surface.

## Decision

Create:

- `target-vacancy-research-v1`, a closed normalized evidence contract; and
- `career-market-learning-dossier-v1`, a private offline client artifact built
  only from the validated research contract and the candidate fact matrix.

A complete default run contains exactly three active vacancies from exactly
three distinct large recognized employers. If three cannot be verified, the
artifact returns `blocked_on_market_evidence` with the verified subset and no
fabricated scores or paid-learning recommendation.

## Employer qualification

An employer is `large_recognized` only when one current official source proves
one of these conditions:

1. latest official report or regulated filing, published within 18 months,
   reports at least 1,000 employees; or
2. an official list owner shows current membership in a named flagship
   national/global index or the Fortune Global 500.

Record qualification type, source issuer, source title, publication or access
date, official URL, and the observed headcount or list membership. Media
snippets, search result snippets, reposts, job aggregators, and model memory do
not qualify an employer.

## Vacancy evidence

Each selected vacancy records:

- stable local vacancy ID;
- direct official employer career or employer-operated ATS URL;
- employer ID and qualification reference;
- role title, geography, work arrangement, seniority, and language;
- access date and publication date when available;
- `active_state=confirmed_active` from a successfully opened official page;
- freshness `fresh_30d` or `publication_date_unknown`;
- eligibility gates;
- normalized requirements with source excerpts paraphrased into bounded text.

An official active page with an unavailable publication date may be included
as `publication_date_unknown`; the artifact must say freshness is unknown and
must not imply it was posted recently. A closed, redirected-to-search, cached,
snippet-only, inaccessible, or reposted vacancy is excluded.

## Exactly-three default and incomplete behavior

The default search continues until it finds three qualifying vacancies or
exhausts a bounded search plan. It never pads with duplicate employers,
expired roles, snippets, or invented jobs.

Complete state:

- exactly three distinct vacancy IDs;
- exactly three distinct qualifying employer IDs;
- all three official pages confirmed active on the access date.

Incomplete state:

- `state=blocked_on_market_evidence`;
- zero to two verified vacancies may be described;
- no overall percentage is rendered for an unverified vacancy;
- no claim that three matches were found;
- no paid course or certification recommendation.

## Eligibility gates

Eligibility is shown separately from evidence alignment. Gates cover:

- work authorization;
- country/geography;
- remote or onsite arrangement;
- mandatory language or location;
- seniority and explicit experience floor.

Each gate is `pass`, `blocked`, or `unknown`. A blocked gate prevents the role
from being described as viable. An unknown gate requires confirmation and is
not a deficit. Eligibility never changes the alignment arithmetic.

## Requirement normalization and alignment score

Requirements are classified as:

- `must_have`, weight 2;
- `preferred`, weight 1;
- `responsibility_only`, weight 0 and display-only.

Candidate support states are:

- `verified_match`, factor 1;
- `candidate_reported_match`, factor 1 and visibly labelled;
- `adjacent_evidence`, factor 0.5;
- `explicit_gap`, factor 0;
- `unknown`, factor 0 but never described as missing.

For scoreable requirements:

```text
W = sum(requirement_weight)
directional_evidence_alignment =
  round(100 * sum(requirement_weight * support_factor) / W)
evidence_coverage =
  round(100 * sum(requirement_weight where state != unknown) / W)
```

The client label is `Alineación de evidencia: N de 100` / `Evidence
alignment: N out of 100`. It is a directional mapping of documented evidence,
not ATS rank, recruiter preference, application success, interview probability,
or fit guarantee. When evidence coverage is below 50, suppress the qualitative
band and render `insufficient_evidence`.

Each vacancy separates:

- verified and candidate-reported matches;
- adjacent evidence;
- confirmed gaps;
- items to confirm;
- blocked and unknown eligibility gates.

## Accessible charts

Each of the exactly three cards uses native progress semantics and a visible
text equivalent:

```html
<h3 id="vacancy-title-1">...</h3>
<p id="vacancy-score-1">Alineación de evidencia: 68 de 100</p>
<progress value="68" max="100"
  aria-labelledby="vacancy-title-1 vacancy-score-1">68/100</progress>
```

The requirement table/list remains the authoritative explanation. Charts do
not depend on canvas, SVG, JavaScript, hover, animation, or color alone.
Forced-colors uses system Canvas, CanvasText, and Highlight. Print keeps each
card and its score explanation together.

## Learning decision contract

Learning decisions are created only from normalized requirements in the three
validated vacancies. A paid course or certification can be recommended only
when the exact requirement recurs in at least two of the three roles.

Classify each need as:

- `terminology_mismatch`;
- `knowledge_gap`;
- `proof_gap`;
- `professional_experience_gap`;
- `low_return`.

Before recommending paid learning, compare:

- course;
- certification;
- lab or portfolio project;
- existing asset rewrite;
- direct application with honest boundary;
- `do_nothing`.

Each provider option uses a current official source and records provider,
issuer, offering title, official URL, access date, cost and currency or
unknown, tax treatment or unknown, estimated duration, prerequisites,
renewal/maintenance, Mexico availability/eligibility, and the exact recurring
gap it addresses.

Acceptable provider categories include accredited universities, official
vendor certification programs, and reputable learning platforms carrying an
identified university or vendor offering. The platform name alone is not
evidence of quality.

A paid option is `recommended` only when:

1. the gap recurs in at least two vacancies;
2. the gap is learnable rather than a professional-experience deficit;
3. provider evidence is current;
4. candidate time and budget fit are known; and
5. no cheaper proof or project path has better expected evidence value.

Other decisions are `consider`, `pause`, `project_first`, `apply_with_boundary`,
or `not_needed`. Unknown price, prerequisites, availability, budget, or time
remain visible unknowns. The artifact never enrolls, purchases, schedules, or
publishes anything.

## Information architecture

The client artifact follows this order:

1. verdict and search scope;
2. employer qualification and freshness summary;
3. exactly three vacancy cards or one bounded incomplete state;
4. cross-vacancy repeated-requirement matrix;
5. confirmed gaps versus items to confirm;
6. learning ROI decisions and cheaper alternatives;
7. official sources, limitations, and no-external-action footer.

The main LinkedIn dossier may render the three cards and learning decisions as
a bound snapshot, but it never recomputes them. The detailed market artifact
retains source dates and methodology.

## Privacy and safety

- Candidate facts are paraphrased and identity-free.
- No candidate name, contact, profile URL, local path, confidential employer
  detail, raw profile text, or raw vacancy dump is rendered.
- No browsing action applies, messages, connects, follows, schedules, enrolls,
  or purchases.
- Current-market claims use official primary sources opened during the run.
- External action requires a later exact action, target, and final-content
  authorization.

## Failure behavior

- Network or browser failure yields bounded incomplete state; cached snippets
  are not promoted.
- A stale or closed vacancy is discarded and replaced only by another verified
  official vacancy.
- A malformed research or learning contract fails closed with bounded
  non-echoing diagnostics.
- Course-source failure suppresses the recommendation rather than substituting
  a remembered or invented course.

## Acceptance criteria

1. Complete output has exactly three active vacancies and three distinct
   objectively qualified employers.
2. Every employer and vacancy has current official source evidence.
3. Eligibility gates are separate from alignment scores.
4. Score arithmetic is deterministic, testable, and reconciles to normalized
   requirements.
5. Unknown requirements are not called candidate deficits.
6. Evidence coverage below 50 suppresses qualitative interpretation.
7. All three charts have visible text, native progress semantics, and labelled
   requirement explanations in EN and ES.
8. Paid learning requires a recurring 2-of-3 learnable gap, current provider
   evidence, known time/budget fit, and no better cheaper evidence path.
9. Fewer than three verified vacancies produces bounded incomplete state with
   no fabricated score or paid recommendation.
10. Static, privacy, source, official-release, renderer, accessibility, print,
    dark, forced-colors, plugin, root, source-cache parity, and provenance gates
    pass before publication; empirical browser QA is reported separately.
