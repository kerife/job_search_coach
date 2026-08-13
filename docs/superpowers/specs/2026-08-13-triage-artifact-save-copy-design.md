# Triage artifact-save boundary copy

## Problem

The private triage renderer writes a requested HTML artifact with restrictive
permissions, while its footer says that nothing is saved on the device. That
sentence correctly describes `local_save_mode=disabled` (the raw source reply
is not retained), but it can mislead users into believing the generated HTML
artifact was not written.

## Decision

Replace the ambiguous footer sentence with two localized, fixed sentences:

- EN: `Source reply is not retained by this flow. This private HTML artifact is saved only at the path you requested.`
- ES: `Este flujo no conserva la respuesta de origen. Este artefacto HTML privado solo se guarda en la ruta que solicitaste.`

Keep the existing `No external action was taken.` / `No se realizó ninguna
acción externa.` boundary and do not interpolate the actual filesystem path
into HTML. The renderer remains local-only, `local_save_mode=disabled` still
means raw reply retention is disabled, and `_atomic_private_write` remains the
authority for the requested artifact's `0600` permissions.

## Verification

Update renderer copy assertions for EN/ES across clarify, ready, and stop
states. Assert the old ambiguous sentence and internal enum are absent, the
two new sentences appear exactly once, and no path is interpolated. Keep the
existing CLI write test as the permission/path proof and add an explicit
assertion that the receipt path equals the requested output. Run triage API and
renderer suites, static/privacy/release gates, and the full plugin suite. No
schema, CSS, Superdesign dump, or external-action behavior changes are needed.
