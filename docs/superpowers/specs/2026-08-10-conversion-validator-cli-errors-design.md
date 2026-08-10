# Conversion validator CLI errors design

## Goal

Normalize missing and unknown arguments in the conversion-outcome validator CLI to the established input-error contract.

## Scope

Catch argparse parse failures in `_cli`, returning 3 without traceback or output; preserve invalid-date code 3, `--help` code 0, semantic validation code 2, and valid JSON output. No schema, renderer, or routing changes.

## Acceptance

Missing required flags and unknown arguments return 3; help remains 0; valid EN/ES fixtures and existing privacy behavior remain unchanged.
