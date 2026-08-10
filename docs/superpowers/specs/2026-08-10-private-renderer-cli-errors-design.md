# Private renderer CLI errors design

## Goal

Normalize malformed arguments in the conversion-outcome and follow-through renderer CLIs to the established input-error contract.

## Scope

Catch argparse parse failures and invalid date values at each `_cli` boundary, emit one concise deterministic error, and return exit code 3. Preserve valid rendering, validator failures (exit 2), output safety, and localized content. No schema or routing changes.

## Acceptance

Invalid `--as-of` and missing required flags in both CLIs return 3 without traceback or artifact; valid EN/ES rendering remains unchanged and focused CLI/renderer tests pass.
