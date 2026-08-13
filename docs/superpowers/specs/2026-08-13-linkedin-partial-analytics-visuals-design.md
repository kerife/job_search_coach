# LinkedIn partial aggregate analytics visuals design

## Status

Approved for implementation from the supplied analytics requirements. This
design replaces candidate-specific mockup values with a closed reusable
contract. It does not authorize another LinkedIn inspection by itself and does
not change the separate five-vacancy or learning contracts.

## Problem

The current dossier supports either no analytics or one all-or-nothing
aggregate record containing profile views, inbound contacts, qualified
contacts, and a rate. LinkedIn may expose only some aggregates—for example,
profile views and the subset classified as recruiters—without comparable
contact counts. The current contract cannot preserve those available measures,
and the renderer has no honest composition view for compatible subsets.

The user-provided current values are run-time evidence to re-confirm, not
constants to embed. No candidate, metric, window, percentage, or date may be
hardcoded into the renderer or skill.

## Decision

Create `executive-career-dossier-v3` after the coverage/coaching v2 increment is
published. Keep v1 and v2 unchanged. V3 inherits the complete v2 coverage and
coaching contract and replaces only its analytics branch with a versioned
aggregate contract that supports:

- `not_requested`;
- `unavailable`;
- `observed_partial`; and
- `observed_complete`.

V3 projects first to v2 for coverage/coaching validation and then to v1 for
legacy profile validation. A complete V3 analytic observation converts to the
legacy v1 aggregate shape only when every legacy metric exists and reconciles.
Partial V3 analytics projects to the v2/v1 `unavailable` branch with one fixed
reason so earlier validators cannot accidentally consume missing fields. V3
semantic validation remains authoritative for the partial observation, and
analytics never affects the seven profile dimensions or their denominator.

## Consent and data minimization

Any observed branch requires:

- `explicit_report_consent=true` for this report;
- `observed_as_of`;
- `raw_records_retained=false`;
- `causality_boundary=observed_not_attributed`;
- one or more aggregate observations; and
- analytics evidence IDs bound only to consented aggregate evidence.

Never retain or render visitor identities, company identities, message text,
contacts, screenshots, cookies, session data, profile URLs, local paths, raw
records, or small-location breakdowns. Read-only profile-section authorization
does not grant analytics consent. Consent is not reusable authorization for a
future report.

## Observation model

An observed analytics object contains:

```json
{
  "state": "observed_partial",
  "explicit_report_consent": true,
  "observed_as_of": "2026-08-13",
  "raw_records_retained": false,
  "observations": [
    {
      "metric": "profile_views",
      "value": 41,
      "window_id": "WINDOW-001",
      "window_days": 90
    },
    {
      "metric": "recruiter_viewers",
      "value": 9,
      "window_id": "WINDOW-001",
      "window_days": 90
    }
  ],
  "evidence_ids": ["E-020"],
  "causality_boundary": "observed_not_attributed"
}
```

The example values above are illustrative input only. Fixtures use synthetic
values; a live report uses only values re-confirmed in the current authorized
inspection.

Allowed metrics are:

- `profile_views`;
- `recruiter_viewers`;
- `inbound_contacts`; and
- `qualified_contacts`.

Each metric appears at most once. Values are non-negative integers. A
`window_id` is a dossier-local non-secret identifier matching
`^WINDOW-[0-9]{3}$`; all observations used together must have the same
`window_id`, `window_days`, and `observed_as_of`. A partial branch contains one
through three allowed metrics and omits at least one. A complete branch contains
all four.

`recruiter_viewers <= profile_views` when both exist.
`qualified_contacts <= inbound_contacts` when both exist. A qualified-contact
rate exists only as a derived value when both contact counts share the window
and `inbound_contacts > 0`; when inbound is zero, render the counts and state
that no rate is calculable. Rates are never accepted from caller input.

## Derived descriptive composition

The segmented profile-view composition is available only when both
`profile_views` and `recruiter_viewers` share the same date, window ID, and
window length.

```text
other_views = profile_views - recruiter_viewers
recruiter_share_percent =
  0 when profile_views = 0
  otherwise round(100 * recruiter_viewers / profile_views)
```

Use integer half-up arithmetic, not floating-point display artifacts. The
rendered visible text includes exact counts, the rounded proportion, window,
and observation date. The chart is descriptive only:

- recruiter-classified views are not inbound contacts;
- they do not measure contact quality or conversion;
- they do not identify individuals; and
- they do not prove that profile changes caused the observation.

If the two metrics are missing or incomparable, omit the segmented bar and
render a fixed availability limit. Do not substitute zeros, estimated values,
or a remembered ratio.

## Information architecture and no duplication

Keep the existing two-card analytics region:

1. **Private analytics** shows only authorized observed KPI values, the common
   window, and observation date.
2. **Impact, quality, and boundary** shows the segmented composition when
   comparable, any derived qualified-contact rate when valid, and one concise
   causal/quality boundary.

Do not repeat the same percentage in a chart, table, and paragraph. The visible
chart label is the accessible text equivalent. Do not create a dashboard or
move charts to the end of the dossier.

## Accessible visualization

Use semantic HTML and CSS already available in the dossier:

- KPI values as text, not chart-only glyphs;
- a segmented bar implemented as a labelled list or meter-like CSS layout with
  exact counts and proportions in visible text;
- no canvas, SVG, external chart library, CDN, remote font, or network request;
- no color-only distinction: each segment has a text label and count;
- no gradient, pie, radar, gauge, bubble, or time-series chart;
- no animation required to understand state;
- print and grayscale preserve labels and counts;
- forced-colors uses Canvas, CanvasText, and Highlight; and
- mobile stacks labels and values without clipping or horizontal scrolling.

A time trend remains forbidden until at least 8–12 comparable observations
exist under a separate stable longitudinal contract.

## Failure behavior

- Negative or non-integer counts fail closed.
- Duplicate metrics, duplicate evidence IDs, invalid windows, future dates,
  additional fields, raw records, and inconsistent counts fail closed.
- Missing values produce an honest partial state; they are not an error unless
  the state claims completeness.
- Incompatible windows suppress derived composition/rate rather than discarding
  valid standalone KPIs.
- Privacy or consent failure suppresses all analytics values.
- Diagnostics are bounded, fixed, and never echo values, paths, keys, or
  controls.

## Acceptance criteria

1. V1 and v2 analytics fixtures, validation, rendering, and bytes remain
   unchanged.
2. V3 accepts consented partial aggregates and rejects partial data labelled
   complete.
3. Every observed metric has one compatible local window definition and one or
   more consented aggregate evidence references.
4. Negative counts, duplicate metrics, future dates, raw/private fields,
   `recruiter_viewers > profile_views`, and
   `qualified_contacts > inbound_contacts` fail closed without echo.
5. Composition and contact rate are recomputed deterministically and are never
   caller-supplied.
6. Missing or incompatible inputs omit the corresponding derived chart and
   explain the limit without fabricated zeros.
7. Renderer shows each observed KPI once, the segmented composition only when
   comparable, and the causal/quality boundary once in EN and ES.
8. DOM, ARIA, mobile, print, dark, forced-colors, high-contrast, grayscale,
   reduced-motion, privacy, static, schema, plugin, root, source-cache, and
   provenance gates pass before publication.
9. Empirical desktop/mobile/print/browser/AT QA is recorded separately and is
   never inferred from static tests.
10. A live run re-confirms aggregate values under explicit report consent; no
    value from the user's example is compiled into source code.
