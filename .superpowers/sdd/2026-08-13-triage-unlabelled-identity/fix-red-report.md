# RED report — final-review identity guard fixes

## Scope

Test-only increment from `b3935a6`; no validator, renderer, schema, fixture, or
template files were changed.

## Added regression coverage

- CLI rejection matrix for ordinary full-name prose in all four walked fields:
  `safe_context.summary`, `facts[0].summary`, `question.text`, and
  `blocked_claims[0]`.
- The matrix retains the prior `has`/`tiene` checks and adds:
  `reports`, `describes`, `works`, `explains`, `reported`, `reporta`,
  `describe`, `trabaja`, `explica`, and `menciona`.
- Explicit CLI acceptance checks for `Platform Engineering has ...`,
  `Technical Leadership has ...`, and `Cloud Security has ...`.
- Renderer gate coverage now uses the previously bypassing `John Smith reports
  a verified technical achievement.` form and requires a
  `TriageValidationError` without name echo.

## RED evidence

Command:

```sh
PYTHONPATH=plugins/professional-growth-coach/scripts python3 -m unittest -q \
  tests.test_private_recruiter_reply_triage.PrivateRecruiterReplyTriageContractTests.test_rejects_ordinary_unlabelled_names_in_every_prose_field \
  tests.test_private_recruiter_reply_triage.PrivateRecruiterReplyTriageContractTests.test_accepts_role_focused_prose_without_identity_context \
  tests.test_render_private_recruiter_reply_triage.PrivateRecruiterReplyTriageRendererTests.test_render_rejects_an_ordinary_unlabelled_english_full_name_without_echoing_it
```

Result: `Ran 3 tests ... FAILED (failures=44)`.

Exact failure classes:

1. 40 rejection-matrix subtests: each new verb form was accepted in each
   prose field (`AssertionError: 0 != 2`).
2. 3 role-focused acceptance subtests: each was rejected as
   `session contains forbidden unlabelled_identity prose` (`AssertionError: 2 != 0`).
3. 1 renderer subtest: `AssertionError: TriageValidationError not raised` for
   the `reports` sentence, proving the unsafe prose would reach rendering.

## Handoff concern

The production fix must expand the full designed verb family while retaining
the established technical-role exclusion. Do not remove or weaken the fixed,
non-echoing diagnostic contract.
