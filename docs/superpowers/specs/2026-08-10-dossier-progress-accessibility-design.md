# Dossier scorecard progress accessibility

## Goal

Give every evaluated scorecard progress bar a programmatic accessible name by
associating it with the dimension heading already visible in the card.

## Design

The dossier renderer will assign each dimension heading an ID derived from the
closed dimension key, such as `dimension-title-visual`, and add the matching
`aria-labelledby` to that card's native `<progress>`. The visible score text,
fallback text, CSS, order, localization, and non-evaluated cards remain
unchanged. Because dimension keys are validator-closed and unique, IDs remain
deterministic and collision-free.

## Acceptance

- Every evaluated `<progress>` in Spanish and English has exactly one
  `aria-labelledby` reference.
- Each reference resolves to the corresponding visible `<h3>` dimension title.
- Non-evaluated cards retain their existing state chip and do not gain a fake
  progress value.
- No copy, CSS, network, persistence, or privacy behavior changes.
