# Feedback-sensitive continuity rail

## Decision

Update the existing private recruiter-practice continuity rail so its final
step reflects the validated governing feedback label after `feedback_available`.
Before feedback, preserve the current three-step rail unchanged. The change is
projection-only: no schema, validator, CLI, artifact, storage, or external
action changes.

## Brainstorming outcome

- Re-entry checklist: useful for routed conversion receipts, but overlaps the
  existing manual bridge and is deferred.
- Feedback-sensitive rail: selected because it corrects a visible state mismatch
  immediately after feedback without transporting private answer or observation
  text.

## Contract

`_continuity_rail(locale, state, governing_label=None)` accepts only the existing
closed locale, session state, and feedback-label enums. When `state` is not
`feedback_available`, it emits the existing copy and pending next-version step.
When feedback is available, the first two steps are current and the final step
is selected from fixed locale/label copy:

- `solid`: pending; review the next answer privately before external action.
- `confirm`: blocked; confirm or narrow the uncertain point before the next
  private rehearsal.
- `do_not_assert`: blocked; remove the unsupported claim before the next private
  rehearsal.

The output may contain only fixed bilingual copy, closed `data-stage` and
`data-state` values, and the existing static structure. It must never reflect
  raw answer/feedback text, IDs, source refs, URLs, paths, or user HTML.

## Acceptance criteria

1. EN/ES × all five question kinds × all three feedback labels render exactly
   one rail with three steps and the expected final state/copy.
2. Ready and awaiting-answer states keep the existing evidence/rehearsal/current
   and next-version/pending rail.
3. Existing order remains feedback → decision → next-version bridge → rail →
   evidence/boundary.
4. Tests reject/never reflect sentinel IDs, raw answer/feedback text, URLs,
   paths, controls, scripts, event handlers, or duplicate IDs.
5. CSS keeps the current grid and 640px collapse, adding only closed-state
   styling that remains legible in dark, print, forced-colors, contrast-more,
   and reduced-motion modes. `.superdesign/init/theme.md` mirrors the exact
   co-located CSS.
6. README and the interview-preparation skill explain that the rail is a static
   private continuity summary and never starts preparation or external action.
