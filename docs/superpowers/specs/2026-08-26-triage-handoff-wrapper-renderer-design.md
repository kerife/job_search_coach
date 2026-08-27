# Triage handoff wrapper renderer

## Goal

Close the last manual seam between a validated triage-practice handoff wrapper
and its HTML artifact without weakening provenance or privacy.

## Contract

`render_private_recruiter_triage_practice_handoff.py HANDOFF.json --output
OUT.html [--force]` loads one wrapper through the bounded private-input loader,
validates it with `validate_private_recruiter_triage_practice_handoff`, extracts
`practice_session` only in memory, and delegates to the existing practice
renderer. It never creates an intermediate JSON file or auto-starts a session.

The wrapper renderer returns a minimal success receipt containing only the
artifact kind and UI locale. Failures use stable codes (`invalid_arguments`,
`invalid_input`, `validation_failed`, `output_exists`, `unsafe_output`) without
echoing paths, arguments, IDs, URLs, raw replies, questions, or diagnostics.
Output is written atomically with existing private permissions (`0600`, parent
`0700`), rejects symlinks and non-regular overwrite targets, and requires
`--force` to replace an existing regular file.

## Visual handoff truth

When the renderer is invoked from a valid wrapper, the triage route includes one
localized static status block: “Borrador privado · Reingreso manual requerido” /
“Private draft · Manual re-entry required”, followed by fixed copy that says it
does not start, send, or save automatically. The existing direct session
renderer remains compatible; a bare session cannot claim wrapper delivery
status. No controls, links, forms, scripts, or new dynamic prose are added.

## Testing

Cover valid ES/EN wrapper→HTML parity, mutated wrapper delivery/provenance,
unsafe prose, duplicate keys, symlinks, size/depth limits, overwrite/force,
permissions, error redaction, and absence of wrapper status for direct sessions.
Run focused, plugin, static, privacy, release, and root suites before release.
