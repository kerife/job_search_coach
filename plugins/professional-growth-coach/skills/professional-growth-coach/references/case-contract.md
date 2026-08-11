# Case contract

Use one JSON object for one candidate. Required keys are:

`schema_version`, `candidate_id`, `mode`, `consent`, `target`, `sources`, `claims`, `interventions`, and `outcomes`.

The named input file must be a regular, non-symlink file no larger than 64,000
UTF-8 encoded bytes. Oversized, non-regular, or unreadable inputs are rejected
before JSON validation and diagnostics do not echo paths or input contents.

Schema version must equal `1.0` and is closed at every object boundary. The only allowed fields are:

- `consent`: `benchmark`.
- `target`: `roles`, `geography`, `compensation`, `constraints`.
- each `source`: `candidate_id`, `source_id`, `kind`, `evidence_label`.
- each `claim`: `candidate_id`, `claim_id`, `text`, `evidence_label`.
- each `intervention`: `candidate_id`, `intervention_id`, `kind`, `description`, `occurred_at`.
- each `outcome`: `candidate_id`, `outcome_id`, `kind`, `value`, `observed_at`, `benchmark_candidate_ids`.

- `candidate_id` is a non-empty stable identifier. Every item in `sources`, `claims`, `interventions`, and `outcomes` carries the same ID. Each collection's provenance ID (`source_id`, `claim_id`, `intervention_id`, or `outcome_id`) is a non-empty stable identifier unique within that collection.
- `mode` is `self-service` or `coach`. Coach mode has one record per candidate, never a combined record.
- `consent.benchmark` defaults to `false`; only explicit, revocable `true` permits anonymized benchmarking.
- `target` is the candidate's stated role, geography, compensation, or constraints. Missing targets are evidence gaps.
- `sources` and `claims` include an `evidence_label`.
- `interventions` and `outcomes` record only this candidate's work and results.

Reject a mixed ID rather than merging it. Recursively bind every candidate-, person-, or subject-ID field to the case candidate; `benchmark_candidate_ids` must be a list of non-empty strings and may differ only with explicit consent, while consent revocation makes that same benchmark object invalid immediately. Apply NFKC, format-character removal, and narrow separator normalization before recursive sensitive-key, identity, and credential-value classification. Reject values outside the JSON data model with deterministic path-specific errors. Recursively reject sensitive key segments and credential-shaped values, including authorization headers, common secret assignments, email addresses, phone numbers, LinkedIn profile URLs, and local paths. Dynamic sensitive or credential-shaped key segments in diagnostics are replaced with `<redacted-key>`; canonical schema names and ordinary unsupported names remain path-specific. Validation and defaulting operate on a copy and never mutate the input. Minimize identifiers and do not store credentials, session data, private conversations, or unnecessary contact details.
