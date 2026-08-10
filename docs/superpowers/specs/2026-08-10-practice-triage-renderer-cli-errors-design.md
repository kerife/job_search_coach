# Practice and triage renderer CLI errors design

## Goal

Normalize malformed arguments in the private practice-session and recruiter-triage renderer CLIs.

## Scope

Catch argparse parse failures at each `_cli`, return code 3 without traceback/artifact, and preserve help 0, semantic validation 2, and valid rendering. No schema, HTML, or routing changes.

## Acceptance

Missing required flags and unknown arguments return 3 for both renderers; help returns 0; valid EN/ES fixtures remain unchanged.
