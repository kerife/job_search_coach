# Dossier copy-button accessible context

## Context

The dossier now names each copy card, but every copy control still exposes the
same accessible name (`Copiar borrador` or `Copy draft`). A screen-reader
button list therefore cannot distinguish which draft each control copies.

## Decision

Keep the visible button text, clipboard target, live status, confirmation
description, localization, print behavior, and copy JavaScript unchanged. Add
only a localized `aria-label` formed from the existing visible action label
and validated copy category, for example `Copiar borrador: Titular` or `Copy
draft: Headline`. Omitted copy cards continue to render no button.

## Verification

Renderer tests will assert ES and EN labels are contextual and unique for every
rendered button, while visible text remains stable and omitted cards remain
button-free. No Superdesign CSS dump changes are required. Run dossier,
accessibility/parity/print, plugin, static/privacy, provenance, and release
validation gates after publishing.
