# Follow-through validator CLI errors design

## Goal

Normalize malformed arguments in the follow-through validator CLI to the established input-error contract.

## Scope

Catch argparse parse failures and invalid `--as-of` values at `_cli`, returning code 3 without traceback or validation artifact. Preserve `--help` code 0, semantic validation code 2, and valid JSON output. No schema, renderer, or routing changes.

## Acceptance

Invalid date and missing required flags return 3 with concise deterministic stderr; valid fixture returns its existing result and help remains 0.
