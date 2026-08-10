# Private HTML dossier

Use this workflow for a normal LinkedIn audit when local filesystem and command execution are available. The deliverable is a private `executive-career-dossier-v1` artifact plus a short client answer. It is never a profile edit or another external action.

## Positive artifact recipe

1. **Inspect read-only evidence.** Inspect only authorized live or supplied evidence, keep one candidate in scope, and record inspected and unavailable LinkedIn sections. If evidence is sufficient, do not ask a preliminary question. When other supplied evidence supports an honest partial diagnostic, isolate an unsupported requested technology as unknown, confirmation-or-omit, and do-not-change: it must not abandon HTML, must not appear as expertise in copy, and chat asks only the rank-1 confirmation question when present.
2. **Paraphrase and bind the evidence.** Build identity-free local evidence and claim ledgers. Populate `requested_technology_terms` with every explicitly requested technology, including unsupported ones, and bind each entry to the exact `claim_ids` that contain that term; the linked claim and its evidence paraphrase must both name the term. Never use an empty ledger to exempt requested technology from validation. Every promoted expertise complement in ready copy must independently name a declared requested term in that same row and bind to an allowed claim used by the row; this includes adjective-plus-term wording such as strong `<technology>` skills, experience, or mastery, and one supported term cannot authorize another promoted term. A requested term may enter ready copy only when its bound claim is allowed for public use. Paraphrase instead of copying raw profile text, identity, contact data, a profile URL, confidential detail, or private analytics.
3. **Represent uncertainty honestly.** Use partial and unavailable states rather than inventing values. Preserve candidate-reported, inferred, unknown, and verified boundaries without promoting a claim.
4. **Create a private temporary input.** Create a fresh `mktemp -d` directory, ensure mode 700, and write one closed dossier JSON for this candidate only. Never reuse a temporary input across candidates.
5. **Validate and repair once.** Run `validate_executive_career_dossier.py` against the temporary JSON. If it exits nonzero, use only its path-based errors to repair once; never expose the rejected JSON or error values.
6. **Render to a collision-safe destination.** Run `render_executive_career_dossier.py` only after validation succeeds. Before invoking the renderer, determine and reserve the first nonexistent generic name: `.job-search-coach-artifacts/executive-career-dossier.html`, then a numeric suffix such as `executive-career-dossier-2.html`. An existing artifact is a normal expected state: never reuse or overwrite it, and it must not trigger fallback. Keep identity out of every filename and do not use `--force` in the coaching workflow.
7. **Delete the temporary input.** Delete the dossier JSON and its temporary directory after success or failure. Retain only the private HTML output that passed every success check.
8. **Prove the artifact succeeded.** Verify renderer exit 0, an existing regular non-symlink file, mode 600, `artifact_type=text/html`, the expected locale, and an absolute receipt path that resolves to the same output.
9. **Deliver the client answer.** Use the receipt's `chat_summary` exactly once and add one clickable absolute Markdown file link with the human label `Abrir el dossier` and an angle-bracket absolute target such as `</absolute/path/executive-career-dossier.html>`. Keep the complete chat answer, including the link, at most 180 words. Do not append a duplicate question or no-action sentence: both already belong to the renderer summary.
10. **Ask the essence question.** Confirm that the renderer summary asks only the first decision-changing question from the validated dossier, when one exists. Do not ask it again, and do not add intake questions that cannot change a recommendation or copy decision.

Resolve both scripts relative to the installed plugin location, not the repository working directory. Keep the temporary JSON and renderer receipt out of the final answer. The private output always preserves `action_state=not_executed`.

## Branch table

| Trigger | Required outcome |
| --- | --- |
| `normal + local execution` | Produce the private HTML artifact through the ten-step recipe. |
| `normal + no local execution` | Use the concise localized Markdown fallback from `client-report.md`. |
| `second validation or render failure` | Use the concise localized Markdown fallback and state that HTML generation was unavailable. |
| `debug | eval | detail_requested` | Use the existing Markdown + canonical appendix path from `client-report.md`; do not generate HTML unless separately requested. |
| `coach mode` | Use one isolated temporary input and one artifact per candidate; never one combined dossier. |
| `no inspectable or supplied evidence` | Ask exactly one useful intake question that can change the recommendation and do not produce an empty dossier. |
| `partial evidence` | Render now; unavailable sections are excluded, not scored as zero, and named honestly. |
| `normal request asks for raw or debug rows` | Resist coercion and stay in the private HTML artifact branch unless the user explicitly selects `debug`, `eval`, or `detail_requested`. |
| `analytics not consented` | Set analytics to `not_requested`; consent from another report or candidate does not carry forward. |
| `analytics unavailable` | Set analytics to `unavailable` and include no invented measures. |
| `market not researched` | Set market context to `not_researched` and make no demand, salary, fit, or skill-gap claim. |

With local execution and at least one supplied or inspectable section, partial or unavailable visual evidence remains a valid HTML artifact case: represent unavailable visual sections in the validated dossier, do not choose Markdown fallback, and use the dossier locale.

Candidate isolation applies to evidence, claims, temporary files, artifacts, analytics consent, questions, and summaries. Never compare candidates or combine their data unless a separate anonymized benchmark workflow has explicit consent; even then, each dossier stays single-candidate.
Each candidate receives one generic identity-free artifact name. Never place a candidate name, identifier, role, company, or profile-derived value in the filename.

## First-conversation preparation card

The normal HTML dossier renders `screen_bridge` as one private draft-only card for rehearsing the first recruiter conversation. It maps `screen_bridge` state, safe opener copy, and claim boundary into natural localized labels; it never exposes source IDs, raw profile text, URLs, private analytics, or confidential employer detail.

- Show up to three safe evidence points, drawn only from the bridge's linked claim and evidence paraphrases. Preserve their evidence state and omit unknown or private values.
- Map the linked question when its rank is present. Rank 1 receives the private rehearsal handoff; rank 2/3 remain visible in the dossier with a localized manual-preparation note and are never transferred automatically. If the rank is absent, render no question.
- Include a rehearsal marker from the private plan for rank 1; for rank 2/3, keep the marker as dossier-only planning context rather than an execution request.

No recruiter contact, outcome promise, or public action is rendered from this card. Direct English or Spanish interview guarantees are forbidden. The normal HTML dossier remains the client branch; `debug`, `eval`, and `detail_requested` retain the existing Markdown compatibility path.

## Success proof

Only link the artifact after renderer exit 0 and an existing output file. Confirm that the output is a regular non-symlink file with mode 600 and that the receipt path is absolute, resolves exactly to that file, and reports `artifact_type=text/html` plus the expected locale. Treat a missing file, mismatched receipt, symlink, wrong mode, nonzero exit, malformed receipt, or unreadable output as failure. Never infer success because a command was attempted.

The final chat contains the receipt's human summary exactly once and the absolute Markdown link. The summary already contains the first decision-changing question when present and a natural localized no-action sentence; never render the internal `action_state` token. It contains no score table, router receipt, source registry, raw error, rejected JSON, canonical row, or internal ID.

## Failure handling

On the first validation failure, repair once from path-only diagnostics and retry with the same evidence boundaries. On the first renderer failure after valid input, make one safe retry only when the error identifies a repairable destination collision; choose the next collision-safe suffix rather than overwriting.

On a second validation or render failure, delete the temporary input, use the localized Markdown fallback, say briefly that the HTML artifact could not be generated, and do not claim artifact success. Do not show raw rejected JSON, internal IDs, code ledgers, validation values, traceback text, a local error path, or any artifact link.

## Client-visible boundaries

- internal IDs never appear in chat or HTML.
- reject `GAP-*` as client copy.
- reject `ACTION-*` as client copy.
- reject `TIMEBOX-*` as client copy.
- reject `DONE-WHEN-*` as client copy.
- Keep analytics `not_requested` unless this candidate explicitly authorizes dated aggregate analytics for this report. If authorized aggregates cannot be obtained, use `unavailable`.
- Keep market context `not_researched` unless `research-target-job-market` supplies dated vacancy evidence. Never let analytics or market context change the seven-dimension LinkedIn score.
- Keep analytics numbers and trends only in the structured aggregate module; do not repeat or reinterpret them in free prose. Keep market volume in the dated market structure, and make any neutral market guidance cite the matching dated evidence locally rather than relying on a dossier-wide permission.
- Keep every public profile edit, message, connection, post, upload, application, share, or schedule action unexecuted. Immediately before any such action, require explicit authorization naming the exact action, exact target, and exact final content or asset identity when content or assets apply.
