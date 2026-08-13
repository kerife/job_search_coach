# Career market and learning dossier design

## Status

Proposed for client review. This revision incorporates the requested
five-vacancy default, real-sample recurrence, LinkedIn Jobs fallback, and
responsive five-column matrix. It does not change current market or learning
behavior until its implementation plan is approved.

## Problem

The LinkedIn dossier needs a current, auditable market comparison rather than
remembered postings or generic advice. It must research up to five active SRE,
Platform Engineering, or DevOps vacancies for Mexico or a compatible remote
arrangement, explain documented evidence alignment, expose recurring gaps over
the actual verified sample, and turn only supported gaps into learning options.

The report must remain useful when fewer than five vacancies can be verified.
It must never fill the sample with expired, duplicate, inaccessible, or
incompatible postings, and it must never treat remote wording as proof of work
authorization, geographic eligibility, internal mobility, or contractor/EOR
availability.

## Decision

Create:

- `target-vacancy-research-v1`, a closed normalized evidence contract; and
- `career-market-learning-dossier-v1`, a private offline client artifact built
  only from that validated research contract and the candidate fact matrix.

The complete default state contains exactly five verified active vacancies.
The artifact admits at most five vacancies. When only one through four qualify,
it renders a bounded limited state with those real vacancies, their individual
scores, an explicit limitation, and recurrence calculated over the actual
sample size `N`. Zero verified vacancies produces an unavailable state with no
vacancy scores, recurrence, or paid-learning recommendation.

## Alternatives considered

### Require five or render no market analysis

Rejected. It would avoid denominator variation but would discard useful,
verified evidence whenever the bounded search finds only one through four
current postings.

### Render the real verified sample up to five

Selected. Five is the complete target and maximum; one through four remains a
truthful limited result with independent vacancy scores and `k/N` recurrence.

### Allow an arbitrary or padded sample

Rejected. More than five weakens the requested bounded comparison, while
padding with duplicates, expired postings, incompatible roles, or empty
columns misrepresents the evidence.

## Employer and vacancy source hierarchy

The search prioritizes five distinct large or recognized employers. A vacancy
source uses this hierarchy:

1. the employer's current official career page;
2. an employer-operated applicant-tracking page linked to that employer;
3. LinkedIn Jobs as an explicitly labelled backup when the official posting is
   unavailable but the LinkedIn posting itself is open, role-matched, and
   inspectable on the access date.

LinkedIn Jobs is not silently promoted to an official employer source. Search
snippets, cached previews, aggregators, undated articles, and model memory are
discovery leads only and cannot enter the verified sample.

An employer is `large_recognized` only when a current official source proves
one of these conditions:

1. the latest official report or regulated filing, published within 18 months,
   reports at least 1,000 employees; or
2. an official list owner shows current membership in a named flagship
   national/global index or the Fortune Global 500.

Record qualification type, source issuer, source title, publication or access
date, official URL, and the observed headcount or list membership. A LinkedIn
company page, media snippet, search snippet, repost, or model memory does not
qualify the employer.

## Vacancy evidence

Each included vacancy records:

- stable local vacancy ID and duplicate fingerprint;
- vacancy-source state: `official_employer`, `employer_operated_ats`, or
  `linkedin_jobs_backup`;
- employer ID and employer-qualification reference;
- role title, geography, stated work arrangement, seniority, and language;
- public source URL, access date, and publication date when visible;
- `source_state=active` from a successfully opened role-matched page;
- `freshness_status=current|unknown` and the reason;
- explicit eligibility gates without inferred answers;
- normalized requirements, using bounded paraphrases rather than a raw
  vacancy dump; and
- evidence references used to score the vacancy.

An active posting with no visible publication date may be included with the
access date, `publication_date=unknown`, and `freshness_status=unknown`. The
artifact says that the posting was verified open on the access date but does
not imply when it was published. A closed, redirected-to-search,
snippet-only, inaccessible, stale, or incompatible posting is excluded.

## Five-vacancy default, distinct employers, and limited behavior

The bounded search continues until it finds five qualifying vacancies or
exhausts its documented search plan. It never pads with an expired posting, a
duplicate posting, an incompatible role, or an unverified source.

Distinct employers are preferred. The search first attempts five different
employers. A second genuinely different posting from the same employer may be
included only after that bounded distinct-employer search is exhausted. The
report discloses the number of unique employers and why distinct coverage was
limited. Two URLs or reposts for the same underlying requisition are always one
posting, not two.

Complete state:

- `state=complete`;
- exactly five distinct vacancy IDs and duplicate fingerprints;
- one through five employer IDs, with five preferred;
- every posting confirmed active on its access date; and
- an explicit count of five verified vacancies and the unique-employer count.

Limited state:

- `state=limited_market_evidence`;
- exactly one through four verified vacancies;
- every included vacancy is still scored independently;
- recurrence uses the actual denominator `N`;
- the report explains why the sample stopped below five; and
- it never claims that five matches or five employers were found.

Unavailable state:

- `state=market_evidence_unavailable`;
- zero verified vacancies;
- no vacancy percentage, recurring-gap claim, or course/certification
  recommendation; and
- one bounded explanation of the evidence limit.

## Eligibility gates

Eligibility is shown separately from evidence alignment. Gates cover:

- work authorization;
- country/geography;
- remote, hybrid, or onsite arrangement;
- mandatory language or location;
- seniority and explicit experience floor; and
- any explicitly stated employment arrangement.

Each gate is `pass`, `blocked`, or `unknown`. A blocked gate prevents the role
from being described as viable. An unknown gate requires confirmation and is
not a candidate deficit. The system never infers work authorization, internal
mobility, relocation, tax eligibility, contractor/EOR availability, or remote
compatibility from location labels alone. Eligibility never changes the
alignment arithmetic.

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

Each verified vacancy receives its own reproducible score, including vacancies
in a limited sample. There is no sample-wide fit score. The client label is
`Alineación de evidencia: N de 100` / `Evidence alignment: N out of 100`.
It is a directional mapping of documented evidence, not ATS rank, recruiter
preference, compatibility prediction, application success, interview
probability, or hiring guarantee. When evidence coverage is below 50, suppress
the qualitative band and render `insufficient_evidence`.

Each vacancy separates:

- verified and candidate-reported matches;
- adjacent evidence;
- confirmed gaps;
- items to confirm; and
- blocked and unknown eligibility gates.

## Actual-sample recurrence

Let `N` be the number of verified vacancies included in the report, where
`1 <= N <= 5`. For each normalized requirement, recurrence is `k/N`, where `k`
is the number of included vacancies that explicitly request that exact
normalized requirement. The artifact shows both `k/N` and the access date.

Provider-specific terms remain distinct unless the same normalized requirement
actually repeats. For example, AWS/EKS and Azure/AKS do not become a generic
cloud recurrence merely to inflate `k`. The report describes recurrence only
inside this sample and never generalizes it to the labor market.

## Accessible visualizations and five-column matrix

Each of the `N` vacancy cards uses a horizontal zero-based bar implemented with
native progress semantics and a visible text equivalent:

```html
<h3 id="vacancy-title-1">...</h3>
<p id="vacancy-score-1">Alineación de evidencia: 68 de 100</p>
<progress value="68" max="100"
  aria-labelledby="vacancy-title-1 vacancy-score-1">68/100</progress>
```

The requirement-by-evidence matrix is authoritative. In the complete state it
has five labelled vacancy columns, plus row/evidence context. In a limited
state it has exactly `N` vacancy columns and no empty padding columns. Duplicate
postings cannot create duplicate columns.

Desktop keeps the five vacancy columns readable within the dossier width.
Mobile preserves the semantic table relationships while presenting each
requirement as a labelled stacked block; horizontal scrolling is not the only
way to access content. Print repeats or preserves column labels, prevents
clipping, and keeps each requirement row understandable in grayscale. Every
cell has a text state (`verified`, `adjacent`, `unknown`, or `required`) and
does not rely on color, hover, animation, canvas, SVG, JavaScript, or remote
assets.

The recurrence view uses zero-based bars or discrete labelled units with the
exact `k/N` value. It is not a market-demand chart. The visual route for closing
gaps contains four fixed stages—clarify evidence, build proof, learn toward a
specific requirement, and measure again—and acts as an index rather than
duplicating the three coach-priority cards.

## Learning decision contract

Learning decisions are created only from normalized requirements in the
actual verified sample. Study topics and free evidence-building resources may
be source-specific, but they are labelled as such when the requirement appears
in only one vacancy.

A paid course or certification requires a recurring learnable gap in a sample
of at least two vacancies. The recurrence threshold is the strict majority:

```text
required_recurrence = max(2, floor(N / 2) + 1)
```

This yields `2/2`, `2/3`, `3/4`, or `3/5`; `N=1` cannot support paid learning.

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
- direct application with an honest boundary; and
- `do_nothing`.

Each provider option uses a current official source and records provider,
issuer, offering title, official URL, access date, cost and currency or
unknown, tax treatment or unknown, estimated duration, prerequisites,
renewal/maintenance, Mexico availability/eligibility, and the exact recurring
gap it addresses.

Acceptable provider categories include accredited universities, official
vendor certification programs, and reputable platforms carrying an identified
university or vendor offering. A platform brand by itself is not evidence of
quality. Harvard, other universities, Coursera-hosted university programs, and
official certifications are eligible only after their current official source
and fit to the recurring gap are verified.

A paid option is `recommended` only when:

1. the exact learnable gap reaches the recurrence threshold;
2. provider evidence is current;
3. candidate time and budget fit are known; and
4. no cheaper proof or project path has better expected evidence value.

Other decisions are `consider`, `pause`, `project_first`,
`apply_with_boundary`, or `not_needed`. A certification never substitutes for
production experience. Unknown price, prerequisites, availability, budget, or
time remain visible unknowns. The artifact never enrolls, purchases, schedules,
applies, or publishes anything.

## Information architecture

The client artifact follows this order:

1. verdict, target roles, geography/arrangement scope, and access date;
2. verified vacancy count, unique-employer count, source states, and limits;
3. exactly five vacancy cards in complete state or `N` cards plus one limited
   explanation in limited state;
4. requirement-by-evidence matrix with up to five vacancy columns;
5. recurring gaps over the actual denominator `N`;
6. confirmed gaps versus items to confirm;
7. learning ROI decisions and cheaper proof alternatives; and
8. official sources, methodology, limitations, and no-external-action footer.

The main LinkedIn dossier may render a bound snapshot of these cards, matrix,
and learning decisions, but it never recomputes them. The detailed market
artifact retains source dates and methodology.

## Privacy and safety

- Candidate facts are paraphrased and identity-free.
- No candidate name, contact, profile URL, local path, confidential employer
  detail, raw profile text, raw analytics record, or raw vacancy dump is
  rendered.
- No browsing action applies, messages, connects, follows, schedules, enrolls,
  purchases, or publishes.
- Current-market claims use public sources opened during the run and preserve
  their access dates and source states.
- External action requires a later exact action, target, and final-content
  authorization.

## Failure behavior

- Network or browser failure yields the limited or unavailable state; cached
  snippets are not promoted.
- A stale, closed, duplicate, or incompatible vacancy is discarded and
  replaced only by another verified posting.
- A malformed research or learning contract fails closed with bounded
  non-echoing diagnostics.
- Course-source failure suppresses the recommendation rather than substituting
  a remembered or invented course.

## Acceptance criteria

1. Complete output has exactly five active unique postings and prefers five
   distinct objectively qualified employers.
2. Every employer has official qualification evidence; every vacancy has an
   active official/ATS source or an explicitly labelled active LinkedIn Jobs
   backup, plus an access date.
3. Duplicate, expired, inaccessible, stale, and incompatible postings never
   enter the sample.
4. Limited output with one through four vacancies scores only those verified
   postings, explains the limit, and uses the actual denominator `N`.
5. Eligibility gates are separate from alignment and are never inferred from
   remote or location wording.
6. Score arithmetic is deterministic and reconciles to normalized requirements;
   unknown requirements are not called candidate deficits.
7. Recurrence is exactly `k/N` over the included sample and is never presented
   as a broad market-demand claim.
8. Complete-state HTML contains five labelled vacancy bars and five readable
   vacancy columns; mobile and print preserve labels, text states, and reading
   order without relying only on horizontal scrolling or color.
9. Paid learning requires the strict-majority recurring learnable gap, current
   official provider evidence, known time/budget fit, and no better cheaper
   evidence path.
10. V1 remains valid; v2 values are structured and dynamic rather than
    candidate-, employer-, vacancy-, or percentage-specific constants.
11. Static, privacy, source, release, renderer, accessibility, responsive,
    print, dark, forced-colors, plugin, root, source-cache parity, and provenance
    gates pass before publication. Empirical desktop/mobile/print/AT QA is
    recorded separately and never inferred from static checks.
