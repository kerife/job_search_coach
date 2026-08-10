# Post-review market evaluator input

Evaluator: `market_post_review_eval`. Evaluation date: 2026-08-06. Scope: read-only audit of the four direct-employer URLs below for Senior DevOps Engineer; no application, message, profile, or account action is authorized.

## Crawl provenance

- Peek: `https://jobs.ashbyhq.com/peek/58b9bb30-2bf9-46ab-afab-f6338131bedc`
  - Crawl outcome: active official employer vacancy. Search and the official page identify a remote, full-time Mexico Senior Dev Ops Engineer vacancy and disclose `MX$950K–MX$1.3M` Mexico base salary. Publication date unavailable.
  - Observed requirements are source-specific: AWS and EKS/Kubernetes, Terraform or Pulumi, CI/CD, and on-call/production operations.
- Restaurant365: `https://jobs.lever.co/restaurant365/1655a724-70fd-42cb-88a1-15cbd6dba926`
  - Crawl outcome: HTTP 404 at the exact direct employer URL. State is `unavailable`; it is not a current feed entry.
  - Historical context retained from the superseded 2026-08-06 run: Mexico City hybrid Senior DevOps Engineer, annual compensation `MX$1,230,000–MX$1,540,000`, with Azure and AKS. This observation may not support a current range, demand, confidence, or recurrence.
- Element84: `https://jobs.ashbyhq.com/element84/9c7498b2-8671-4f06-a1b5-e70fc7cd32b1`
  - Crawl outcome: active official page titled Senior DevOps Engineer (Hub-Remote: DC or Philly Metro), but its JavaScript response exposed no salary details. Retain the US-person and US-work-authorization constraint documented in the original direct-page capture; range remains unknown.
- Luxury Presence: `https://jobs.lever.co/luxurypresence/c8c67c22-5ba3-4284-8247-3564eaf2ccb6`
  - Crawl outcome: active official Senior DevOps Engineer - LATAM (Remote), full-time remote vacancy. No compensation or Mexico-specific employee, contractor, EOR, tax, or benefit arrangement is disclosed.

## Required evaluation rules

Use `source_state` values `active`, `stale`, `expired`, or `unavailable`. Record a source-specific `compensation_observation` or `unknown` for every source. A current range needs multiple active compatible observations. Stale, expired, or unavailable observations cannot support current range, demand, confidence, or recurrence. Broad demand and recurring requirements are unknown when only one active vacancy exists. Keep provider-specific AWS/EKS and Azure/AKS requirements source-specific. Do not make a career decision.
Do not compare or rank employment/geography observations as high-paying roles unless multiple active observations are fresh and compatible in currency, compensation basis, compensation components, seniority, geography, employment arrangement, and eligibility.
