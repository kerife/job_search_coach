# ATS and truthfulness audit

Provide an ATS gap map with four distinct categories:

- `formatting`: parseability or hierarchy risks, such as image-only text or unconventional headings.
- `terminology`: supported vacancy language missing from a truthful candidate fact.
- `evidence`: a CV claim lacks a candidate fact ID, source, scope, date, or reconciliation with LinkedIn.
- `genuine skill gap`: the vacancy requires knowledge or experience the candidate does not have, such as Terraform or Argo CD when absent from the fact matrix.

Never turn a genuine skill gap into a terminology fix. Never fill a formatting issue with unsupported keywords. The workflow must not promise an ATS score from opaque ATS systems, a ranking, an interview, or a hiring outcome. State uncertainty where the vacancy parser or system is unavailable.

Each rewrite must map to a candidate fact ID or be labeled recommendation. Use the canonical labels `verified:`, `candidate-reported:`, `inferred:`, and `unknown:`; optional qualifiers after the colon clarify source or availability. Keep recommendations distinct from claims and preserve `unknown: (conflicting)` LinkedIn/CV records until confirmed.
