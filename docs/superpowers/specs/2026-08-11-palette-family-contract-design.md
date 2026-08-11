# Palette family contract

## Problem

The Superdesign system describes one base palette, while the plugin already
ships three intentional visual families: the dossier, practice/triage, and
compact receipts. CSS values are currently valid but undocumented as a family
contract, so a future edit can introduce an unreviewed color without a static
failure.

## Decision

Document the three family allowlists and add a dependency-free checker for the
five canonical CSS assets. The checker normalizes three-digit hex values and
reports any hex color outside the allowlist for that asset family. It ignores
non-hex CSS color functions and forced-colors system keywords. This increment
does not recolor or re-layout any artifact, and compact receipt palettes stay
separate from dossier/practice/triage palettes.

## Acceptance

- Existing canonical CSS passes its family allowlist.
- A synthetic unapproved hex and a family-mismatched hex fail with a bounded
  diagnostic naming only the asset family and color.
- The plugin-local static gate runs the checker.
- Existing renderer, privacy, schema, and release tests remain green.
