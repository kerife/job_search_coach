# Validate-case diagnostic path-key redaction

## Problem

Malformed case JSON can supply an unsupported object key that is an absolute
Unix, application, or UNC path. `validate_case.py` escapes controls and hides
some credential-shaped keys, but its unsupported-field diagnostic currently
echoes `/opt`, `/Applications`, and UNC paths in the API result and CLI stderr.

## Design

Extend the existing `_LOCAL_PATH_VALUE` classifier with the common absolute
roots and UNC prefixes already treated as private input boundaries elsewhere
in the plugin. `_safe_path_key` will continue returning ordinary relative keys
unchanged, keep control escaping, and preserve the existing `<redacted-key>`
marker for absolute or credential-shaped keys.

The public behavior for valid cases, schema validation, duplicate-key handling,
and diagnostic byte bounds remains unchanged. The regression contract covers
both direct validation and the supported CLI so the privacy boundary is tested
at both output surfaces.

## Success criteria

- `/opt/private/profile.json`, `/Applications/private.app`, and
  `\\\\server\\share\\profile.json` never appear in returned diagnostics or
  CLI stderr.
- Ordinary `unexpected` and relative `relative\\profile.json` keys remain
  visible for useful diagnostics.
- Existing drive-path and control-character tests remain green.
- Focused case tests, plugin tests, static checks, privacy scan, and release
  validation pass before publishing the next plugin version.

