# Summarize outcomes input boundary

## Goal

Keep the deterministic outcome summary safe for candidate-supplied CSV files by rejecting path traversal through symlinks, invalid encodings, and oversized input before CSV parsing.

## Contract

- Read the final path through the shared descriptor-anchored private-input loader.
- Cap the decoded input source at 256 KiB before constructing a CSV reader.
- Return stable JSON errors without echoing paths, errno text, or candidate identifiers.
- Preserve existing headers, date/boolean validation, candidate isolation, consent, and summary JSON.

## Verification

RED tests cover direct/intermediate symlinks, oversized bytes, invalid UTF-8, and diagnostic non-echo. GREEN requires the focused outcome suite, plugin suite, static/schema/privacy checks, source/cache parity, installed smoke, and release validation.

## Deferred opportunity

The dossier utility-action landmark currently uses `nav` for a print action without links. Revisit it as a separate accessibility increment after this input-boundary release.
