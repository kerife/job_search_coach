# Extractable components

These are **candidate** DraftComponent extractions from repeated static HTML/CSS patterns. None is currently an exported JavaScript or framework component; source paths identify the static template(s) that contain the pattern. Keep generated designs aligned with the privacy-first, offline-document model.

## Layout components

## DocumentShell

- Source: `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`; `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html`; `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html`
- Category: layout
- Description: Offline document frame that supplies document metadata, restrictive CSP, an inline stylesheet placeholder, and renderer-owned header/main slots.
- Extractable props: `lang` (string), `title` (string), `headerHtml` (HTML), `mainHtml` (HTML); dossier only: `inlineScript` (HTML).
- Hardcoded: restrictive offline CSP, noindex/no-referrer metadata, inline-style delivery, and document body class.

## PrivateReceiptShell

- Source: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`; `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`
- Category: layout
- Description: Compact private receipt with skip link, single article, facts list, boundary, and local-saving footer.
- Extractable props: `title` (string), `kicker` (string), `heading` (string), `facts` (list), `boundary` (string), `footerText` (string).
- Hardcoded: semantic `main/article/dl/footer` structure, local/offline privacy framing, CSP, and CSS class names.

## Basic components

## SkipLink

- Source: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`; `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`. The dossier, practice-session, and reply-triage skip links are renderer-generated markup rather than static template source.
- Category: basic
- Description: Keyboard-visible jump link to the main artifact content.
- Extractable props: `targetId` (string, default: `main-content`), `label` (string).
- Hardcoded: visually hidden/default-offscreen treatment and focus-visible reveal.

## StatusChip

- Source: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`; `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`; `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`
- Category: basic
- Description: Bordered state/status label used for practice state, triage state, and dossier privacy/confidence signals.
- Extractable props: `state` (string), `label` (string).
- Hardcoded: forest/coral/gold visual states, uppercase/weight rules where used, and current CSS class names.

## PrivateInformationCard

- Source: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`; `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`; `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`
- Category: basic
- Description: White document card with a strong forest top or left edge for a private decision, prompt, boundary, or evidence section.
- Extractable props: `tone` (string: forest/coral/gold), `heading` (string), `bodyHtml` (HTML), `isPrintSafe` (boolean, default: true).
- Hardcoded: paper background, serif heading, border/animation treatment, and print rules.

## FactList

- Source: `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`; `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`
- Category: basic
- Description: Definition-list rows for a small, localized observation receipt.
- Extractable props: `items` (list of label/value pairs), `columnsAtWideViewport` (number, default: 2).
- Hardcoded: semantic `dl/dt/dd` markup, accent divider, and 40rem two-column breakpoint.

## ManualHandoffSequence

- Source: `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`
- Category: basic
- Description: Numbered, read-only sequence for a manual re-entry into private recruiter preparation.
- Extractable props: `steps` (list), `readinessRows` (list), `nextStep` (string), `showPreview` (boolean, default: false).
- Hardcoded: CSS counter circles, forest/coral colors, non-automated handoff framing, and privacy-safe copy structure.
