# LinkedIn Profile URL Privacy Guard

## Context

`validate_case.py` rejects LinkedIn profile URLs only when the value includes
`http://` or `https://`. The case contract requires rejecting LinkedIn profile
URLs as credential-shaped/private values, so scheme-less forms such as
`linkedin.com/in/example/`, `www.linkedin.com/in/example/`, and legacy
`linkedin.com/pub/example/...` forms must fail before case data is retained or
rendered.

## Design

- Keep the existing validator API, error wording, optional record fields, and
  recursive scan unchanged.
- Replace the LinkedIn profile regex with a bounded host/path pattern that
  accepts an optional HTTP(S) scheme, an optional subdomain such as `www`, and
  the `/in/` or legacy `/pub/` profile path.
- Require a host boundary so ordinary prose containing a larger hostname or
  identifier is not rejected accidentally.
- Do not change schemas or renderers because this is the case-ingestion privacy
  guard and the existing diagnostic is already stable.

## Acceptance criteria

1. `https://www.linkedin.com/in/synthetic-sentinel/`,
   `www.linkedin.com/in/synthetic-sentinel/`, `linkedin.com/in/synthetic-sentinel/`,
   and equivalent `/pub/` profile forms all produce the existing bounded
   `case contains credential-shaped value at claims[0].text` error.
2. The diagnostic never echoes the URL value.
3. Existing safe prose and all current `validate_case` tests remain green.
4. The change is limited to the validator and its focused regression tests.

## Explicitly deferred

The print-safe `.practice-next-action` contrast override and triage
`prefers-contrast` hook are recorded as the next UX cycle; they are independent
of this privacy boundary.
