# Case Path Descriptor Walk

## Context

The case reader now opens the final pathname component with `O_NOFOLLOW`, but
intermediate parent symlinks are still resolved by the kernel. A path such as
`alias/case.json`, where `alias` points outside the intended tree, is accepted;
swapping that parent during a read can also redirect the leaf.

## Design

Resolve the textual input path to an absolute path without calling
`realpath()`. Open `/` (or the current directory for a relative path) as a
directory descriptor, then open each parent component with `O_DIRECTORY` and
`O_NOFOLLOW` using `dir_fd`. The only symlink exceptions are macOS's trusted
system aliases `/tmp -> /private/tmp` and `/var -> /private/var`, verified by
exact `realpath` targets and only for the first component. Open the final name
relative to the anchored parent descriptor with `O_NOFOLLOW`, then retain the
existing regular-file, size, UTF-8, and bounded-read checks.

Close every descriptor on success and failure. Keep relative `CASE.json`
behavior by anchoring `.` and reject `.`/`..` components inside the walked path
as unsafe rather than allowing an escape from the anchor.

## Boundaries

- No schema, validation, renderer, or diagnostic changes.
- Existing direct symlink, regular temp file, `/tmp`, `/var`, and relative path
  behavior is covered by tests.
- The diagnostic cap remains unchanged.

## Acceptance

1. A valid case behind one or more intermediate symlink directories is rejected
   with the fixed unreadable-input error and never reads the target.
2. Absolute and relative regular files remain accepted.
3. Trusted macOS `/tmp` and `/var` aliases remain accepted when they resolve to
   their exact private targets.
4. No path-based leaf open remains after the parent descriptors are acquired.
5. Existing case, privacy, static, plugin, release, and installed smoke gates
   remain green.
