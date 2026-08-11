# Private renderer asset hardlink boundary

## Problem

The private renderer asset loader rejects symlinks and path traversal, but it
currently accepts a hardlink. A hardlink inside a package can reference an
inode created from a private file outside the package, so a renderer can read
bytes that were never part of the package inventory. This violates the
package-local regular-file boundary.

## Design

`private_asset_loader._regular_package_path` will accept only an absolute,
package-contained inode that is a regular file with exactly one hardlink
(`st_nlink == 1`). The existing symlink, traversal, UTF-8, and bounded error
contracts remain unchanged. `validate_asset_paths` already exercises every
canonical renderer asset, so the static gate will inherit the same hardlink
check without a second inventory or renderer change.

## Acceptance

- A normal copied file remains readable.
- A direct hardlink to an external file is rejected before bytes are read.
- Existing symlink, broken-symlink, traversal, renderer, privacy, schema, and
  no-action behavior remains unchanged.
- The focused loader tests, plugin suite, static/privacy/release gates, root
  suite, and installed source/cache smoke pass before a single new cachebuster.
