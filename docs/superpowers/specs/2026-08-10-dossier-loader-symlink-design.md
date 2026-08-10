# Executive dossier loader symlink boundary

## Goal

Keep the executive dossier validator inside the caller-declared file boundary
by rejecting symlink inputs before reading them.

## Problem

`validate_executive_career_dossier.load_dossier()` reads any path that exists,
including symlinks. Other private artifact loaders already reject symlinks.
Following one lets a caller-provided dossier path resolve to a different file,
weakening the local/private input boundary and introducing a TOCTOU risk.

## Design

At the start of `load_dossier`, inspect the supplied `Path` with
`is_symlink()`. Raise the existing `DossierLoadError` with a fixed diagnostic
when true, before opening or parsing the target. Preserve the existing regular
file, directory, malformed JSON, duplicate-key, and missing-file behavior.
The CLI continues to map loader errors to its bounded exit code and does not
echo dossier content or resolved target paths.

## Acceptance

- A symlink to a valid dossier is rejected by the Python loader.
- The CLI rejects the same symlink with its normal validation error/exit code.
- A regular valid dossier still loads and validates.
- The error is stable, short, and contains no dossier content or target path.
- Existing plugin, root, privacy, static, release, and installed-cache gates
  remain green.
