# Static triage state accessibility

The private recruiter-reply decision card is server-rendered as a complete
document. Its state chip must remain ordinary static content rather than a
live region, avoiding redundant announcements on initial load. Visible
localized state, styling, routing, privacy, and dynamic feedback boundaries
remain unchanged.

Acceptance: ready, clarify, and stop state chips contain no `aria-live`;
existing deterministic, accessibility, privacy, and print tests remain green.
