# Private loader symlink consistency design

## Goal

Make every private JSON loader reject symlink input paths consistently.

## Scope

Add the existing fail-closed `Path.is_symlink()` guard to recruiter practice-session and private recruiter-reply triage loaders. Preserve their duplicate-key, byte-size, depth, validation, renderer, and CLI behavior for regular files. No schema, routing, HTML, or persistence changes.

## Acceptance

Each loader rejects a temporary symlink in focused tests, valid fixtures remain accepted, and the existing error class/CLI failure boundary remains intact. Focused suites, static/privacy checks, and full discovery must pass before release.
