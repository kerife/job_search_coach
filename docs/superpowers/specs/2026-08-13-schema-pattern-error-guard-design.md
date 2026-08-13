# Schema pattern error guard

## Problem

The public schema subset validator accepts a string `pattern` keyword and sends
it directly to `re.search`. A syntactically valid JSON schema containing an
invalid regex raises `re.error`; a nested unbounded quantifier such as
`(a+)+$` can consume exponential CPU instead of returning the validator's
normal diagnostic list.

## Design

Keep the existing string-shape check and validate regex syntax before search.
Invalid regex syntax returns `schema pattern is invalid`. A nested unbounded
quantifier returns `schema pattern exceeds safe complexity limit`; finite
quantifiers and existing pattern mismatch messages remain unchanged.

## Success criteria

- Invalid patterns return the fixed diagnostic without an exception.
- Valid matching and non-matching patterns preserve existing behavior.
- Schema, plugin, static, privacy, release, and source/cache parity gates pass.
