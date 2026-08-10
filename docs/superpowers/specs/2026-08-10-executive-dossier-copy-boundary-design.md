# Executive dossier confirmation boundary

Copy controls for cards marked as requiring confirmation remain draft-only,
but their boundary must be announced to assistive technology. The renderer
will add a fixed localized description to those buttons and include it in
`aria-describedby` alongside the live copy status. The description never
contains draft text, identity, contact data, or an action instruction.

Acceptance: ready cards keep their existing semantics; confirmation cards
announce the fixed boundary; omitted cards have no copy control; button names,
copy status, print behavior, CSP, and privacy behavior remain unchanged.
