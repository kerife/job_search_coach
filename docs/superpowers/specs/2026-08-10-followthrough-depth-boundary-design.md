# Follow-through depth boundary design

## Goal

Apply the private artifact JSON nesting limit uniformly to follow-through checkpoint and receipt inputs.

## Scope

Add the existing maximum depth policy (12, root depth 0) to `_load_json` in the follow-through validator. Both checkpoint and receipt files use this loader, so no renderer, schema, routing, or copy changes are needed.

## Acceptance

Valid fixtures remain accepted; checkpoint and receipt JSON nested beyond depth 12 fail closed before validation/rendering; focused tests, static/privacy checks, and full discovery pass.
