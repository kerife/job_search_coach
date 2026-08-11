# Private Recruiter Reply Triage v2 Content Locale

## Context

Triage v1 uses one `locale` for fixed decision copy and free-form context,
question, facts, and blocked-claim prose. A valid mixed-language artifact can
therefore expose the wrong language to assistive technology. Adding optional
fields to v1 would violate its closed schema and leave existing consumers
ambiguous.

## Design

Add `private-recruiter-reply-triage-v2` as a parallel closed schema. It replaces
v1 `locale` with required `ui_locale` and `content_locale`, each `es|en`; all
other fields, privacy guards, delivery invariants, and state/classification
rules remain identical. The v1 validator/schema/fixtures remain unchanged.

The triage renderer uses `ui_locale` for document language, fixed labels,
receipt/chat copy, and decisions. It adds escaped `lang=content_locale` only to
dynamic prose: safe-context summary, fact summary, question text, blocked
claims, and the repeated handoff preview values. For v1 it emits the existing
markup byte-for-byte. Dossier and dossier→practice handoff are explicitly out
of this increment.

## Verification

Add v2 schema/validator/renderer tests for English UI with Spanish content,
missing/invalid locale rejection, v1 rejection of v2 fields, unchanged v1
markup, resolved ARIA references, and no identifier/raw-content leakage. Run
the full release/install matrix.
