# Atomic private renderer asset reads

## Context

Private renderer assets must remain inside the installed plugin package. The
current loader validates a pathname and then reads that pathname later, so a
replacement between those operations can redirect the read outside the
package. Symlink and hardlink checks are necessary but are not sufficient when
the pathname is reopened after validation.

## Contract

- Resolve and validate the requested path using the existing package-local,
  absolute-path and regular-file rules.
- Open the package root and every intermediate directory with directory file
  descriptors and `O_NOFOLLOW`.
- Open the final component relative to its already-open parent descriptor,
  never by reopening the full pathname.
- Validate the opened final descriptor with `fstat`: it must be a regular file
  with exactly one hard link.
- Read and decode UTF-8 bytes from that descriptor, then close every descriptor
  on every success and failure path.
- Return the existing bounded `PrivateAssetError` message for missing files,
  symlinks, hardlinks, directories, races, and decode failures. Never echo the
  requested path or asset bytes in the error.
- Keep the canonical ten-asset inventory and renderer output unchanged.

## Compatibility and non-goals

This is an internal loader hardening change. It does not change asset contents,
HTML, CSS, schemas, renderer copy, or the v1/v2 contracts. It does not delete
legacy caches or modify marketplace configuration. The dark-mode opportunity
for practice and triage remains a separate later increment.

## Acceptance evidence

1. A regular package-local file remains readable.
2. Existing symlink and hardlink tests remain rejecting without echoing data.
3. A controlled swap after pathname validation cannot cause external bytes to
   be returned; it raises the bounded loader error instead.
4. Canonical asset validation, renderers, static/privacy/release gates, and the
   installed smoke suite remain green.
