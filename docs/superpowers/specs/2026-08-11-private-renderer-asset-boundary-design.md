# Private renderer asset boundary

## Problem

The offline renderers read their HTML templates and CSS directly from the
plugin asset directory. A symlink on an asset, or on an intermediate directory,
can redirect that read outside the checked-out plugin and inject unreviewed
content into a private artifact.

## Design

Add one dependency-free `private_asset_loader.py` helper. It accepts a plugin
root and an asset path, requires the path to remain below that root, rejects
every symlink component (including broken links), requires a regular file, and
reads UTF-8 content. It raises one bounded error without echoing paths or
content. Dossier, practice, triage, checkpoint, and outcome renderers use this
helper for both template and CSS reads. The static checker uses the same
boundary for all ten canonical HTML/CSS assets.

## Non-goals

No CSS, HTML structure, copy, CSP, output permissions, or external-resource
behavior changes. Normal regular files remain accepted; compact receipts keep
their existing visual family.

## Acceptance

- Direct, intermediate, and broken asset symlinks fail closed in the helper,
  renderer path, and static package gate.
- A symlinked asset containing a marker is never embedded in output.
- All canonical regular assets pass, and diagnostics do not echo external
  paths or content.
- Existing render, schema, privacy, static, and release gates remain green.
