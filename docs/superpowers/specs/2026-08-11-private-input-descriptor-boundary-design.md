# Descriptor-anchored private input boundary

## Context

The six private JSON validators reject a symlink at the final pathname
component, then call `Path.read_text()` or `read_bytes()`. A symlink in an
intermediate directory is therefore followed, and a final component can also
be swapped between the check and the read. The loaders additionally allocate
the full file before enforcing their existing byte limits.

## Design

Add `scripts/private_input_loader.py` with one dependency-free reader:

- normalize lexical path components without resolving user symlinks;
- open each parent directory with `O_DIRECTORY | O_NOFOLLOW` and a retained
  descriptor, then open the leaf with `O_NOFOLLOW` and `O_CLOEXEC`;
- require a regular leaf and read at most `max_bytes + 1` bytes before UTF-8
  decoding; reject oversized, unavailable, non-regular, or symlink paths with
  typed reasons;
- preserve the existing trusted macOS `/tmp` and `/var` aliases used by the
  repository's descriptor boundary tests.

The dossier, practice, triage, checkpoint, and conversion loaders will map
those reasons to their existing surface-specific public error strings. JSON
parsing, duplicate-key checks, depth limits, schemas, HTML, IDs, and actions
remain unchanged.

## Acceptance

Each loader rejects a valid JSON file reached through an intermediate parent
symlink and a direct leaf symlink, while regular files under `/tmp` and the
default macOS temporary directory remain accepted. A bounded read rejects
files larger than the existing per-surface limit without allocating their full
contents. Focused and full suites, static/privacy gates, official validation,
source/cache parity, and installed smoke must pass.
