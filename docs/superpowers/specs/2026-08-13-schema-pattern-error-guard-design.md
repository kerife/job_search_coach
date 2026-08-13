# Schema pattern error guard

## Problem

The public schema subset validator accepts a string `pattern` keyword and sends
it directly to `re.search`. A syntactically valid JSON schema containing an
invalid regex raises `re.error` instead of returning the validator's normal
diagnostic list.

## Design

Keep the existing string-shape check and wrap only regex compilation/search in
the validator's fixed error contract. Invalid regex syntax returns
`schema pattern is invalid`; valid patterns and existing pattern mismatch
messages remain unchanged.

## Success criteria

- Invalid patterns return the fixed diagnostic without an exception.
- Valid matching and non-matching patterns preserve existing behavior.
- Schema, plugin, static, privacy, release, and source/cache parity gates pass.

